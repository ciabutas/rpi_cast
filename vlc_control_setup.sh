#!/bin/bash

# Create a named pipe for VLC control
if [ ! -e /tmp/cmd ]; then
    mkfifo /tmp/cmd
fi

# Set up VLC to read commands from the pipe
# This should be run before starting VLC
cat /tmp/cmd | cvlc --fullscreen --control rc-host=localhost:4212