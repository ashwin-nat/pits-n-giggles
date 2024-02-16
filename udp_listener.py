import socket

class UDPListener(object):

    def __init__(self, port, bind_ip, buffer_size=1500):
        self.m_buffer_size = buffer_size
        self.m_port = port
        self.m_bind_ip = bind_ip
        self.m_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.m_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.m_socket.bind((self.m_bind_ip, self.m_port))

    def getNextMessage(self):
        message, src = self.m_socket.recvfrom(self.m_buffer_size)
        return message