// UCLA CS 111 Lab 1 command execution

#include "command.h"
#include "command-internals.h"

#include <stdio.h>
#include <string.h>
#include <error.h>
#include <unistd.h>
#include <fcntl.h>
#include <sys/types.h>
#include <sys/wait.h>

#define FLAGS_READ O_RDONLY
#define FLAGS_WRITE O_WRONLY|O_CREAT|O_TRUNC
#define ERR(msg, ...) error(1, 0, msg, ##__VA_ARGS__)

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
 * While (f = next file) not int output_stack, push(f)
 *
 * 1. Any single word after > < is input/output
 * 2. The first word after simple command is a read from file
 * Execution algorithm:
 *  - find all nodes w/o incoming edges
 *  - execute those nodes, and remove them
 */

/* ----- Public functions ----- */

int
command_status (command_t c)
{
  return c->status;
}

void
execute_command (command_t c, int time_travel)
{
  execute_tree(c);
}
