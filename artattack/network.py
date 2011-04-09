import time
import struct
from cPickle import loads, dumps, PicklingError, UnpicklingError
import socket

from threading import Thread
from Queue import Queue, Empty

from select import select


OP_ERR = -1 # Socket error
OP_CONNECT = 0  # Connection established
OP_START = 1    # Client/server ready, commence game
OP_NAME = 2    # My name is
OP_GAMECONFIG = 3    # Server sends painting and time limit
OP_GIVE_COLOUR = 4  # Give colour, at the start of the game
OP_POWERUP_SPAWN = 5 # Powerup spawned
OP_PALETTE_CHANGE = 6  # Palette changed (order/colours etc)
OP_TOOL_MOVE = 7 # Player tool moved
OP_PAINT = 8 # Player used a tool

DEFAULT_PORT = 9067


class BaseConnection(Thread):
    def __init__(self):
        super(BaseConnection, self).__init__()
        self.send_queue = Queue()
        self.receive_queue = Queue()
        self.read_buf = ''

        self.daemon = True

    def send_message(self, op, payload):
        buf = dumps((op, payload), -1)
        self.send_queue.put(buf)

    def receive_message(self):
        return self.receive_queue.get_nowait()

    def disconnect(self):
        self.keeprunning = False

    def _read_socket(self):
        try:
            b = self.socket.recv(4096)
        except socket.error, e:
            self.receive_queue.put((OP_ERR, e.strerror))
            self.disconnect()
            return

        self.read_buf += b
        while len(self.read_buf) > 4:
            size = struct.unpack('!I', self.read_buf[:4])[0]
            if len(self.read_buf) < size + 4:
#                print "waiting for", len(self.read_buf) - size - 4, "more bytes"
                break
            chunk = self.read_buf[4:size + 4]
            self.read_buf = self.read_buf[size + 4:]
            self._recv_chunk(chunk)
    
    def _recv_chunk(self, chunk):
        payload = loads(chunk)
        self.receive_queue.put(payload)

    def _write_socket(self):
        try:
            buf = self.send_queue.get_nowait()
        except Empty:
            return

        size = struct.pack('!I', len(buf))

#        print "Sending", len(size) + len(buf), "bytes"

        self.socket.send(size + buf)

    def establish_connection(self):
        """Subclasses should implement this method to block until a connection is successfully established
        or self.keeprunning is False
        
        """
        raise NotImplementedError("Implement this")

    def run(self):
        self.keeprunning = True
        try:
            self.establish_connection()
        except socket.error, e:
            self.receive_queue.put((OP_ERR, e.strerror))
            return

        while self.keeprunning:
            if self.send_queue.qsize():
                wlist = [self.socket]
            else:
                wlist = []
            rlist, wlist, xlist = select([self.socket], wlist, [self.socket], 0.02)

            try:
                if rlist:
                    self._read_socket()
                elif wlist:
                    self._write_socket()
                elif xlist:
                    pass
            except:
                self.receive_queue.put((OP_ERR, "Networking crashed :("))
                break

        self.socket.close()



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
        self.receive_queue.put((OP_CONNECT, self.remote_addr))


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
