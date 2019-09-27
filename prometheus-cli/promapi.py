# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import socket

HOSTS = [('192.168.66.66', 50660), ('192.168.66.67', 50660)]

class apiHandler:

    def __init__(self):
        self.commandhistory = []

    def apiCall(self, command, camnum):
        command = command + '\n'
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(HOSTS[camnum])
            s.sendall(command.encode(), socket.MSG_NOSIGNAL)
            responselength = int.from_bytes(s.recv(4),'little')
            response = s.recv(responselength)
            return response


    