#!/bin/bash
set -eE

username=$1
message=$2

source functions.sh

type=$(parseJson "$message" TYPE)

if [ "$type" == "DISCOVER" ]
then
    # responde to an incoming announcement
    ip=$(parseJson "$message" MY_IP)
    send=$(createJson "$username" $(getMyIP) RESPONDE)
    echo $send | nc -N "$ip" 12345 &
    name=$(parseJson "$message" NAME)
    addContact "$username" "$name" "$ip"

elif [ "$type" == "RESPONDE" ]
then
    # discovered a contact
    name=$(parseJson "$message" NAME)
    ip=$(parseJson "$message" MY_IP)
    echo "$name responded from $ip"
    addContact "$username" "$name" "$ip"

elif [ "$type" == "MESSAGE" ]
then
    # incoming message
    name=$(parseJson "$message" NAME)
    payload=$(parseJson "$message" PAYLOAD)
    msg="$name - $(date +"%Y-%m-%d-%T") : $payload"
    echo $msg
    echo $msg >> logs/"$username"/"$name.chat"

else
    echo "Got an invalid message: $message"
fi
