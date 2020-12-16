function getMyIP {
    ip addr | \
      grep 'state UP' -A2 | \
      tail -n1 | \
      awk '{print $2}' | \
      cut -f1  -d'/'
}

function createJson {
    jq -n \
      --arg name "$1" \
      --arg ip "$2" \
      --arg type "$3" \
      --arg payload "$4" \
      '{NAME: $name, MY_IP: $ip, TYPE: $type, PAYLOAD: $payload}'
}

function parseJson {
    message=$1
    key=$2
    result=$(echo $message | jq ".$key" 2> /dev/null)
    # key is valid if result is inside "quotes"
    if [ "${result::1}" == \" ] && [ "${result:~0}" == \" ]
        then echo $result | sed -e 's/^"//' -e 's/"$//'
    fi
}

function addContact {
    username=$1
    name=$2
    ip=$3
    grep "$ip - $name" logs/"$username"/contacts.conn > /dev/null ||
      echo "$ip - $name" >> logs/"$username"/contacts.conn
}
