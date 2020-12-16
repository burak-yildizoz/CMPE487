#!/bin/bash

# e makes the script exit at error, E lets the error trap we define below propagate through functions, subshells etc.
set -eE

# kill all processes before exitting
trap "exit" INT TERM
trap "kill 0" EXIT

# requirements
which jq > /dev/null || sudo apt-get install jq

# script directory
cd "$(dirname "$0")"

IFS= read -r -p "Your name: " username

if [ -d logs/"$username" ]
    then echo "Welcome back $username"
else
    echo "Welcome $username"
    mkdir -p logs/"$username"
fi

source functions.sh

# listen to incoming messages in background
./subscripts/listener.sh "$username" &

# discover online users
./subscripts/broadcast.sh "$username"

while true
do
    clear
    echo "What do you want to do?"
    echo "1. Show Chat"
    echo "2. Send Message"
    echo "3. Exit"
    read option

    if [ "$option" == 1 ] # Show Chat
    then
        clear
        ls logs/"$username" | grep .chat | sed 's/.chat//g'
        echo "Type 0 and hit enter to return main menu"
        IFS= read -r -p "Write the name of the person for the chat history: " chatname

        if [ "$chatname" == 0 ]
            then clear
        elif [ -f logs/"$username"/"$chatname.chat" ]
        then
            echo ""
            cat logs/"$username"/"$chatname.chat"
            read -p "Press enter to continue"
        else
            echo "There is no chat like that"
        fi

    elif [ "$option" == 2 ] # Send Message
    then
        # update contacts if necessary
        ./subscripts/broadcast.sh "$username"
        # list contacts
        cat logs/"$username"/contacts.conn
        echo "Type 0 and hit enter to return main menu"
        IFS= read -r -p "Who do you want to talk to: " name

        if [ "$name" == 0 ]
            then clear

        # name found in contacts
        elif grep -q "$name" logs/"$username"/contacts.conn
        then
            foundname=$(grep "$name" logs/"$username"/contacts.conn | \
                cut -d "-" -f2 | cut -c 2-) # strip the space at the beginning

            if [ $(echo "$foundname" | wc -l) -gt 1 ]
            then
                echo "Multiple results are found for $name"
                echo "$foundname"

            else
                name="$foundname"
                cat logs/"$username"/"$name.chat" 2> /dev/null || true
                ip=$(grep "$name" logs/"$username"/contacts.conn | \
                  cut -d "-" -f1 | rev | cut -c 2- | rev) # strip the space at the end
                IFS= read -r -p "Type your message to $name: " payload
                # create json package
                send=$(createJson "$username" $(getMyIP) MESSAGE "$payload")
                # send over netcat at background
                echo $send | nc -N "$ip" 12345 &
                # write to chat history
                echo "$username - $(date +"%Y-%m-%d-%T") : $payload" >> logs/"$username"/"$name.chat"
            fi

        else
            echo "There is no contact like that"
        fi

    elif [ "$option" == 3 ] # Exit
        then exit

    else
        echo "Wrong Input"
    fi

    sleep 1
done
