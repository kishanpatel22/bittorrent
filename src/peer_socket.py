from socket import *
from select import *
from threading import *
from torrent_error import *
from torrent_logger import *
import sys

"""
    module handles the creating the socket for peers, and operations that
    peer socket can peform

    Note that all the current socket operations written are blocking 
"""

# class for general peer socket 
class peer_socket():

    def __init__(self, peer_IP, peer_port, psocket = None):
        if psocket is None:
            # initializing a peer socket for TCP communiction 
            self.peer_sock = socket(AF_INET, SOCK_STREAM)
        else:
            # initializing using the constructor argument socket
            self.peer_sock = psocket
        
        self.peer_sock.settimeout(5)
        
        # IP and port of the peer
        self.IP         = peer_IP
        self.port       = peer_port
        self.unique_id  = self.IP + ' ' + str(self.port)

        # the maximum peer request that seeder can handle
        self.max_peer_requests = 50
        
        # variable for peer connection
        self.peer_connection = True

        # socket locks for synchronization 
        self.socket_lock = Lock()
        
        # logger for peer socket
        self.socket_logger = torrent_logger(self.unique_id, SOCKET_LOG_FILE, DEBUG)
        

    """
        attempts to connect the peer using TCP connection 
    """
    def request_connection(self):
        self.peer_sock.connect((self.IP, self.port))

    """
        function returns raw data of given data size which is recieved 
        function returns the exact length data as recieved else return None
    """
    def recieve_data(self, data_size):
        if not self.peer_connection:
            return 
        peer_raw_data = b''
        recieved_data_length = 0
        request_size = data_size
        
        #loop untill you recieve all the data from the peer
        while(recieved_data_length < data_size):
            # attempt recieving request data size in chunks
            self.socket_lock.acquire()
            try:
                chunk = self.peer_sock.recv(request_size)
            except:
                chunk = b''
            finally:
                self.socket_lock.release()
            # when recieved length 0 means simply return 
            if len(chunk) == 0:
                return None
            peer_raw_data += chunk
            request_size -=  len(chunk)
            recieved_data_length += len(chunk)

        # return required size data recieved from peer
        return peer_raw_data 
   
    """
        function helps send raw data by the socket
        function sends the complete message.
    """
    def send_data(self, raw_data):
        if not self.peer_connection:
            return 
        data_length_send = 0
        while(data_length_send < len(raw_data)):
            with self.socket_lock:
                data_length_send += self.peer_sock.send(raw_data[data_length_send:])

    """
        binds the socket that IP and port and starts listening over it
    """
    def start_seeding(self):
        try:
            self.peer_sock.bind((self.IP, self.port))
            self.peer_sock.listen(self.max_peer_requests)
        except Exception as err:
            binding_log = 'Seeding socket binding failed ! ' + self.unique_id + ' : '
            self.socket_logger.log(binding_log + err.__str__())
            sys.exit(0)

    """
        accepts an incomming connection
        return connection socket and ip address of incoming connection
    """
    def accept_connection(self):
        try:
            connection = self.peer_sock.accept()
        except Exception as err:
            connection_log = 'Socket connection error for ' + self.unique_id + ' : ' 
            torrent_error(connection_log + err.__str__()) 
        # successfully return connection
        return connection

    """
        disconnects the socket
    """
    def disconnect(self):
        self.peer_sock.close() 
        self.peer_connection = False
       
    """
        context manager for exit
    """
    def __exit__(self):
        self.disconnect()
