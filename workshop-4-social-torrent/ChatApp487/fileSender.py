import threading, time, copy, json, math, base64, sys

class PacketLossError(Exception):
    def __init__(self, serial):
        self.message = "Packet Loss with Serial No: {}".format(serial)
        super().__init__("Packet Loss with Serial No: {}".format(serial))


class FileSender(object):
    def __init__(self, my_ip, my_name, comm_port, chat_api):
        self.my_ip = my_ip
        self.my_name = my_name
        self.comm_port = comm_port

        self.resend_packets = [] # serial no of packets to be resent
        self.received_acks = {} # key: serial no, value: remaining rwnd
        self.suspend = False

        self.chat_api = chat_api  # we need chat api to send packets
        
        self.message_template = {"NAME":self.my_name, "MY_IP": self.my_ip, "TYPE": "FILE",
                                 "PAYLOAD": "", "SERIAL":None}
    
        self.received_acks_lock = threading.Lock()
        self.resend_packets_lock = threading.Lock()

    
    def _wait(self, sec):
        """ Busy wait for given seconds """
        t1 = time.time()
        t2 = time.time()
        while(t2-t1<sec):
            t2 = time.time()


    def ack_confirm(self, serial, rwnd):
        with self.received_acks_lock:
            self.received_acks[serial] = int(rwnd)


    def _check_ack(self, chunk):
        serial_no = chunk["SERIAL"]
        ack_success = False
        t1 = time.time()
        while(True): # for 1 second
            with self.received_acks_lock:
                if serial_no in self.received_acks:
                    ack_success = True
                    remaining_rwnd = self.received_acks[serial_no]
                    if remaining_rwnd < 1024*1024:
                        self.suspend = True
                    return
            if time.time() - t1 > 1:
                break

        if not ack_success:
            with self.resend_packets_lock:
                self.resend_packets.append(chunk)


    def _send_packet(self, packet, target_ip):
        """ Sends given packet to target ip 
        Args:
            packet (str): JSON-like string to be sent (packet is in file type)
        """
        self.chat_api._send_message("UDP", target_ip, packet)


    def _generate_message(self, serial, payload=None):
        """ Generates a message packet in json format according to given 
        message type and the payload.

        Args:
            serial (int): Serial No for packet
            payload (str, optional): Message content.

        Returns:
            dict: Ready-to-send JSON-like packet in str format.
        """
        message = copy.deepcopy(self.message_template)
        message["SERIAL"] = serial
        if payload:
            message["PAYLOAD"] = payload
        return json.dumps(message)
    

    def _dowload_finish(self, target_ip, success, chunk_num):
            if success:
                finish_mes = self.chat_api._generate_message("DOWNLOAD_SUCCESS", \
                                                        payload=chunk_num)
            else:
                finish_mes = self.chat_api._generate_message("DOWNLOAD_FAIL")
            self.chat_api._send_message("TCP", target_ip, json.dumps(finish_mes))

    def file_to_chunks(self, path):
        packet_wo_payload = self._generate_message(2147483647) # max serial no
        packet_size_wo_payload = len(packet_wo_payload.encode("UTF-8"))
        payload_space = 1500 - packet_size_wo_payload # in bytes
        
        with open(path, "rb") as file:
            base64_encoded = base64.b64encode(file.read())
        filesize = len(base64_encoded)
        chunk_num = math.ceil(float(filesize)/payload_space)
        base64_encoded_str = base64_encoded.decode("utf-8")
        
        chunks = []
        
        for i in range(chunk_num):
            chunk_start = i*payload_space
            chunk_end = min((i+1)*payload_space, len(base64_encoded_str))
            chunk = {"NAME":self.my_name, "MY_IP": self.my_ip, "TYPE": "FILE",
                     "PAYLOAD": base64_encoded_str[chunk_start:chunk_end], "SERIAL":i}
            chunks.append(chunk)
        return chunks


    def send_file(self, chunks, target_ip):
        """ Starts sending process of a file given in list of chunks
        Args: 
            chunks (list): List of chunks that constitute the file to be sent 
                Each chunk is a dict and must contain following fields.
                NAME, MY_IP, TYPE(=FILE), PAYLOAD, SERIAL
        """
        total = len(chunks)
        received_acks_num = 0
        while(received_acks_num != total):
            #print(len(chunks))
            received_acks_num = len(self.received_acks) if -1 not in self.received_acks else \
                                                            len(self.received_acks) -1
            if self.suspend:
                print("Uploading suspended for 1 minute, because of the low buffer space of the receiver")
                self._wait(60)
                for _ in range(3):
                    empty_packet = self._generate_message(-1)
                    self._send_packet(empty_packet, target_ip)
                
                    empty_packet_sent_success = False
                    t1 = time.time()
                    while(True): # for 1 second
                        with self.received_acks_lock:
                            if -1 in self.received_acks: # check if empty ack received
                                empty_packet_sent_success = True
                                remaining_rwnd = self.received_acks[-1]
                                del self.received_acks[-1]
                                if remaining_rwnd > 1024*1024:
                                    self.suspend = False
                                break
                        if time.time() - t1 > 1:
                            break
                    if empty_packet_sent_success:
                        break

                if not empty_packet_sent_success:
                    self._dowload_finish(target_ip, 0, total)
                    raise PacketLossError("-1 (empty packet)")
                    
                time.sleep(2) # just to make sure that we got all empty acks
                if -1 in self.received_acks:
                    del self.received_acks[-1]
                continue

            if chunks:
                chunk = chunks.pop(0)
                self._send_packet(json.dumps(chunk), target_ip)
                ## start checking ack (non-blocking)
                checking_ack_thread = threading.Thread(target=self._check_ack, \
                                                        args=(chunk,))
                checking_ack_thread.start()
            
            ## resend packets that might lost
            with self.resend_packets_lock:
                while(self.resend_packets):
                    chunk = self.resend_packets.pop(0)
                    # resend
                    for _ in range(3):
                        self._send_packet(json.dumps(chunk), target_ip)
                        # wait for ack for 1 sec (blocking)
                        resend_success = False
                        t1 = time.time()
                        while(True):
                            with self.received_acks_lock:
                                if chunk["SERIAL"] in self.received_acks:
                                    resend_success = True
                                    remaining_rwnd = self.received_acks[chunk["SERIAL"]]
                                    if remaining_rwnd < 1024*1024:
                                        self.suspend = True
                                    break
                            if time.time() - t1 > 1:
                                break
                        if resend_success:
                            break
                    if not resend_success:
                        #print(chunk)
                        #time.sleep(100)
                        self._dowload_finish(target_ip, 0, total)
                        raise PacketLossError(chunk["SERIAL"])

        print()
        self._dowload_finish(target_ip, 1, total)



            



                













