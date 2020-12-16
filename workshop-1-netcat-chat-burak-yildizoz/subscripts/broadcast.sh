#!/bin/bash
set -eE

username=$1

contacts="logs/$username/contacts.conn"

if [ "$(find "$contacts" -cmin -1 2> /dev/null)" == "$contacts" ]
then
    echo "Not broadcasting, cooldown is 1 minute"
    exit
fi

source functions.sh

rm -f "$contacts"
touch "$contacts"

myip=$(getMyIP)
ip1=$(echo $myip | cut -d "." -f1)
ip2=$(echo $myip | cut -d "." -f2)
ip3=$(echo $myip | cut -d "." -f3)
domain=$ip1.$ip2.$ip3

echo "Broadcasting on domain $domain with name $username"

for i in {1..255}
do
    ip=$domain.$i
    send=$(createJson "$username" $myip DISCOVER)
    echo $send | nc -N $ip 12345 &
done

# wait for responses
sleep 0.5
