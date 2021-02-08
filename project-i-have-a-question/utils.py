import os, socket, json, pickle

def get_my_ip():
    #return '127.0.0.1'
    if os.name == 'posix':
        # Get the local ip using hostname (works in Ubuntu)
        import subprocess
        local_ip = subprocess.run(["hostname","-I"], stdout=subprocess.PIPE)
        local_ip = local_ip.stdout.decode().split(" ")[0] # HAMACHI
        return local_ip
    else:   # platform independent (192.168)
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        return s.getsockname()[0]


def decode_message(data):
    """ Converts given data to dict. If it cannot or data 
    is not in correct protocol, returns False
    
    Args:
        data (str): Received message from another user
    """
    try:
        mes = json.loads(data.strip())
        if validate_packet(mes):
            return mes
        assert False, "DEBUG"
        return False
    except json.decoder.JSONDecodeError:
        assert False, "DEBUG"
        return False


def validate_packet(packet):
    """ Validates the given packet
    Returns False if it is not correct.
    """
    packet_keys = set(packet.keys())
    
    is_question = (packet_keys == {"TYPE", "ACTOR", "TITLE", "CONTENT"}) and (packet["TYPE"] == "QUESTION")
    is_answer = (packet_keys == {"TYPE", "ACTOR", "QUESTION_TITLE", "CONTENT"}) and (packet["TYPE"] == "ANSWER")
    is_vote = (packet_keys == {"TYPE", "ACTOR", "QUESTION_TITLE", "VOTE"}) and (packet["TYPE"] == "VOTE")
    is_quit = (packet_keys == {"TYPE", "ACTOR"}) and (packet["TYPE"] == "QUIT")
    is_request = (packet_keys == {"TYPE", "ACTOR"}) and \
        (packet["TYPE"] == "REQUEST" or packet["TYPE"] == "REQUEST_RESPONSE" or \
         packet["TYPE"] == "REQUEST_DATA")
    #is_past_data = TODO 
    
    return is_question or is_answer or is_vote or is_quit or is_request
