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
        
        # handshake flag with peer
        self.handshake_flag = 0
        
        # keep track of upload and download speed
        self.upload_speed   = None
        self.download_speed = None
        
        # Initialize the two states of the peer
        self.am_choking         = 1
        self.am_interested      = 0
        self.peer_choking       = 1
        self.peer_interested    = 0
        

    # does an initial handshake with the peer
    def hanshake(self):
        if self.handshake_flag == 0:
            # protocol name : BTP 
            protcol_name = "BitTorrent protocol"

            # first bytes the length of protocol name default - 19
            handshake_payload  = struct.pack("!B", 19)
            # protocol name 19 bytes
            handshake_payload += struct.pack("!19s", self.protcol_name.encode())
            # next 8 bytes reserved 
            handshake_payload += struct.pack("!Q", 0)
            # next 20 bytes info hash
            handshake_payload += struct.pack("!20s", self.torrent.torrent_metadata.info_hash)
            # next 20 bytes peer id
            handshake_payload += struct.pack("!20s", self.torrent.peer_id)

            print(handshake_payload)






"""
    Implementation of Peer Wire Protocol as mentioned in RFC of BTP/1.0
    PWP will help in contacting the list of peers requesting them chucks 
    of file data. The peer class implements various algorithms like piece
    downloading stratergy, chocking and unchocking the peers, etc.
"""
class peers:
    def __init__(self, peers_data_list, torrent):
        self.peers_list = []

        for peer_IP, peer_port in peers_data_list:
            self.peers_list.append(peer(peer_IP, peer_port, torrent))






