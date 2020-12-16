#!/bin/bash
set -eE

username=$1

while true
do
    message=$(nc -l 12345)
    ./subscripts/processMessage.sh "$username" "$message" &
done
