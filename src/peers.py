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

        # maximum peer connections
        self.max_peer_connections = 10

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
        self.bitfield = set([])

        # initializing a peer socket for TCP communiction 
        self.peer_sock = socket(AF_INET, SOCK_STREAM)
        self.peer_sock.settimeout(10)
        
        info_hash = self.torrent.torrent_metadata.info_hash
        client_peer_id = self.torrent.peer_id

        # make the handshake payload for handshake
        self.handshake_payload = handshake().message(info_hash, client_peer_id)


    # attempts to connect the peer using TCP connection 
    # returns success/failure for connection
    def connect(self):
        try:
            self.peer_sock.connect((self.IP, self.port))
            return True
        except Exception as err_msg:
            print('The error is : ', err_msg)
            return False
       

    # does an handshake with the peer 
    # returns success/failure for handshake
    def hanshake(self):
        # only do handshake if not done earlier
        if not self.handshake_flag and self.connect():
            self.peer_sock.send(self.handshake_payload)
            try:
                # recieves the peer handshake response 
                peer_response_handshake = self.peer_sock.recv(1024)
                self.handshake_flag = True
                # compared the recieved handshake
                if(self.validate_handshake_response(peer_response_handshake)):
                    return True
                else:
                    print('Invalid Handshake !')
                    return False
            except Exception as err:
                print('Error is ', err)
                return False
   

    # checks if handshake response given by peer is correct
    def validate_handshake_response(self, peer_response_handshake):
        # check for valid peer response 
        if(len(peer_response_handshake) != 68):
            return False
        
        # extract the info hash of torrent 
        peer_info_hash  = peer_response_handshake[28:48]
        # extract the peer id 
        self.peer_id    = peer_response_handshake[48:68]

        # check if the info hash is equal 
        if(peer_info_hash != self.torrent.torrent_metadata.info_hash):
            return False
        # check if peer has got a unique id associated with it
        if(self.peer_id == self.torrent.peer_id):
            return False
        # succesfully validaded the peer information
        return True
    
    
    # sends the peer given request message 
    def send_message(self, peer_request):
        if self.handshake_flag:
            self.peer_sock.send(peer_request.message())

    
    # the function attempts recieves for any messages from the peer
    # the function returns the peer wire message object if recieved
    # any message for peer successfully else returns None
    def recieve_message(self):
        # attempt to recieve any message
        try:
            peer_message = self.peer_sock.recv(1024)
        except:
            print(self.IP + " peer didn't send any message !")
            return None
        
        # extract the peer wire message information
        offset = 0
        # first 4 bytes     : message length
        message_length = struct.unpack_from("!I", peer_message)[0]
        
        offset = offset + 4
        # next 1 byte       : message ID
        message_id     = struct.unpack_from("!B", peer_message, offset)[0]
        
        offset = offset + 1
        # variable bytes    : message ID
        if(message_length > 1): 
            message_payload = peer_message[offset:]
        else:
            message_payload = None
        return peer_wire_message(message_length, message_id, message_payload)
       





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

    def handshakes(self):
        for peer in self.peers_list[:3]:
            if(peer.hanshake()):
                print(peer.IP, peer.port, ' Did handshake succesfully!')
                peer.send_message(interested())
                a = peer.recieve_message()
                print(a.message_length)
                print(a.message_id)
                print(a.payload)
                print('')
            else:
                print(peer.IP, peer.port, ' Did not do handshake !\n')







