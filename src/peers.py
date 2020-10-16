import time
import struct
from network_error import network_error
from peer_wire_messages import *
from socket import *

"""
    peer class instance maintains the information about the peer participating
    in the file sharing. The class provides function like handshake, request
    chunk, etc and also keeps track of upload and download speed.
"""
class peer():
    # parameterized constructor does the peer class initialization
    def __init__(self, peer_IP, peer_port, torrent):
        # peer IP, port and torrent instance
        self.IP = peer_IP
        self.port = peer_port
        self.torrent = torrent
        
        # unique peer ID recieved from peer
        self.peer_id = None

        # maximum message length
        self.max_message_length = 1024

        # handshake flag with peer
        self.handshake_flag = False
        
        # keep track of upload and download speed
        self.upload_speed   = None
        self.download_speed = None
        
        # Initialize the states of the peer 
        # Initial state of the peer is choked and not interested
        self.am_choking         = True
        self.am_interested      = False
        self.peer_choking       = True
        self.peer_interested    = False
    
        # bitfield representing which data file pieces peer has
        self.bitfield_pieces = None

        # initializing a peer socket for TCP communiction 
        self.peer_sock = socket(AF_INET, SOCK_STREAM)
        self.peer_sock.settimeout(10)
        
        info_hash = self.torrent.torrent_metadata.info_hash
        client_peer_id = self.torrent.peer_id



    # attempts to connect the peer using TCP connection 
    # returns success/failure for connection
    def connect(self):
        try:
            self.peer_sock.connect((self.IP, self.port))
            return True
        except Exception as err_msg:
            print(self.IP + ' peer connection Error : ', err_msg)
            return False

    """
        function helps in work of recieving data from peers
        function returns raw data if recieved from peer else returns None
    """
    def recieve(self, data_size):
        # attempt to recieve the message length from message
        try:
            peer_raw_data = self.peer_sock.recv(data_size)
        except:
            return None
        return peer_raw_data 
    
    """
        function helps in recieving full message given the data length
        the recieve function accumulates the data that is being recieved
    """
    def recieve_full():
        return None

    """
        function helps sends raw data to the peer connection
    """
    def send(self, raw_data):
        self.peer_sock.send(raw_data)
     

    """
        function helps in sending peer messgae given peer wire message 
        class object as an argument to the function
    """
    def send_message(self, peer_request):
        if self.handshake_flag:
            self.peer_sock.send(peer_request.message())

    """
        functions helpes in recieving peer wire protocol messages. Note that 
        function uses low level function to recieve data and creates peer
        wire message class object as return value is no had no errors
    """
    def recieve_message(self):
        # extract the peer wire message information by receiving chunks of data
        
        # recieve the message length 
        raw_message_length = self.recieve(MESSAGE_LENGTH_SIZE)
        if raw_message_length is None or raw_message_length == 0:
            return None

        # unpack the message length which is 4 bytes long
        message_length = struct.unpack_from("!I", raw_message_length)[0]
        # keep alive messages have no message ID and payload
        if message_length == 0:
            return peer_wire_message(message_length, None, None)

        # attempt to recieve the message ID from message
        raw_message_ID =  self.recieve(MESSAGE_ID_SIZE)
        if raw_message_ID is None:
            return None
       
        # unpack the message length which is 4 bytes long
        message_id  = struct.unpack_from("!B", raw_message_ID)[0]
        # messages having no payload 
        if message_length == 1:
            return peer_wire_message(message_length, message_id, None)
       
        # extract all the payload
        payload_length = message_length - 1
        
        # extract the message payload 
        message_payload = b''
        while(payload_length != 0):
            recieved_payload = self.recieve(payload_length)
            if recieved_payload is None:
                return None
            message_payload += recieved_payload
            payload_length = payload_length - len(recieved_payload)

        # return peer wire message object given the three parameters
        return peer_wire_message(message_length, message_id, message_payload)
 

    """
        functions helps in doing a handshake with peer connection
        functions returns success/failure result of handshake 
    """
    def handshake(self):
        # only do handshake if not done earlier and connection established with peer
        if not self.handshake_flag and self.connect():
            info_hash = self.torrent.torrent_metadata.info_hash
            peer_id   = self.torrent.peer_id

            # create a handshake object instance for request
            handshake_request = handshake(info_hash, peer_id)
            # send the handshake message
            self.send(handshake_request.message())
            
            # recieve message for the peer
            raw_handshake_response = self.recieve(HANDSHAKE_MESSAGE_LENGTH)
            if raw_handshake_response is None:
                return False
            # validate the raw handshake response with handshake request
            handshake_response = handshake_request.validate_handshake(raw_handshake_response)
            if handshake_response is None:
                return False

            # get the client peer id for the handshake response
            self.peer_id = handshake_response.client_peer_id
            self.handshake_flag = True
            
            # handshake success 
            return True
        # already attempted handshake with the peer
        return False
            
  
    # TODO : bitfields do get recieved need resolve the thing 
    # recieved commands since many peers send many messages in one response
    # Note : after recieving bitfields messages like unchoke or have keep on 
    # accumulating, example in given below example I am able to get the piece
    # request
    def recieve_bitfield(self):
        peer_response_message = self.recieve_message()
        print(peer_response_message)        
        
        time.sleep(5)
        peer_response_message = self.recieve_message()
        print(peer_response_message)        
        
        print('sending a request message')
        self.send_message(request(0, 0, 1024))

        time.sleep(5)
        print('recieve the peer response')
        peer_response_message = self.recieve_message()
        print(peer_response_message)        
        print(peer_response_message.payload)
        
        
        bitfield_piece = bitfield(peer_response_message.payload)
        return bitfield_piece.extract_pieces()
    
            


"""
    Implementation of Peer Wire Protocol as mentioned in RFC of BTP/1.0
    PWP will help in contacting the list of peers requesting them chucks 
    of file data. The peer class implements various algorithms like piece
    downloading stratergy, chocking and unchocking the peers, etc.
"""
class peers:

    def __init__(self, peers_data, torrent):
        # initialize the peers class with peer data recieved
        self.interval   = peers_data['interval']
        self.seeders    = peers_data['seeders']
        self.leechers   = peers_data['leechers']
        
        # create a peer instance for all the peers recieved 
        self.peers_list = []
        for peer_IP, peer_port in peers_data['peers']:
            self.peers_list.append(peer(peer_IP, peer_port, torrent))


    # perfroms the handshake with all the peers 
    def handshakes(self):
        for peer in self.peers_list[:1]:
            print('===========================================================')
            if(peer.handshake()):
                print(peer.IP, peer.port, ' did handshake succesfully !')
            else:
                print(peer.IP, peer.port, ' did not do handshake !')
            print('===========================================================\n')


    # recieves a set of bitfields from the peers 
    def recieve_bitfields(self):
        for peer in self.peers_list[:1]:
            if(peer.handshake_flag):
                print('===========================================================')
                bitfield_piece = peer.recieve_bitfield()
                if(bitfield_piece == None):
                    print(peer.IP, ' did not send bitfield !')
                else:
                    print(peer.IP, ' did send bitfields successfully !')
                print('===========================================================\n')


