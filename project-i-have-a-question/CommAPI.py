import os, time, json, copy, socket, select, threading, sys, base64, pickle

import utils
from database import Database


class CommunicationModule(object):

    def __init__(self, my_name, is_moderator, comm_port):
        """ CommunicationModule manages the sending and receiving
        messages.

        Args:
            my_ip (str): IPv4 address of the user
            my_name (str): Username of the user
            comm_port (str): Communication port
        """
        self.my_ip = utils.get_my_ip()
        self.my_name = my_name
        self.port = comm_port
        self.database = Database()
        self.database_lock = threading.Lock() # will be used by tcp and udp listeners
        self.is_requesting = False if is_moderator else True
        self.is_moderator = is_moderator

        self.udp_server_thread = None
        self.tcp_server_thread = None
        self.app = None

    def set_application(self, app):
        self.app = app

    def init(self):
        """ Initializes the listener """

        self.udp_server_thread = threading.Thread(target=self._start_udp_listener,args=())
        self.udp_server_thread.start()

        self.tcp_server_thread = threading.Thread(target=self._start_tcp_listener, args=())
        self.tcp_server_thread.start()

        time.sleep(2) # wait for listeners to get ready


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

        elif m_type == "REQUEST": # packet for requesting all database
            message = {"TYPE":m_type, "ACTOR":self.my_ip}

        elif m_type == "REQUEST_RESPONSE": # all available clients will send a response
            message = {"TYPE":m_type, "ACTOR":self.my_ip}

        elif m_type == "REQUEST_DATA": # packet for requesting all database from single client
            message = {"TYPE":m_type, "ACTOR":self.my_ip}

        else:
            assert False, "Message type is wrong"

        return json.dumps(message)


    def _start_udp_listener(self):

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('', self.port))
            s.setblocking(0)

            while True:
                result = select.select([s], [], [])
                data = result[0][0].recv(1500).decode("utf-8")
                mes = utils.decode_message(data)
                if not mes:
                    continue
                elif mes["TYPE"] == "QUIT" and mes["ACTOR"] == self.my_ip:
                    break

                if mes["TYPE"] == "REQUEST" and not self.is_requesting and mes["ACTOR"] != self.my_ip:
                    request_response_packet = self._generate_message("REQUEST_RESPONSE", None)
                    self._send_message("TCP", mes["ACTOR"], request_response_packet)
                else:
                    with self.database_lock:
                        self.database.update_database(mes)
                        if self.app:
                            self.app.show_frame(self.app.current_page)

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

                        try:
                            past_database = pickle.loads(data)
                            print("Past room data downloaded!")
                            self.database = copy.deepcopy(past_database)
                            if self.app:
                                self.app.show_frame(self.app.current_page)
                        except:
                            mes = utils.decode_message(data.decode("utf-8"))
                            if not mes:
                                continue
                            elif mes["TYPE"] == "QUIT" and mes["ACTOR"] == self.my_ip:
                                quit_listener = True
                                break

                            if mes["TYPE"] == "REQUEST_RESPONSE" and self.is_requesting:
                                self.is_requesting = False
                                request_data_packet = self._generate_message("REQUEST_DATA", None)
                                self._send_message("TCP", mes["ACTOR"], request_data_packet)

                            elif mes["TYPE"] == "REQUEST_DATA":
                                pickled_database = pickle.dumps(self.database)
                                self._send_message("TCP", mes["ACTOR"], pickled_database)

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
                    if isinstance(message_str, str):
                        s.sendall(str.encode(message_str, "utf-8"))
                    else:
                        s.sendall(message_str) # Send past data
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


    def add_question(self, title, content):
        payload = {"TITLE":title, "CONTENT":content}
        packet_str = self._generate_message("QUESTION", payload)
        for _ in range(3):
            self._send_message("UDP", "broadcast", packet_str)


    def add_answer(self, question_title, content):
        payload = {"QUESTION_TITLE":question_title, "CONTENT":content}
        packet_str = self._generate_message("ANSWER", payload)
        for _ in range(3):
            self._send_message("UDP", "broadcast", packet_str)


    def add_vote(self, question_title, vote):
        assert vote == "+" or vote == "-"
        payload = {"QUESTION_TITLE":question_title, "VOTE":vote}
        packet_str = self._generate_message("VOTE", payload)
        for _ in range(3):
            self._send_message("UDP", "broadcast", packet_str)


    def init_database_after_login(self):
        request_packet = self._generate_message("REQUEST", None)
        self.is_requesting = True
        self._send_message("UDP", "broadcast", request_packet)
