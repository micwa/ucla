// UCLA CS 111 Lab 1 command reading

#include "command.h"
#include "command-internals.h"

#include <error.h>

#include "alloc.h"
#include "vector.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <ctype.h>
#include <stdbool.h>
#include <limits.h>

#define DEFAULT_STACK_CAPAC 16
#define BUF_SIZE 1024

/* Command- and command_stream-related functions. */
static void add_command(command_stream_t stream, command_t cmd);
static struct command_node *make_node(command_t cmd, struct command_node *next);
static void free_command(command_t cmd);
static command_t make_command(int status, char *input, char *output, enum command_type type);

/* Miscellaneous functions. */
static char *make_string(const char *buf, int len);
static char *string_append(char *str, const char *to_append, int len);
static char *read_all(int (*get_next_byte)(void *), void *get_next_byte_argument);

static bool is_word_char(char c);
static bool is_operator_char(char c);
static bool is_whitespace(char c);
static char skip_whitespace(const char *buf, int *pos);
static char get_next_non_wschar(const char *buf);
static char *get_next_token(const char *buf, bool (*char_pred)(char), int *pos);
static int get_precedence(enum command_type type);

static void flatten_stack(struct vector *cmd_stack, struct vector *op_stack, int precedence);
static void push_operator(struct vector *cmd_stack, struct vector *op_stack, command_t op_cmd);
static void flatten_stack_to_stream(command_stream_t stream, struct vector *cmd_stack, struct vector *op_stack);
static void error_and_exit(int line, const char *msg);

struct command_node;

/* Complete command_stream definition. */
struct command_stream {
    /* Current node */
    struct command_node *head;
    /* Last node, solely for (easily) adding to end of stream */
    struct command_node *last;
};

/* Node that holds a command_t. */
struct command_node {
    struct command_node *next;
    command_t cmd;
};

static const char OPERATOR_CHARS[] = { '&', '|', ';' };

/* ----- Command-related static functions ----- */

/* Add the given command_t (as a root node) to the stream. */
static void add_command(command_stream_t stream, command_t cmd)
{
    struct command_node *node = make_node(cmd, NULL);
    if (stream->head == NULL)
    {
        stream->head = node;
        stream->last = node;
    }
    else
    {
        stream->last->next = node;
        stream->last = node;
    }
}

/* Malloc() a node with the given command_t and "next" pointer. */
static struct command_node* make_node(command_t cmd, struct command_node *next)
{
    struct command_node *node = checked_malloc(sizeof(struct command_node));
    node->next = next;
    node->cmd = cmd;
    return node;
}

/* Malloc() a command with the given status, input, and output.
   Command type and union types must be set separately. */
static command_t make_command(int status, char *input, char *output, enum command_type type)
{
    command_t cmd = checked_malloc(sizeof(struct command));
    cmd->type = type;
    cmd->status = status;
    cmd->input = input;
    cmd->output = output;
    
    return cmd;
}

/* ----- Miscellaneous static functions ----- */

/* Malloc() a null-terminated string of length len (+ 1 for the '\0'). */
static char *make_string(const char *buf, int len)
{
    char *str = checked_malloc((len+1) * sizeof(char));
    memcpy(str, buf, len);
    str[len] = '\0';
    
    return str;
}

/* Appends len characters from to_append to str. */
static char *string_append(char *str, const char *to_append, int len)
{
    int old_size = strlen(str);
    int new_size = old_size + 1 + len;
    str = checked_realloc(str, new_size * sizeof(char));
    memcpy(&str[old_size], to_append, len);
    str[new_size - 1] = '\0';

    return str;
}

/* Returns a malloc()'d string consisting of all the bytes obtained through get_next_byte,
   until EOF is reached.*/
static char *read_all(int (*get_next_byte)(void *), void *get_next_byte_argument)
{
    char buf[BUF_SIZE];
    char *text = NULL;
    int buf_len;
    bool do_read = true;

    /* Read all input into buf, then copy/append to text */
    while (do_read)
    {
        buf_len = 0;
        for (int i = 0; i < BUF_SIZE; ++i)
        {
            int b = get_next_byte(get_next_byte_argument);
            if (b == EOF)
            {
                do_read = false;
                break;
            }
            buf[buf_len++] = b;
        }
        if (text == NULL)
            text = make_string(&buf[0], buf_len);
        else
            text = string_append(text, &buf[0], buf_len);
    }
    return text;
}

