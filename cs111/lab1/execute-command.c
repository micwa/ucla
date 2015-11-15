// UCLA CS 111 Lab 1 command execution

#include "command.h"
#include "command-internals.h"
#include "alloc.h"
#include "vector.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdbool.h>
#include <error.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>

#define FLAGS_READ O_RDONLY
#define FLAGS_WRITE O_WRONLY|O_CREAT|O_TRUNC
#define ERR(msg, ...) error(1, 0, msg, ##__VA_ARGS__)
#define DEFAULT_STACK_CAPAC 8

static int execute_tree(command_t cmd);
static int execute_simple_cmd(command_t cmd);
static int redirect(int fd, char *filename, int flags);

/* ----- Static functions ----- */

static int execute_tree(command_t cmd)
{
    int status;
    
    if (cmd->type == SIMPLE_COMMAND)
    {
        status = execute_simple_cmd(cmd);
    }
    else if (cmd->type == SEQUENCE_COMMAND) /* Always execute second command */
    {
        execute_tree(cmd->u.command[0]);
        status = execute_tree(cmd->u.command[1]);
    }
    else if (cmd->type == AND_COMMAND)
    {
        status = execute_tree(cmd->u.command[0]);
        if (status == 0)
            status = execute_tree(cmd->u.command[1]);
    }
    else if (cmd->type == OR_COMMAND)
    {
        status = execute_tree(cmd->u.command[0]);
        if (status != 0)
            status = execute_tree(cmd->u.command[1]);
    }
    else if (cmd->type == PIPE_COMMAND)
    {
        /* Set up pipe, spawn two children, and wait for them to finish */
        int fd[2];
        int p_left, p_right;
        
        if (pipe(fd) < 0)
            ERR("Failed to create pipe\n");

        /* Left child writes to fd[0], right reads from fd[1] */
        if ((p_left = fork()) == 0)
        {
            close(fd[0]);
            if (dup2(fd[1], STDOUT_FILENO) < 0)
                ERR("Failed to dup2(%d, %d) for redirect pipe\n", fd[1], STDOUT_FILENO);
            
            status = execute_tree(cmd->u.command[0]);
            close(fd[1]);
            _exit(status);
        }
        else if (p_left < 0)
        {
            ERR("Failed to fork() to execute pipe command\n");
        }
        if ((p_right = fork()) == 0)
        {
            close(fd[1]);
            if (dup2(fd[0], STDIN_FILENO) < 0)
                ERR("Failed to dup2(%d, %d) for redirect pipe\n", fd[0], STDIN_FILENO);
            
            status = execute_tree(cmd->u.command[1]);
            close(fd[0]);
            _exit(status);
        }
        else if (p_right < 0)
        {
            ERR("Failed to fork() to execute pipe command\n");
        }

        /* Parent can close pipe immediately. Return status is status of right command. */
        close(fd[0]);
        close(fd[1]);
        if (waitpid(p_left, &status, 0) < 0)
            ERR("Failed to waitpid() for left pipe child\n");
        if (waitpid(p_right, &status, 0) < 0)
            ERR("Failed to waitpid() for right pipe child\n");
        status = WEXITSTATUS(status);
    }
    else        /* SUBSHELL_COMMAND: spawn new process (with redirects) to execute command */
    {
        int p;
        int fd_in = -1, fd_out = -1;

        if ((p = fork()) == 0)
        {
            if (cmd->input != NULL)
                fd_in = redirect(STDIN_FILENO, cmd->input, FLAGS_READ);
            if (cmd->output != NULL)
                fd_out = redirect(STDOUT_FILENO, cmd->output, FLAGS_WRITE);

            status = execute_tree(cmd->u.subshell_command);
            if (fd_in >= 0)
                close(fd_in);
            if (fd_out >= 0)
                close(fd_out);
            _exit(status);
        }
        else if (p < 0)
        {
            ERR("Failed to fork() to execute subshell command\n");
        }

        if (waitpid(p, &status, 0)  < 0)
            ERR("Failed to waitpid() for child\n");
        status = WEXITSTATUS(status);
    }
    
    cmd->status = status;
    return status;
}

