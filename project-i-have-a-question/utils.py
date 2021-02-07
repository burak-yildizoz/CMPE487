import os, socket

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

