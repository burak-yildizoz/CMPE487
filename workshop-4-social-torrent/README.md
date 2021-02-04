# Social Torrent

A Python App to send files and messages to other available users in LAN.

### Group Members
1. Alperen Bağ
2. Burak Yıldızöz

### Dependencies
* Tested OS: Ubuntu 18.04, Raspbian, Windows 10
* Python3
* Python dependencies can be installed using requirements.txt
    1. inputimeout (pip)

### OS
This program works on both Linux and Windows. (It was tested on Ubuntu 18.04, Raspbian and Windows 10)

In Linux, ```hostname -I``` will return the IP address of Hamachi, if available. But the IP should be written in the code for Hamachi in Windows.
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
- It was tested with 2 computer (Ubuntu 18.04 and Raspbian) in a home LAN. We could succesfully transfer a txt file, a jpg file, a png file, and a pdf file whose size is approx. 4 MB.

- Another test performed over Hamachi between Raspbian and Windows 10. Text and image files are sent successfully.

- Finally, sending messages and files succeeded between two computers with Windows 10.

### Known Issues
1. We didn't check maximum number of threads can the computer handle in the program. Practically, we didn't encountered any problem during the testing phase. However, the program might crash on a computer with low computational capability.
2. Since the screen is cleared every 3 seconds, it is possible that it can be cleared after you type your input and before pressing ENTER. Just try again in that case :)
