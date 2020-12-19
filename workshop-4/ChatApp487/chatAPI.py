import os, time, json, copy, socket, select, threading, sys, base64

from inputimeout import inputimeout, TimeoutOccurred

from fileSender import FileSender, PacketLossError


def _decode_message(data):
    """ Converts given data to dict. If it cannot or data 
    is not in correct protocol, returns False
    
    Args:
        data (str): Received message from another user
    """
    try:
        mes = json.loads(data.strip())
        if _validate_packet(mes):
            return mes
        return False
    except json.decoder.JSONDecodeError:
        return False


def _validate_packet(packet):
    """ Validates the given packet
    Returns False if it is not correct.
    """
    if "TYPE" in packet and "NAME" in packet and "MY_IP" in packet and "PAYLOAD" in packet:
        return True
    elif "SERIAL" in packet and "RWND" in packet:
        return True
    return False


class Messenger(object):

    def __init__(self, my_ip, my_name, comm_port):
        """ Messenger object manages the sending, receiving and updating 
        messages. init() must be called after the object is created to
        start scanning for available users in the LAN. 
         
        Args:
            my_ip (str): IPv4 address of the user
            my_name (str): Username of the user
            comm_port (str): Communication port
        """
        self.my_ip = my_ip 
        self.my_name = my_name
        self.port = comm_port
        
        self.udp_server_thread = None
        self.tcp_server_thread = None

        self.db_file = ".db/.chat_db"
        self.ip2name = {}
        self.message_template = {"NAME":self.my_name, "MY_IP": self.my_ip, 
                                 "TYPE": None, "PAYLOAD": None}
        self.ip2name_lock = threading.Lock()
        self.permission_to_send = False
        self.download_request = False

        self.current_download = [None, {}, ""] # uploader ip, data, filename
        self.file_sender = None

        self.ack_buffer = []
        self.ack_buffer_lock = threading.Lock()


    def init(self):
        """ Initializes the listener and opens the database file. After, it 
        starts the scanning LAN. 
        """

        # create the db files
        with open(self.db_file, "w+") as _:
            pass

        # start listeners
        self.udp_server_thread = threading.Thread(target=self._start_udp_listener,args=())
        self.udp_server_thread.start()

        self.tcp_server_thread = threading.Thread(target=self._start_tcp_listener, args=())
        self.tcp_server_thread.start()

        print("Starting server...")
        time.sleep(2)

        # sends entrance messsage to all ips and fills the ip2name dict
        message_str = json.dumps(self._generate_message("DISCOVER"))
        for _ in range(3):
            self._send_message("UDP", "broadcast", message_str) # HAMACHI


    def enter_chat_room(self, peer_ip, peer_name):
        """ This is a UI function. It displays the chat room for the given peer
        IP.  

        Args:
            peer_ip (str): IP address of the peer.
            peer_name (str): Username of the peer.
        """
        is_peer_offline = False
        while True:
            mes_list = self._read_messages(peer_ip)
            os.system("clear")
            print("Chat Room ({} at {} and {} at {}) - Refreshed every 3 seconds\n"\
                            .format(self.my_name, self.my_ip, peer_name, peer_ip))
            
            with self.ip2name_lock:
                if not (peer_ip in self.ip2name):
                    is_peer_offline = True
                else:
                    is_peer_offline = False

            for mes in mes_list:
                print("{}: {}".format(mes["NAME"], mes["PAYLOAD"]))
            print()

            if self.download_request:
                mes = self.download_request
                self.download_request = False
                self.download_request_display(mes)
                continue

            try:
                if is_peer_offline:
                    key = inputimeout(prompt="User is offline now! They won't get your messages!\n(q) to return lobby...\n",\
                                        timeout=3)      
                else:
                    key = inputimeout(prompt='(m) to enter a message, (f) to send a file or (q) to return lobby...\n',\
                                        timeout=3)
            except TimeoutOccurred:
                continue

            if key == "q":
                break
            elif key == "m" and not is_peer_offline:
                payload = input("Enter your message\n")
                message_send = json.dumps(self._generate_message("MESSAGE", payload))
                success = self._send_message("TCP", peer_ip, message_send, filename=self.db_file)
                if not success:
                    is_peer_offline = True
            
            elif key == "f" and not is_peer_offline:
                file_path = input("Enter the relative path of the file\n").strip()
                file_path = os.path.abspath(file_path)
                if not os.path.exists(file_path):
                    print("File couldn't be found!")
                    time.sleep(2)
                    continue
                self.file_sender = FileSender(self.my_ip, self.my_name, self.port, self)
                chunks = self.file_sender.file_to_chunks(file_path)
                allow_packet = self._generate_message("ALLOW", file_path.split("/")[-1])
                self._send_message("TCP", peer_ip, json.dumps(allow_packet))
                # wait for permission
                print("Waiting for permission from the peer for the file transfer...")
                print("Press (c) to cancel...")
                while(True):
                    try:
                        if self.permission_to_send:
                            self.permission_to_send = False
                            print("Permission granted, please wait during the transfer")
                            try:
                                self.file_sender.send_file(chunks, peer_ip)
                            except PacketLossError as e:
                                print(e.message)
                                time.sleep(2)
                                break
                            print("File sent!")
                            time.sleep(2)
                            break
                        key = inputimeout(timeout=3)
                        if key == "c":
                            break
                    except TimeoutOccurred:
                        continue
                self.file_sender = None  # reset sender object
            else:
                continue
    
    def kill(self):
        """ Kills the TCP and UDP listeners and sends GOODBYE message """
        if self.tcp_server_thread:
            self._send_message("TCP", self.my_ip, "QUIT")
            self.tcp_server_thread.join()

        if self.udp_server_thread:
            message_str = json.dumps(self._generate_message("GOODBYE"))
            for _ in range(3):
                self._send_message("UDP", "broadcast", message_str)
            self.udp_server_thread.join()
    

    def download_request_display(self, mes):
        
        source_ip = mes["MY_IP"]
        source_name = mes["NAME"]
        source_payload = mes["PAYLOAD"]
        for _ in range(20):
            print()
        print("!"*50)
        res = input("{}-{} wants to send you a file named {}. If you accept "\
                    "press (y), otherwise press any other button\n".\
                format(source_name, source_ip, source_payload)+"!"*50+'\n')
        print()
        if res == "y":
            self.current_download[0] = source_ip     
            self.current_download[-1] = source_payload       
            ack_sender = threading.Thread(target=self._ack_sender, args=())
            ack_sender.start()
            yes_packet = self._generate_message("YES")
            self._send_message("TCP", source_ip, json.dumps(yes_packet))
            print("Download started. When finished, it will be saved in "\
                "the 'Downloads' folder located in the application root")
            input("Press enter to continue chatting ...")


    def _generate_message(self, m_type, payload=None):
        """ Generates a message packet in json format according to given 
        message type and the payload.

        Args:
            m_type (str): "DISCOVER", "RESPOND" or "MESSAGE"
            payload (str, optional): Message content. Should be None for 
            "RESPOND", "GOODBYE" and "DISCOVER". Defaults to None.

        Returns:
            dict: Ready-to-send packet in json format.
        """
        message = copy.deepcopy(self.message_template)
        message["TYPE"] = m_type
        if payload:
            message["PAYLOAD"] = payload
        return message


    def _update_ip2name(self, update_type, ip, name=None):
        """ Updates the user dictionary """
        if ip == self.my_ip:
            return
        if update_type == "DEL":
            with self.ip2name_lock:
                if ip in self.ip2name: del self.ip2name[ip]
        elif update_type == "ADD":
            with self.ip2name_lock:
                self.ip2name[ip] = name


    def _download_finish(self, last_chunk_id):
        downloaded_file_str = ""
        filename = self.current_download[-1]
        for i in range(last_chunk_id+1):
            downloaded_file_str += self.current_download[1][i]
        self.current_download = [None, {}, ""]
        downloaded_file = base64.b64decode(downloaded_file_str.encode("UTF-8"))
        f = open('./Downloads/'+filename, 'wb')
        f.write(downloaded_file)
        f.close()


    def _start_udp_listener(self):
        """ Listens and responds to DISCOVER and GOODBYE packets and updates ip2name """

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:            
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', self.port))
            s.setblocking(0)
            
            while True:
                
                result = select.select([s], [], [])
                data = result[0][0].recv(1500).decode("utf-8")
                
                mes = _decode_message(data)
                if not mes or mes["MY_IP"] == self.my_ip:
                    if mes["TYPE"] == "GOODBYE":
                        break
                    continue

                #print(mes)
                
                if mes["TYPE"]=="DISCOVER":
                    self._update_ip2name("ADD", mes["MY_IP"], mes["NAME"])
                    message_str = json.dumps(self._generate_message("RESPOND"))
                    self._send_message("TCP", mes["MY_IP"], message_str)

                elif mes["TYPE"]=="GOODBYE":
                    self._update_ip2name("DEL", mes["MY_IP"])

                elif mes["TYPE"]=="ACK" and not(self.file_sender is None):
                    self.file_sender.ack_confirm(mes["SERIAL"], mes["RWND"])


                elif mes["TYPE"]=="FILE":
                    #print(mes, self.current_download)
                    if self.current_download[0] == mes["MY_IP"]:
                        with self.ack_buffer_lock:
                            self.ack_buffer.append(mes)

        
        print("UDP Server killed")

                    
    def _start_tcp_listener(self):
        """ Listens MESSAGE and RESPOND packets """
        quit_listener = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.my_ip, self.port))
            s.listen()
            while True:
                conn, _ = s.accept()
                with open(self.db_file, "a") as chatdb_write:
                    with conn:
                        while True:
                            data = conn.recv(1024)
                            if not data:
                                break
                            elif data.decode("utf-8").startswith("QUIT"):
                                quit_listener = True
                                break
                            else:
                                mes = _decode_message(data.decode("utf-8"))
                                if not mes:
                                    continue

                                #print(mes)
                                if mes["TYPE"] == "RESPOND":
                                    self._update_ip2name("ADD", mes["MY_IP"], mes["NAME"])
                                
                                elif mes["TYPE"] == "MESSAGE":
                                    chatdb_write.write(data.decode("utf-8"))

                                elif mes["TYPE"]=="YES":
                                    self.permission_to_send = True

                                elif mes["TYPE"]=="ALLOW":
                                    self.download_request = mes  

                                elif mes["TYPE"]=="DOWNLOAD_FAIL":
                                    #print("FAILL")
                                    #time.sleep(100)
                                    self.current_download = [None, {}, ""]
 
                                elif mes["TYPE"]=="DOWNLOAD_SUCCESS":
                                    total = int(mes["PAYLOAD"])
                                    #print("Successs")
                                    #time.sleep(100)
                                    if True or len(self.current_download[1]) == total:
                                        t = threading.Thread(target=self._download_finish,\
                                                                        args=(total-1,))
                                        t.start()
                                    else:
                                        self.current_download = [None, {}, ""]


                        if quit_listener:
                            break
        
        print("TCP Server killed")
                        
  
    def _send_message(self, protocol, ip_address, message, filename=None):
        """ Sends message to given ip address in given protocol type """
        message += '\n'
        if protocol == "TCP":
            if filename:
                with open(filename, "a") as f:
                    f.write(ip_address+"|"+message)
            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.settimeout(2)
                    s.connect((ip_address, self.port))
                    s.settimeout(None)
                    s.sendall(str.encode(message, "utf-8"))
                except:
                    return False
            return True

        elif protocol == "UDP":
            if ip_address == "broadcast":
                ip_address = '<broadcast>'
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
                s.sendto(str.encode(message, "utf-8"), (ip_address, self.port))


    def _read_messages(self, ip_addr):
        """ Reads messages from db to display messages in a chat room.

        Args:
            ip_addr (str): IP address of the peer in the chat room.

        Returns:
            list: list of messages for the chat room.
        """
        res = []
        with open(self.db_file, "r") as file:
            lines = file.readlines()
            for line in lines:
                try:
                    mes = json.loads(line)
                except:
                    if line.split("|")[0] != ip_addr:
                        continue
                    else:
                        mes = json.loads("|".join(line.split("|")[1:]))
                        if _validate_packet(mes):
                            res.append(mes)
                if mes["TYPE"] == "MESSAGE" and mes["MY_IP"] == ip_addr:
                    if _validate_packet(mes):
                        res.append(mes)
        return res


    def _ack_sender(self):
        while(not (self.current_download[0] is None)):
            send_ack = False
            with self.ack_buffer_lock:
                if self.ack_buffer:
                    mes = self.ack_buffer.pop(0)
                    send_ack = True
            
            if send_ack:
                ack_packet = {"NAME":self.my_name, "MY_IP": self.my_ip, 
                                "TYPE": "ACK", "PAYLOAD": None,
                                "SERIAL":mes["SERIAL"], "RWND":self._calculate_rwnd()}
                self._send_message("UDP", mes["MY_IP"], json.dumps(ack_packet))
                
                if mes["SERIAL"] != -1:
                    self.current_download[1][mes["SERIAL"]] = mes["PAYLOAD"]


    def _calculate_rwnd(self):

        buffer_len = len(self.ack_buffer)*1500 # in bytes
        return 2*1024*1024-buffer_len # our buffer size is 2 mb
