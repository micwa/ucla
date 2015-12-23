#include "ospfs_ioctl.h"

#include <sys/types.h> 
#include <sys/stat.h> 
#include <fcntl.h>

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>

int main(int argc, const char* argv[])
{
    const char *FILE = "./test/abcd.txt";
    int nwrites_to_crash;
    int fd;

    /* Check command-line argument */
    if (argc != 2 || (nwrites_to_crash = atoi(argv[1])) < -1)
    {
        fprintf(stderr, "Must provide one integer argument, i >= -1\n");
        exit(EXIT_FAILURE);
    }

    /* open(), ioctl(), and close() */
    if ((fd = open(FILE, O_RDONLY|O_CREAT)) == -1)
    {
        fprintf(stderr, "open() failed\n");
        exit(EXIT_FAILURE);
    }
    if (ioctl(fd, OSPFS_SET_NWRITES_TO_CRASH, nwrites_to_crash) == -1)
    {
        fprintf(stderr, "ioctl() failed: %d\n", errno);
        exit(EXIT_FAILURE);
    }
    if (close(fd) == -1)
    {
        fprintf(stderr, "close() failed\n");
        exit(EXIT_FAILURE);
    }
    return 0;
}
