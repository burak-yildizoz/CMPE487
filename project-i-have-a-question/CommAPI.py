import os, time, json, copy, socket, select, threading, sys, base64

from utils import get_my_ip
from database import Database

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
        assert False, "DEBUG"
        return False
    except json.decoder.JSONDecodeError:
        assert False, "DEBUG"
        return False


def _validate_packet(packet):
    """ Validates the given packet
    Returns False if it is not correct.
    """
    packet_keys = set(packet.keys())
    
    is_question = (packet_keys == {"TYPE", "ACTOR", "TITLE", "CONTENT"}) and (packet["TYPE"] == "QUESTION")
    is_answer = (packet_keys == {"TYPE", "ACTOR", "QUESTION_TITLE", "CONTENT"}) and (packet["TYPE"] == "ANSWER")
    is_vote = (packet_keys == {"TYPE", "ACTOR", "QUESTION_TITLE", "VOTE"}) and (packet["TYPE"] == "VOTE")
    is_quit = (packet_keys == {"TYPE", "ACTOR"}) and (packet["TYPE"] == "QUIT")
    return is_question or is_answer or is_vote or is_quit


class CommunicationModule(object):

    def __init__(self, my_name, comm_port):
        """ CommunicationModule manages the sending and receiving 
        messages. 
         
        Args:
            my_ip (str): IPv4 address of the user
            my_name (str): Username of the user
            comm_port (str): Communication port
        """
        self.my_ip = get_my_ip()
        self.my_name = my_name
        self.port = comm_port
        self.database = Database()
        self.database_lock = threading.Lock() # will be used by tcp and udp listeners 
        
        self.udp_server_thread = None
        self.tcp_server_thread = None


    def init(self):
        """ Initializes the listener """

        self.udp_server_thread = threading.Thread(target=self._start_udp_listener,args=())
        self.udp_server_thread.start()

        self.tcp_server_thread = threading.Thread(target=self._start_tcp_listener, args=())
        self.tcp_server_thread.start()

        time.sleep(2)
        # TODO Send the hello packet and get all questions from peers
        # init_database()

    
    def kill(self):
        """ Kills the TCP and UDP listeners """
        quit_message_str = self._generate_message("QUIT", None)
        
        if self.tcp_server_thread:
            self._send_message("TCP", self.my_ip, quit_message_str)
            self.tcp_server_thread.join()

        if self.udp_server_thread:
            for _ in range(3):
                self._send_message("UDP", self.my_ip, quit_message_str)
            self.udp_server_thread.join()


    def _generate_message(self, m_type, payload):
        """ Generates a message packet as string in json format according to given 
        message type and the payload.

        Args:
            m_type (str): "QUESTION", "ANSWER" or "VOTE"
            payload (str, optional): Message content. 

        Returns:
            str: Ready-to-send packet in json format.
        """
        if m_type == "QUESTION":
            message = {"TYPE":m_type, "ACTOR":self.my_ip,\
                       "TITLE":payload["TITLE"], "CONTENT":payload["CONTENT"]}
        
        elif m_type == "ANSWER":
            message = {"TYPE":m_type, "ACTOR":self.my_ip,\
                       "QUESTION_TITLE":payload["QUESTION_TITLE"], \
                       "CONTENT":payload["CONTENT"]}
        
        elif m_type == "VOTE":
            message = {"TYPE":m_type, "ACTOR":self.my_ip,\
                       "QUESTION_TITLE":payload["QUESTION_TITLE"], "VOTE":payload["VOTE"]}
        
        elif m_type == "QUIT":
            message = {"TYPE":m_type, "ACTOR":self.my_ip}
        
        else:
            assert False, "Message type should be QUESTION, ANSWER or VOTE"

        return json.dumps(message)


    def _start_udp_listener(self):

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:            
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', self.port))
            s.setblocking(0)
            
            while True:
                result = select.select([s], [], [])
                data = result[0][0].recv(1500).decode("utf-8")
                mes = _decode_message(data)
                if not mes:
                    continue
                elif mes["TYPE"] == "QUIT" and mes["ACTOR"] == self.my_ip:
                    break
                
                with self.database_lock:
                    self.database.update_database(mes)
                
        print("UDP Server killed")

                    
    def _start_tcp_listener(self):
        quit_listener = False
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.my_ip, self.port))
            s.listen()
            while True:
                conn, _ = s.accept()
                with conn:
                    while True:
                        data = conn.recv(1500)
                        if not data:
                            break
                        
                        mes = _decode_message(data.decode("utf-8"))
                        if not mes:
                            continue    
                        elif mes["TYPE"] == "QUIT" and mes["ACTOR"] == self.my_ip:
                            quit_listener = True
                            break
                    
                        with self.database_lock:
                            self.database.update_database(mes)

                    if quit_listener:
                        break
        
        print("TCP Server killed")
                        
  
    def _send_message(self, protocol, ip_address, message_str):
        """ Sends message to given ip address in given protocol type """

        if protocol == "TCP":            
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.settimeout(2)
                    s.connect((ip_address, self.port))
                    s.settimeout(None)
                    s.sendall(str.encode(message_str, "utf-8"))
                except:
                    return False
            return True

        elif protocol == "UDP":
            if ip_address == "broadcast":
                domain = self.my_ip[0:self.my_ip.find('.')]
                if domain == '192':
                    ip_address = '<broadcast>'
                else:
                    ip_address = domain + '.255.255.255'
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
                s.sendto(str.encode(message_str, "utf-8"), (ip_address, self.port))