static int execute_simple_cmd(command_t cmd)
{
    int p;
    int status;

    /* Fork and execute cmd->word in child */
    if ((p = fork()) == 0)
    {
        if (cmd->input != NULL)
            redirect(STDIN_FILENO, cmd->input, FLAGS_READ);
        if (cmd->output != NULL)
            redirect(STDOUT_FILENO, cmd->output, FLAGS_WRITE);

        char **word = cmd->u.word;
        if (strcmp(word[0], "exec") == 0)
            execvp(word[1], &word[1]);
        else
            execvp(word[0], &word[0]);
        ERR("Failed to execvp() to execute command=%s\n", word[0]);
    }
    else if (p < 0)
    {
        ERR("Failed to fork() to execvp() command\n");
    }

    /* Parent: get exit status */
    if (waitpid(p, &status, 0)  < 0)
        ERR("Failed to waitpid() for child\n");
    return WEXITSTATUS(status);
}

/* Redirect fd to the given file, which is opened using open(filename, flags).
   Returns the file descriptor of the opened file. */
static int redirect(int fd, char *filename, int flags)
{
    int newfd;

    if ((newfd = open(filename, flags, 0644)) < 0)
        ERR("Error opening file=%s for redirect\n", filename);
    if (dup2(newfd, fd) < 0)
        ERR("Failed to dup2(%d, %d) for redirect file\n", newfd, fd);
    
    return newfd;
}

/**
 * Execution algorithm:
 *  - find all nodes w/o incoming edges
 *  - execute those nodes, and remove them
 */

/* ----- "Time travel" (parallel) portion ----- */

struct graph_node
{
    command_t cmd;
    int pid;                        /* pid of process running the cmd */
    int deps;                       /* Number of nodes it's waiting for to finish */
    struct vector *input_files;
    struct vector *output_files;
    struct vector *node_deps;       /* Nodes that depend on this node */
};

static struct graph_node *make_graph_node(command_t cmd);
static void free_graph_node(struct graph_node *node);
static void build_input_output_list(struct graph_node *node, const command_t cmd);
static void calc_dependencies(struct vector *gnodes);
static bool string_vector_intersection_null(const struct vector *v1, const struct vector *v2);

static void dispatch_graph_node(struct graph_node *node);
static void reap_and_resolve(struct vector *gnodes, const struct vector *pids);

/* Creates a graph node for the given command, including populating the
   lists of input and output files. */
static struct graph_node *make_graph_node(command_t cmd)
{
    struct graph_node *node = checked_malloc(sizeof(struct graph_node));
    node->cmd = cmd;
    node->pid = -1;     /* Not yet run */
    node->deps = 0;
    node->input_files = make_vector(DEFAULT_STACK_CAPAC);
    node->output_files = make_vector(DEFAULT_STACK_CAPAC);
    node->node_deps = make_vector(DEFAULT_STACK_CAPAC);

    return node;
}

/* Free()s the given graph_node but NOT its command. */
static void free_graph_node(struct graph_node *node)
{
    free_vector(node->input_files);
    free_vector(node->output_files);
    free_vector(node->node_deps);
    free(node);
}

/* Recursively build list of input/output files from the given command. */
static void build_input_output_list(struct graph_node *node, const command_t cmd)
{
    if (cmd == NULL)
        ERR("Graph ndoe command can not be null");
    else if (cmd->type == SIMPLE_COMMAND)
    {
        /* Add redirects, then process arguments */
        if (cmd->input != NULL)
            vector_push(node->input_files, cmd->input);
        if (cmd->output != NULL)
            vector_push(node->output_files, cmd->output);

        /* Note: consider ALL arguments of the command as input files */
        char **word = cmd->u.word;
        if (strcmp(word[0], "exec") == 0)   /* Skip "exec" */
            ++word;

        for (char **w = word + 1; *w != NULL; ++w)  /* Consider "-*" as options */
            if (w[0][0] != '-')
                vector_push(node->input_files, *w);
    }
    else if (cmd->type == SUBSHELL_COMMAND)
    {
        if (cmd->input != NULL)
            vector_push(node->input_files, cmd->input);
        if (cmd->output != NULL)
            vector_push(node->output_files, cmd->output);
        build_input_output_list(node, cmd->u.subshell_command);
    }
    else    /* All other commands have two sub-commands */
    {
        build_input_output_list(node, cmd->u.command[0]);
        build_input_output_list(node, cmd->u.command[1]);
    }
}