/* Returns true if c is a valid word character, and false if not. */
static bool is_word_char(char c)
{
    if (isalnum(c))
        return true;
    switch (c)
    {
    case '!': case '+': case '-': case '/': case '@': case '_':
    case '%': case ',': case '.': case ':': case '^':
        return true;
    default:
        return false;
    }
}

/* Returns true if c is an operator characer, and false if not. */
static bool is_operator_char(char c)
{
    for (size_t i = 0; i < sizeof(OPERATOR_CHARS); ++i)
        if (c == OPERATOR_CHARS[i])
            return true;
    return false;
}

/* Returns true if c is a whitespace character, and false if not. */
static bool is_whitespace(char c)
{
    if (c == ' ' || c == '\t')
        return true;
    return false;
}

/* Sets pos to the first non-whitespace character in buf, starting from buf[pos],
   and returns that character. */
static char skip_whitespace(const char *buf, int *pos)
{
    int i = *pos;
    while (is_whitespace(buf[i]))
        ++i;
    *pos = i;
    return buf[i];
}

/* Returns the first non-whitespace character in buf. */
static char get_next_non_wschar(const char *buf)
{
    while (is_whitespace(*buf))
        ++buf;
    return *buf;
}

/* Returns the next token with characters all satisfying char_pred, starting from buf[*pos],
   or NULL if the token is an empty string. *pos will contain the first non-char_pred character. */
static char *get_next_token(const char *buf, bool (*char_pred)(char), int *pos)
{
    int start = *pos;
    int end = start;
    
    /* end will be the index of the first non-char_pred character */
    while (char_pred(buf[end]))
        ++end;
    *pos = end;
    
    if (end == start)
        return NULL;
    return make_string(&buf[start], end - start);
}

/* Returns the precedence of the following operators: ;, |, &&, ||. */
static int get_precedence(enum command_type type)
{
    if (type == SEQUENCE_COMMAND)
        return 10;
    else if (type == PIPE_COMMAND)
        return 30;
    else if (type == DUMMY_COMMAND)
        return 5;
    else        /* AND_, OR_COMMAND */
        return 20;
}

/* Helper method that pops operators off the stack until the top operator is of lesser
   precedence than "precedence", and uses those operators to combine commands from cmd_stack. */
static void flatten_stack(struct vector *cmd_stack, struct vector *op_stack, int precedence)
{
    command_t curr_op;

    while ((curr_op = vector_back(op_stack)) != NULL &&
           get_precedence(curr_op->type) >= precedence)
    {
        vector_pop(op_stack);
        command_t cmd2 = vector_pop(cmd_stack);
        command_t cmd1 = vector_pop(cmd_stack);
        
        if (cmd1 == NULL || cmd2 == NULL)   /* Too many operators? */
            error_and_exit(-1000, "TOO many operators on the stack");

        curr_op->u.command[0] = cmd1;
        curr_op->u.command[1] = cmd2;
        vector_push(cmd_stack, curr_op);
    }
}

/* Push the given operator onto the op_stack and pop all operators of greater or equal precedence 
   off using flatten_stack(). */
static void push_operator(struct vector *cmd_stack, struct vector *op_stack, command_t op_cmd)
{
    flatten_stack(cmd_stack, op_stack, get_precedence(op_cmd->type));
    vector_push(op_stack, op_cmd);
}

/* Flatten cmd_stack and add the last (remaining) command to the command_stream_t. */
static void flatten_stack_to_stream(command_stream_t stream, struct vector *cmd_stack, struct vector *op_stack)
{
    flatten_stack(cmd_stack, op_stack, -1);
    if (cmd_stack->size != 1 || op_stack->size != 0)
        error_and_exit(-1000, "PLEASE track your operators/operands (2)");

    command_t cmd = vector_pop(cmd_stack);
    add_command(stream, cmd);
}

