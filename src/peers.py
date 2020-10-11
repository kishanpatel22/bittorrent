import struct
from network_error import network_error
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
        self.handshake_flag = 0
        
        # keep track of upload and download speed
        self.upload_speed   = None
        self.download_speed = None
        
        # Initialize the two states of the peer
        self.am_choking         = True
        self.am_interested      = False
        self.peer_choking       = True
        self.peer_interested    = False
         
        # initializing a peer socket for TCP communiction 
        self.peer_sock = socket(AF_INET, SOCK_STREAM)
        self.peer_sock.settimeout(10)
        
        # make the handshake payload for handshake
        self.handshake_payload = self.build_handshake_payload()


    # attempts to connect the peer using TCP connection 
    # returns success/failure for connection
    def connect(self):
        try:
            self.peer_sock.connect((self.IP, self.port))
            return True
        except Exception as err_msg:
            print('The error is : ', err_msg)
            return False
   

    # creates the handshake payload for peer wire protocol handshake
    def build_handshake_payload(self):
        # protocol name : BTP 
        protcol_name = "BitTorrent protocol"
        # first bytes the length of protocol name default - 19
        handshake_payload  = struct.pack("!B", 19)
        # protocol name 19 bytes
        handshake_payload += struct.pack("!19s", protcol_name.encode())
        # next 8 bytes reserved 
        handshake_payload += struct.pack("!Q", 0x0)
        # next 20 bytes info hash
        handshake_payload += struct.pack("!20s", self.torrent.torrent_metadata.info_hash)
        # next 20 bytes peer id
        handshake_payload += struct.pack("!20s", self.torrent.peer_id)
        # returns the handshake payload
        return handshake_payload
        

    # does an handshake with the peer 
    # returns success/failure for handshake
    def hanshake(self):
        # only do handshake if not done earlier
        if self.handshake_flag == 0 and self.connect():
            self.peer_sock.send(self.handshake_payload)
            try:
                # recieves the peer handshake response 
                peer_response = self.peer_sock.recv(1024)
                # compared the recieved handshake
                if(self.confirm_handshake_response(peer_response)):
                    self.handshake_flag = True
                    return True
                else:
                    return False
            except:
                return False
   

    # checks if handshake response given by peer is correct
    def confirm_handshake_response(self, peer_response):
        # check for valid peer response 
        if(len(peer_response) < 64):
            return False
        # extract the info hash of torrent 
        peer_info_hash  = peer_response[28:48]
        # extract the peer id 
        peer_id    = peer_response[48:68]

        # check if the info hash is equal 
        if(peer_info_hash != self.torrent.torrent_metadata.info_hash):
            return False
        # check if peer has got a unique id associated with it
        if(peer_id == self.torrent.peer_id):
            return False
        
        # succesfully validaded the peer information
        return True

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
        peer = self.peers_list[0]
        if(peer.hanshake()):
            print(peer.IP, peer.port, ' Did handshake succesfully!')
        else:
            print(peer.IP, peer.port, ' Did not do handshake !')

        #for peer in self.peers_list:
        #    print(peer.IP, peer.port)
        #    if(peer.hanshake()):
        #        print(peer.IP, peer.port, ' Did handshake succesfully!')
        #    else:
        #        print(peer.IP, peer.port, ' Did not do handshake !')