/* Calculates dependencies for the given vector of gnodes.
   The algorithm is as follows: vector[0] is executed first, along with all vector[i]
   that have no dependencies on vectors before them (i.e., on vector[j] for all j: 0 <= j < i).
   The executed nodes are (effectively) removed from the vector, and the process is repeated. */
static void calc_dependencies(struct vector *gnodes)
{
    for (int i = 0; i < gnodes->size; ++i)
    {
        struct graph_node *curr_node = vector_get(gnodes, i);

        /* If there are any WAR, WAW, or RAW, add dependency */
        for (int j = i + 1; j < gnodes->size; ++j)
        {
            struct graph_node *check_node = vector_get(gnodes, j);
            if (!string_vector_intersection_null(curr_node->input_files, check_node->output_files) ||
                !string_vector_intersection_null(curr_node->output_files, check_node->output_files) ||
                !string_vector_intersection_null(curr_node->output_files, check_node->input_files))
            {
                check_node->deps++;
                vector_push(curr_node->node_deps, check_node);
            }
        }
    }
}

/* Returns true if the intersection of v1 and v2 is an empty set, and false if not. */
static bool string_vector_intersection_null(const struct vector *v1, const struct vector *v2)
{
    for (int i = 0; i < v1->size; ++i)
    {
        const char *s1 = vector_get(v1, i);
        for (int j = 0; j < v2->size; ++j)
        {
            const char *s2 = vector_get(v2, j);
            if (strcmp(s1, s2) == 0)
                return false;
        }
    }
    return true;
}

/* Runs the command in the graph_node in a different process, and sets node->pid
   to the pid of the child process. */
static void dispatch_graph_node(struct graph_node *node)
{
    int p;
    if ((p = fork()) == 0)
    {
        int status = execute_tree(node->cmd);
        _exit(status);
    }
    else if (p < 0)
    {
        ERR("Failed to fork() for dispatch_graph_node()\n");
    }
    node->pid = p;
}

/* ----- Public functions ----- */

int execute_time_travel(command_stream_t stream)
{
    command_t cmd;
    struct vector *gnodes = make_vector(DEFAULT_STACK_CAPAC);
    struct vector *running_nodes = make_vector(DEFAULT_STACK_CAPAC);

    /* Create all nodes and build input/output list */
    while ((cmd = read_command_stream(stream)) != NULL)
    {
        struct graph_node *node = make_graph_node(cmd);
        build_input_output_list(node, cmd);
        vector_push(gnodes, node);
    }

    /* Calculate dependencies */
    calc_dependencies(gnodes);

    /* Run initial nodes, then continue to run gnodes with zero dependencies until there are none left */
    for (int i = 0; i < gnodes->size; ++i)
    {
        struct graph_node *node = vector_get(gnodes, i);
        if (node->deps == 0)
        {
            dispatch_graph_node(node);
            vector_push(running_nodes, node);
        }
    }
    int last_status = 0;
    while (running_nodes->size > 0)         /* Poll for finished commands in running_nodes */
    {
        for (int i = 0; i < running_nodes->size; ++i)
        {
            struct graph_node *node = vector_get(running_nodes, i);
            int pid = node->pid;
            int wait_result;

            /* Don't block for waitpid(); check the next running process immediately */
            wait_result = waitpid(pid, &last_status, WNOHANG);
            if (wait_result > 0)
            {
                struct vector *depped_by = node->node_deps;
                for (int j = 0; j < depped_by->size; ++j)
                {
                    struct graph_node *dep_node = vector_get(depped_by, j);
                    dep_node->deps--;
                    if (dep_node->deps == 0)
                    {
                        dispatch_graph_node(dep_node);
                        vector_push(running_nodes, dep_node);
                    }
                }
                vector_remove(running_nodes, i);
                --i;
                last_status = WEXITSTATUS(last_status);
            }
            else if (wait_result < 0)
                ERR("Failed to waitpid() for child\n");
        }
    }

    /* Cleanup */
    for (int i = 0; i < gnodes->size; ++i)
        free_graph_node(vector_get(gnodes, i));
    free_vector(gnodes);
    free_vector(running_nodes);

    return last_status;
}

int
command_status (command_t c)
{
  return c->status;
}

void
execute_command (command_t c)
{
  execute_tree(c);
}
