// UCLA CS 111 Lab 1 main program

#include <errno.h>
#include <error.h>
#include <getopt.h>
#include <stdio.h>

#include "command.h"
/* ADDITION */
#include "command-internals.h"
#include <stdlib.h>
/* --- END ADDITION */

static char const *program_name;
static char const *script_name;

static void
usage (void)
{
  error (1, 0, "usage: %s [-pt] SCRIPT-FILE", program_name);
}

static int
get_next_byte (void *stream)
{
  return getc (stream);
}

/* ADDITION */
/* Recursively free all commands. For each command, free its input, output, and "word" when applicable. */
static void free_command(command_t cmd)
{
    free(cmd->input);
    free(cmd->output);
    char **start;
    
    switch (cmd->type)
    {
    case AND_COMMAND:
    case SEQUENCE_COMMAND:
    case OR_COMMAND:
    case PIPE_COMMAND:
        free_command(cmd->u.command[0]);
        free_command(cmd->u.command[1]);
        break;
    case SIMPLE_COMMAND:
        start = cmd->u.word;
        while (*cmd->u.word != NULL)          /* Assumes non-null word */
        {
            free(*cmd->u.word);
            cmd->u.word++;
        }
        free(start);
        break;
    case SUBSHELL_COMMAND:
        free_command(cmd->u.subshell_command);
        break;
    default:
        abort();
    }
    free(cmd);
}
/* END ADDITION */

int
main (int argc, char **argv)
{
  int opt;
  int command_number = 1;
  int print_tree = 0;
  int time_travel = 0;
  program_name = argv[0];

  for (;;)
    switch (getopt (argc, argv, "pt"))
      {
      case 'p': print_tree = 1; break;
      case 't': time_travel = 1; break;
      default: usage (); break;
      case -1: goto options_exhausted;
      }
 options_exhausted:;

  // There must be exactly one file argument.
  if (optind != argc - 1)
    usage ();

  script_name = argv[optind];
  FILE *script_stream = fopen (script_name, "r");
  if (! script_stream)
    error (1, errno, "%s: cannot open", script_name);
  command_stream_t command_stream =
    make_command_stream (get_next_byte, script_stream);

  command_t command;
  /* ADDITION */
  int status = 0;

  if (time_travel)
  {
      status = execute_time_travel(command_stream);
  }
  else
  {
      command_t last_command;
      while ((command = read_command_stream (command_stream)))
      {
          if (print_tree)
          {
              printf ("# %d\n", command_number++);
              print_command (command);
          }
          else
          {
              last_command = command;
              execute_command(command);
          }
          free_command(command);
      }
      status = print_tree || !last_command ? 0 : command_status (last_command);
  }

  free(command_stream);
  /* --- END ADDITION */
  return status;
}
