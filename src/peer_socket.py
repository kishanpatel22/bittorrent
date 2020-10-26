from socket import *
"""
    module handles the creating the socket for peers
    Note that peers are of two types peers 
    1) leechers - one who only downloads 
    2) seeders  - one who only uploads

    Note that all the current socket operations written are blocking 
    and can raise execption so inorder to test it always use try and except
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
        self.IP     = peer_IP
        self.port   = peer_port
    
    def disconnect(self):
        self.peer_sock.close() 


# class for leecher sockets
class leecher_socket(peer_socket):
   
    def __init__(self, peer_IP, peer_port, psocket = None):
        # base class contructor
        super().__init__(peer_IP, peer_port, psocket)
    
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
        peer_raw_data = b''
        recieved_data_length = 0
        request_size = data_size
        
        #loop untill you recieve all the data from the peer
        while(recieved_data_length < data_size):
            # attempt recieving request size data
            try:
                chunk = self.peer_sock.recv(request_size)
            except:
                return None
            # when recieves returns 0 means the peer has disconnected
            if len(chunk) == 0:
                self.disconnect()
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
        data_length_send = 0    
        while(data_length_send < len(raw_data)):
            data_length_send += self.peer_sock.send(raw_data[data_length_send:])




# class for seeder sockets
class seeder_socket(peer_socket):

    def __init__(self, peer_IP, peer_port, psocket = None):
        # base class constructor
        super().__init__(peer_IP, peer_port, psocket)
        # the maximum peer request that seeder can handle
        self.max_peer_requests = 50
        # the seeder must be binded at given IP and port
        self.start_seeding()
   
    """
        binds the socket that IP and port and starts listening over it
    """
    def start_seeding(self):
        self.peer_sock.bind((self.IP, self.port))
        self.peer_sock.listen(self.max_peer_requests)

    """
        accepts an incomming connection
        return connection socket and ip address of incoming connection
    """
    def accept_connection(self):
        return self.peer_sock.accept()



    

