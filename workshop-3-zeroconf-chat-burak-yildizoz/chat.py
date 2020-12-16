import socket
import threading
import json
import os
import sys
import time
from datetime import datetime
import glob
import select

################################################################################

PORT = 12345
CODING = 'utf-8'
BUFFSIZE = 1024

"""
In case of an open socket, check active ports by the following command:
netstat -ano
"""

CONTACTS=dict()

################################################################################

def send_port(IP, message, timeout=1.0):
    res = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((IP, PORT))
        s.sendall(message.encode(CODING))
        res = True
    except:
        pass
    finally:
        s.close()
    return res

def send_port_background(IP, message, timeout=1.0):
    t = threading.Thread(target=send_port, args=(IP, message, timeout),
                         daemon=True).start()

################################################################################

def send_udp_port(message):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', 0))
        s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        s.sendto(message.encode(CODING), ('255.255.255.255', PORT))
    except:
        print('udp send exception')
        pass
    finally:
        s.close()

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
                chunk = conn.recv(BUFFSIZE)
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

def listen_udp_port(username):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('', PORT))
        s.setblocking(0)
        result = select.select([s], [], [])
        data = result[0][0].recv(BUFFSIZE)
        data = data.decode(CODING)
        processMessage(username, data)
    except:
        print('listen udp exception')
        pass
    finally:
        s.close()

def listen_udp_port_continuously(username):
    while True:
        listen_udp_port(username)

def listen_udp_port_background(username):
    t = threading.Thread(target=listen_udp_port_continuously, args=(username,),
                         daemon=True).start()

################################################################################

def broadcast(username):
    # send discover messages
    myip = get_my_ip()
    message = create_json(username, myip, 'DISCOVER')
    for i in range(3):
        send_udp_port(message)
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
        add_contact(name, ip)
    elif type == 'RESPONDE':
        # discovered a contact
        name = parse_json(message, 'NAME')
        ip =  parse_json(message, 'MY_IP')
        add_contact(name, ip)
    elif type == 'MESSAGE':
        # incoming message
        name = parse_json(message, 'NAME')
        payload = parse_json(message, 'PAYLOAD')
        msg = name + ' - ' + get_date() + ' : ' + payload
        print(msg)
        with open('logs/' + username + '/' + name + '.chat', 'a') as cf:
            cf.write(msg + '\n')
        ip = parse_json(message, 'MY_IP')
        add_contact(name, ip)
    elif type == 'GOODBYE':
        name = parse_json(message, 'NAME')
        ip = parse_json(message, 'MY_IP')
        delete_contact(name, ip)
    else:
        print('Got an invalid message:', message)

################################################################################

def send_message(username, name, ip):
    chatfile = 'logs/' + username + '/' + name + '.chat'
    if os.path.isfile(chatfile):
        print('')
        with open(chatfile) as cf:
            print(cf.read())
    payload = input('Type your message to %s: ' % name)
    message = create_json(username, get_my_ip(), 'MESSAGE', payload)
    res = send_port(ip, message)
    if res:
        with open(chatfile, 'a') as cf:
            msg = username + ' - ' + get_date() + ' : ' + payload
            cf.write(msg + '\n')
    else:
        print('Unexpected offline client detected')
        delete_contact(name, ip)

################################################################################

def add_contact(name, ip):
    global CONTACTS
    c = CONTACTS.get(ip)
    if c is None:
        #print(name, 'connected from', ip)
        CONTACTS[ip] = name
    elif c == name:
        pass
    else:
        print('%s changed name to %s. IP: %s' % (c, name, ip))
        CONTACTS[ip] = name

def delete_contact(name, ip):
    global CONTACTS
    c = CONTACTS.get(ip)
    if c is None:
        pass
    elif c == name:
        print(name, 'left the chat. IP:', ip)
        CONTACTS.pop(ip)
    else:
        print('%s (known as %s) left the chat. IP: %s' % (name, c, ip))
        CONTACTS.pop(ip)

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
listen_udp_port_background(username)

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
        # list contacts
        for c in CONTACTS:
            print(CONTACTS[c])
        print('Type 0 and hit enter to return main menu')
        name = input('Who do you want to talk to: ')

        if name == '0':
            clear()

        # name found in contacts
        elif name in CONTACTS.values():
            occurrences = ()
            for ip in CONTACTS:
                if CONTACTS[ip] == name:
                    occurrences += (ip,)

            if len(occurrences) > 1:
                print('Multiple results are found for', name)
                for ip in occurrences:
                    print(ip)
                ip = input('Which IP do you want to talk to: ')
                if ip not in occurences:
                    print('Wrong Input')
                else:
                    send_message(username, name, ip)

            else:
                ip = occurrences[0]
                send_message(username, name, ip)

        else:
            print('There is no contact like that')

    elif option == '3': # Exit
        break

    else:
        print('Wrong Input')

    time.sleep(1)

#import shutil
#shutil.rmtree('logs')
