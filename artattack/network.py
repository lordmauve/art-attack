import time
import struct
from cPickle import loads, dumps
import socket

from threading import Thread
from Queue import Queue, Empty

from select import select


OP_CONNECT = 0  # Remote host has connected
OP_START = 1    # Client/server ready, commence game
OP_NAME = 2    # My name is

DEFAULT_PORT = 9067


class BaseConnection(Thread):
    def __init__(self):
        super(BaseConnection, self).__init__()
        self.send_queue = Queue()
        self.receive_queue = Queue()
        self.read_buf = ''

        self.daemon = True

    def send_message(self, op, payload):
        self.send_queue.put((op, payload))

    def receive_message(self):
        return self.receive_queue.get_nowait()

    def stop(self):
        self.keeprunning = False

    def _read_socket(self):
        b = self.socket.recv(4096)
        self.read_buf += b
        while len(self.read_buf) > 4:
            size = struct.unpack('!I', b[:4])[0]
            if len(self.read_buf) < size + 4:
                break
            chunk = self.read_buf[4:size + 4]
            self.read_buf = self.read_buf[size + 4:]
            self._recv_chunk(chunk)
    
    def _recv_chunk(self, chunk):
        self.receive_queue.put(loads(chunk))

    def _write_socket(self):
        try:
            payload = self.send_queue.get_nowait()
        except Empty:
            return

        buf = dumps(payload, -1)
        size = struct.pack('!I', len(buf))

        self.socket.send(size + buf)

    def establish_connection(self):
        """Subclasses should implement this method to block until a connection is successfully established
        or self.keeprunning is False
        
        """
        raise NotImplementedError("Implement this")

    def run(self):
        self.keeprunning = True
        self.establish_connection()
        # Disable Nagle algorithm
        self.socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        while self.keeprunning:
            if self.send_queue.qsize():
                wlist = [self.socket]
            else:
                wlist = []
            rlist, wlist, xlist = select([self.socket], wlist, [self.socket], 20)

            if rlist:
                self._read_socket()

            if wlist:
                self._write_socket()

            if xlist:
                pass
                


class ServerSocket(BaseConnection):
    def __init__(self, port=DEFAULT_PORT):
        super(ServerSocket, self).__init__()
        self.port = port
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind(('0.0.0.0', port))
        self.server_socket.listen(1)

    def wait_for_connection(self):
        r = self.server_socket.accept()
        if r:
            conn, address = r

            self.socket = conn
            self.remote_addr = address
            return True
        return False

    def on_connection_receive(self):
        self.receive_queue.put((OP_CONNECT, self.remote_addr))

    def establish_connection(self):
        while self.keeprunning:
            if self.wait_for_connection():
                break
            time.sleep(1)
        self.on_connection_receive()


class ClientSocket(BaseConnection):
    def __init__(self, host, port=DEFAULT_PORT):
        super(ClientSocket, self).__init__()
        self.remote_addr = ((host, port))
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def establish_connection(self):
        self.socket.connect(self.remote_addr)


if __name__ == '__main__':
    serv = ServerSocket()
    cli = ClientSocket('127.0.0.1')

    serv.send_message(2, 'Mr. Server')
    cli.send_message(2, 'Mrs. Client')

    serv.start()
    time.sleep(3)
    cli.start()

    while True:
        try:
            message = cli.receive_message()
            print "Client got", message
        except Empty:
            pass

        try:
            message = serv.receive_message()
            print "Server got", message
        except Empty:
            pass

        time.sleep(0.005)
