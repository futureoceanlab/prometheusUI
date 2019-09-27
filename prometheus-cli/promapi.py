# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import socket
import time

HOSTS = [('192.168.66.66', 50660), ('192.168.66.67', 50660)]

def apiCall(command, camnum):
    command = command + '\n'
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect(HOSTS[camnum])
        s.sendall(command.encode(), socket.MSG_NOSIGNAL)
        responselength = int.from_bytes(s.recv(4),'little')
        startrec = time.time()
        response = s.recv(responselength,socket.MSG_WAITALL)
        rectime = time.time-startrec
        return [response, rectime]


    