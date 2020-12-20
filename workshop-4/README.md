### Group Members
1. Burak Yılzdızöz
2. Alperen Bağ

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
It was tested with 2 computer (Ubuntu 18.04 and Raspbian) in a home LAN. I could succesfully transfer a txt file, a jpg file, a png file, and a pdf file whose size is approx. 4 MB.


### Knonw Issues
1. We didn't check maximum number of threads can the computer handle in the program. Practically, we didn't encountered any problem during the testing phase. However, the program might crash on a computers with a low computation capability.
