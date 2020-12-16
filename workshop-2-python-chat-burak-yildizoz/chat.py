import socket
import threading
import json
import os
import sys
import time
from datetime import datetime
import glob

################################################################################

PORT = 12345
CODING = 'utf-8'

"""
In case of an open socket, check active ports by the following command:
netstat -ano
"""

################################################################################

def send_port(IP, message, timeout=1.0):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((IP, PORT))
        s.sendall(message.encode(CODING))
    except:
        pass
    finally:
        s.close()

def send_port_background(IP, message, timeout=1.0):
    t = threading.Thread(target=send_port, args=(IP, message, timeout),
                         daemon=True).start()

################################################################################

def listen_port(username, timeout=1.0):
    HOST = get_my_ip()
    conn = None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind((HOST, PORT))
        s.settimeout(timeout)
        s.listen()
        conn, addr = s.accept()
    except:
        pass
    finally:
        s.close()
    if conn is not None:
        data = b''
        with conn:
            #print('Connected by', addr)
            while True:
                chunk = conn.recv(1024)
                if not chunk:
                    break
                data += chunk
        data = data.decode(CODING)
        processMessage(username, data)

def listen_port_continuously(username):
    while True:
        listen_port(username)

def listen_port_background(username):
    t = threading.Thread(target=listen_port_continuously, args=(username,),
                         daemon=True).start()

################################################################################

def broadcast(username):
    contacts = 'logs/' + username + '/contacts.conn'
    cooldown = 10 # seconds
    # create file if not exists
    if not os.path.isfile(contacts):
        with open(contacts, 'w') as cf:
            pass
        cooldown = 0
    # abort if under cooldown
    if time.time() - os.path.getmtime(contacts) < cooldown:
        print('Not broadcasting, cooldown is %d seconds' % cooldown)
        return
    # clear file & reset cooldown
    with open(contacts, 'w') as cf:
        pass
    # send discover messages
    myip = get_my_ip()
    domain = myip[0:myip.rfind('.')]
    print('Broadcasting on domain %s with name %s' % (domain, username))
    timeout = 1.0
    for i in range(256):
        ip = domain + '.' + str(i)
        message = create_json(username, myip, 'DISCOVER')
        send_port_background(ip, message, timeout)
    time.sleep(timeout)
    print('Broadcasting done')

################################################################################

def processMessage(username, message):
    type = parse_json(message, 'TYPE')
    if type == 'DISCOVER':
        # responde to an incoming announcement
        ip =  parse_json(message, 'MY_IP')
        send = create_json(username, get_my_ip(), 'RESPONDE')
        send_port_background(ip, send)
        name = parse_json(message, 'NAME')
        add_contact(username, name, ip)
    elif type == 'RESPONDE':
        # discovered a contact
        name = parse_json(message, 'NAME')
        ip =  parse_json(message, 'MY_IP')
        print('%s responded from %s' % (name, ip))
        add_contact(username, name, ip)
    elif type == 'MESSAGE':
        # incoming message
        name = parse_json(message, 'NAME')
        payload = parse_json(message, 'PAYLOAD')
        msg = name + ' - ' + get_date() + ' : ' + payload
        print(msg)
        with open('logs/' + username + '/' + name + '.chat', 'a') as cf:
            cf.write(msg + '\n')
    else:
        print('Got an invalid message:', message)

################################################################################

def add_contact(username, name, ip):
    contacts = 'logs/' + username + '/contacts.conn'
    save = ip + ' - ' + name
    if not find_in_file(contacts, save):
        with open(contacts, 'a') as cf:
            cf.write(save + '\n')

################################################################################

def find_in_file(file, expr):
    with open(file) as f:
        lines = f.readlines()
    for line in lines:
        if expr in line:
            return True
    return False

################################################################################

def create_json(name, ip, type, payload=''):
    return json.dumps({'NAME': name, 'MY_IP': ip,
                       'TYPE': type, 'PAYLOAD': payload},
                      ensure_ascii=False) + '\n'

def parse_json(message, key):
    try:
        msg = json.loads(message)
        return msg[key]
    except:
        return ''

################################################################################

def get_my_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    return s.getsockname()[0]

def get_date():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

################################################################################

# script directory
os.chdir(sys.path[0])

# get username and create logs directory
username = input('Your name: ')
path = 'logs/' + username + '/'
if os.path.isdir(path):
    print('Welcome back,', username)
else:
    print('Welcome', username)
os.makedirs(path, exist_ok=True)

# listen to incoming messages in background
listen_port_background(username)

# discover online users
broadcast(username)

while True:
    clear()
    print('What do you want to do?')
    print('1. Show Chat')
    print('2. Send Message')
    print('3. Exit')
    option = input()

    if option == '1': # Show Chat
        clear()
        chats = glob.glob(path + '*.chat')
        for chat in chats:
            chat = chat[chat.rfind(os.sep)+1:len(chat)]
            chat = chat.rstrip('.chat')
            print(chat)
        print('Type 0 and hit enter to return main menu')
        chat = input('Write the name of the person for the chat history: ')
        if chat == '0':
            clear()
        elif os.path.isfile(path + chat + '.chat'):
            print('')
            with open(path + chat + '.chat') as cf:
                print(cf.read())
            input('Press enter to continue')
        else:
            print('There is no chat like that')

    elif option == '2': # Send Message
        # update contacts if necessary
        broadcast(username)
        # list contacts
        with open(path + 'contacts.conn') as cf:
            print(cf.read())
        print('Type 0 and hit enter to return main menu')
        name = input('Who do you want to talk to: ')

        if name == '0':
            clear()

        # name found in contacts
        elif find_in_file(path + 'contacts.conn', name):
            occurrences = ()
            with open(path + 'contacts.conn') as cf:
                lines = cf.readlines()
            for line in lines:
                if name in line:
                    occurrences += (line,)

            if len(occurrences) > 1:
                print('Multiple results are found for', name)
                for line in occurrences:
                    line = line[line.find(' - ')+3:len(line)].rstrip()
                    print(line)

            else:
                line = occurrences[0]
                name = line[line.find(' - ')+3:len(line)].rstrip()
                if os.path.isfile(path + name + '.chat'):
                    print('')
                    with open(path + name + '.chat') as cf:
                        print(cf.read())
                ip = line[0:line.find(' - ')]
                payload = input('Type your message to %s: ' % name)
                message = create_json(username, get_my_ip(), 'MESSAGE', payload)
                send_port_background(ip, message)
                with open(path + name + '.chat', 'a') as cf:
                    msg = username + ' - ' + get_date() + ' : ' + payload
                    cf.write(msg + '\n')

        else:
            print('There is no contact like that')

    elif option == '3': # Exit
        break

    else:
        print('Wrong Input')

    time.sleep(1)
