#!/bin/bash

# Compile test program
gcc -o ioctl_set ioctl_set.c

# Set ioctl
./ioctl_set 7 || exit 1
cd test

# Perform 2 + 1 + 1 + 2 + 1 = 7 writes
echo -n "hello" > a.txt   && echo "creating a.txt"
ln a.txt b.txt            && echo "hard link b.txt to a.txt"
echo -n " world" >> b.txt && echo "appending to a.txt/b.txt"
echo -n "catch" > c.txt   && echo "creating c.txt"
ln -s c.txt d.txt         && echo "symlink d.txt to c.txt"

# These writes silently fail
echo "--- Following writes should fail and produce error messages"
echo -n ", crash" >> a.txt; echo -n "!" >> b.txt
rm b.txt; ln -s a.txt b.txt
rm d.txt
echo "kc" > s.txt

# Restore ioctl
cd ..
./ioctl_set -1 || exit 1
cd test

# Check to confirm that the "failed" writes actually failed
echo "--- Confirming that writes failed"
[ "$(cat a.txt)" == "hello world" ] && \
    echo "Success: a.txt not written past 'hello world'" || \
    echo "Failed test 1"
[ -f "b.txt" ] && [ ! -h "b.txt" ] && \
    echo "Success: b.txt is a regular file (and not a symlink)" || \
    echo "Failed test 2"
[ -h "d.txt" ] && \
    echo "Success: d.txt was not removed (and is still a symlink)" || \
    echo "Failed test 3"
[ ! -f "s.txt" ] && \
    echo "Success: s.txt was not created/written to" || \
    echo "Failed test 4"

# Cleanup
rm a.txt; rm b.txt; rm c.txt; rm d.txt
cd ..
rm ioctl_set
echo "Cleaning up"
