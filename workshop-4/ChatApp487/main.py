import os, subprocess, socket

from chatAPI import Messenger
from inputimeout import inputimeout, TimeoutOccurred

COMM_PORT = 12345

def display_lobby(messenger, local_ip, name):
    os.system('cls' if os.name == 'nt' else 'clear')
    print("ChatApp487\n")
    print("My IP:", local_ip)
    print("My Name:", name, '\n')
    print("CHAT ROOMS (refreshed every 3 seconds)")
    # List all users in the LAN
    with messenger.ip2name_lock:
        for i, ip_addr in enumerate(messenger.ip2name):
            print("{}- {} at {}".format(i+1, messenger.ip2name[ip_addr],\
                                        ip_addr))
    print()

def get_my_ip():
    #return '127.0.0.1'
    if os.name == 'posix':
        # Get the local ip using hostname (works in Ubuntu)
        local_ip = subprocess.run(["hostname","-I"], stdout=subprocess.PIPE)
        local_ip = local_ip.stdout.decode().split(" ")[0] # HAMACHI
        return local_ip
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]

if __name__ == "__main__":
    # We need try-except to kill the listener if something goes wrong.
    try:    
        # Create DB file
        os.makedirs(".db", exist_ok=True)
        with open(".db/.chat_db", "w+") as _:
            pass
        local_ip = get_my_ip()

        # Start UI
        os.system('cls' if os.name == 'nt' else 'clear')
        print("Welcome to ChatApp487")
        name = input("Your Name?\n")

        # Create the messenger api object
        messenger = Messenger(local_ip, name, COMM_PORT)
        messenger.init()

        while True:
            display_lobby(messenger, local_ip, name)
            if messenger.download_request:
                mes = messenger.download_request
                messenger.download_request = False
                messenger.download_request_display(mes)
                continue
            # Waits for an input in every iteration. If no input is given in 3
            # seconds, it runs the next iteration and updates the user list.
            try:
                key = inputimeout(prompt="Enter the number of the chat room "
                        "you want to enter\nEnter (q) to exit\n", timeout=3)
            except TimeoutOccurred:
                continue
           
            if key == 'q':  
                # Exit
                raise Exception("Good bye")
            else:  
                # Enter a chat room
                try:
                    chat_idx = int(key) - 1
                    with messenger.ip2name_lock:
                        peer_ip = list(messenger.ip2name.keys())[chat_idx]
                        peer_name = messenger.ip2name[peer_ip]
                except (ValueError, IndexError):
                    continue

                messenger.enter_chat_room(peer_ip, peer_name)

    except Exception as e:
        # Kill the listener before exiting
        messenger.kill()
        print(e)
