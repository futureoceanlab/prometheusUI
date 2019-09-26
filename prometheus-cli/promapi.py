# -*- coding: utf-8 -*-
#!/usr/bin/env python3

import socket

HOSTS = [('192.168.66.66', 50660), ('192.168.66.67', 50660)]

class apiHandler:

    def __init__( ):
        self.commandhistory = []

    def apiCall(self, command, camnum):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect(HOSTS[camnum])
            s.sendall(command, socket.MSG_NOSIGNAL)
            responselength = s.recv(4)
            response = s.recv(responselength)
            return response


    