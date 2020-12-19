### Dependencies
* Tested OS: Ubuntu 18.04, Raspbian
* Python3 
* Python dependencies can be installed using requirements.txt
    2. inputimeout (pip)

### OS
This program works on Linux. (It was tested on Ubuntu 18.04 and Raspbian)
I assumed that ```hostname -I``` will return the local IPv4 address, otherwise the program won't work.
```
> hostname -I
192.168.1.111 ...
```

### How to Run
```
cd ChatApp487
python3 main.py
```

### Tests
1. It was tested using 2 computer (Ubuntu 18.04 and Raspbian) in my home LAN. Tests were succesful. 
2. I have tested my code with **Emre Girgin** using Hamachi.