/* Prints out the message ("%d: %s\n", line, msg) and exits. */
static void error_and_exit(int line, const char *msg)
{
    fprintf(stderr, "%d: %s\n", line, msg);
    exit(EXIT_FAILURE);
}

/* Public functions */

command_stream_t
make_command_stream (int (*get_next_byte) (void *),
		     void *get_next_byte_argument)
{
    char *buf = read_all(get_next_byte, get_next_byte_argument);
    command_stream_t stream = checked_malloc(sizeof(struct command_stream));
    stream->head = NULL;
    stream->last = NULL;

    /* Variables for parsing */
    struct vector *cmd_stack = make_vector(DEFAULT_STACK_CAPAC);
    struct vector *op_stack = make_vector(DEFAULT_STACK_CAPAC);
    int pos = 0;
    int curr_line = 1;
    int num_left_parens = 0;
    int c;

    /* For the current command */
    struct vector *curr_word = make_vector(DEFAULT_STACK_CAPAC);

    enum token_type {
        WORD,               /* Word */
        OPERATOR_REG,       /* ;, |, &&, || */
        NEWLINE,            /* Newline that signals start of new command tree */
        LEFT_PAREN,         /* ( */
        RIGHT_PAREN         /* ) */
    };
    enum token_type prev_token = NEWLINE;

    while ((c = skip_whitespace(buf, &pos)) != '\0')
    {
        if (is_word_char(c))
        {
            if (prev_token == RIGHT_PAREN)
                error_and_exit(curr_line, "Command not allowed immediately after right parenthesis");

            char *input = NULL, *output = NULL;
            while (is_word_char(c) || c == '<' || c == '>') /* Parse a simple command */
            {
                if (c == '<' || c == '>')
                {
                    ++pos;
                    skip_whitespace(buf, &pos);
                    char *word = get_next_token(buf, &is_word_char, &pos);

                    if (curr_word->size == 0)       /* bash, however, accepts "< foo" as valid syntax */
                        error_and_exit(curr_line, "No left operand for redirect");
                    if (word == NULL)
                        error_and_exit(curr_line, "No right operand for redirect");

                    if (c == '<') input = word;
                    else          output = word;
                }
                else
                {
                    char *word = get_next_token(buf, &is_word_char, &pos);
                    vector_push(curr_word, word);
                }
                c = skip_whitespace(buf, &pos);
            }

            /* Make simple command */
            command_t cmd = make_command(-1, input, output, SIMPLE_COMMAND);
            vector_push(curr_word, NULL);
            cmd->u.word = vector_to_words(curr_word);
            vector_push(cmd_stack, cmd);
            vector_clear(curr_word);
            prev_token = WORD;
        }
        else if (c == '(')
        {
            ++pos;
            ++num_left_parens;
            if (prev_token == WORD || prev_token == LEFT_PAREN || prev_token == RIGHT_PAREN)
                error_and_exit(curr_line, "Improper placement of left parenthesis");

            command_t op_cmd = make_command(-1, NULL, NULL, DUMMY_COMMAND);
            vector_push(op_stack, op_cmd);  /* Dummy operator */
            prev_token = LEFT_PAREN;
        }
        else if (c == ')')
        {
            ++pos;
            --num_left_parens;
            if (num_left_parens < 0)
                error_and_exit(curr_line, "Missing left parenthesis");
            if (prev_token != WORD && prev_token != RIGHT_PAREN)
                error_and_exit(curr_line, "Improper placement of right parenthesis");

            /* Flatten stack, create subshell command, and pop off matching ) */
            flatten_stack(cmd_stack, op_stack, get_precedence(DUMMY_COMMAND) + 1);
            command_t sub_cmd = vector_pop(cmd_stack);
            command_t new_cmd = make_command(-1, NULL, NULL, SUBSHELL_COMMAND);
            new_cmd->u.subshell_command = sub_cmd;

            vector_push(cmd_stack, new_cmd);
            command_t op_cmd = vector_pop(op_stack);
            free(op_cmd);
            prev_token = RIGHT_PAREN;

            /* Get input/output if applicable */
            for (c = skip_whitespace(buf, &pos);
                 c == '<' || c == '>';
                 c = skip_whitespace(buf, &pos))
            {
                ++pos;
                skip_whitespace(buf, &pos);
                char *word = get_next_token(buf, &is_word_char, &pos);

                if (word == NULL)
                    error_and_exit(curr_line, "No right operand for redirect (subshell)");

                if (c == '<') new_cmd->input = word;
                else          new_cmd->output = word;
            }
        }
        else if (is_operator_char(c))
        {
            if (prev_token == NEWLINE)
                error_and_exit(curr_line, "Missing left operand");
            if (prev_token == LEFT_PAREN)
                error_and_exit(curr_line, "Operator not allowed after right parenthesis");
            if (prev_token == OPERATOR_REG)
                error_and_exit(curr_line, "Two operators in a row");

            /* Add ready-made command to op_stack */
            ++pos;
            command_t op_cmd;
            if (c == ';')
            {
                char c2 = skip_whitespace(buf, &pos);
                
                /* Special cases: treat ";\n" as "\n" and ";)" as ")" */
                if (c2 == ')' ||        /* Let double newlines take care of themselves */
                    (c2 == '\n' && get_next_non_wschar(&buf[pos + 1])))
                    continue;
                else if (c2 == '\n')
                {
                    ++curr_line;
                    buf[pos] = ' ';     /* Delete the newline */
                }
                op_cmd = make_command(-1, NULL, NULL, SEQUENCE_COMMAND);
            }
            else if (c == '&' && buf[pos] == '&')
                op_cmd = make_command(-1, NULL, NULL, AND_COMMAND);
            else if (c == '|' && buf[pos] == '|')
                op_cmd = make_command(-1, NULL, NULL, OR_COMMAND);
            else if (c == '|')
                op_cmd = make_command(-1, NULL, NULL, PIPE_COMMAND);
            else
                error_and_exit(curr_line, "Invalid combination of operator characters");

            prev_token = OPERATOR_REG;
            push_operator(cmd_stack, op_stack, op_cmd);
            if (op_cmd->type == AND_COMMAND || op_cmd->type == OR_COMMAND)
                ++pos;
        }
        else if (c == '\n')
        {
            /* Check next line to determine whether to pretend to be a SEQUENCE_COMMAND or start new tree.
               If inside a subshell command, newlines are always SEQUENCE_COMMANDs. */
            ++curr_line;
            ++pos;
            if (!(prev_token == WORD || prev_token == RIGHT_PAREN))
                continue;

            if (num_left_parens == 0 && (buf[pos] == '\n' || buf[pos] == '\0')) /* Never flatten if parenthesis is unclosed */
            {
                if (vector_back(cmd_stack) != NULL)
                    flatten_stack_to_stream(stream, cmd_stack, op_stack);
                prev_token = NEWLINE;
            }                
            else        /* Pretend to be a semicolon */
                buf[--pos] = ';';
        }
        else if (c == '#')                  /* Only valid if not preceded by word character */
        {
            if (pos > 0 && is_word_char(buf[pos - 1]))
                error_and_exit(curr_line, "'#' in word");
            while ((c = buf[++pos]) != '\0' && c != '\n')
                ;       /* pos will be index of first '\n' or NULL */
        }
        else
            error_and_exit(curr_line, "Invalid character");
    }

    /* Not allowed to end with an operator */
    if (num_left_parens != 0)
        error_and_exit(curr_line, "No right parenthesis found before EOF");
    if (prev_token == OPERATOR_REG)
        error_and_exit(curr_line, "No right operand found");

    /* In case buf does not end with a newline */
    if (vector_back(cmd_stack) != NULL)
        flatten_stack_to_stream(stream, cmd_stack, op_stack);

    /* Cleanup */
    free(buf);
    free_vector(cmd_stack);
    free_vector(op_stack);
    free_vector(curr_word);

    return stream;
}

command_t
read_command_stream (command_stream_t s)
{
    if (s->head != NULL)
    {
        struct command_node *node = s->head;
        command_t cmd = node->cmd;
        s->head = node->next;
        free(node);
        return cmd;
    }
    return NULL;
}
