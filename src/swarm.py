from threading import *
from peer import peer
from torrent_error import *
from torrent_logger import *
from socket import *
from shared_file_handler import torrent_shared_file_handler


"""
    Implementation of Peer Wire Protocol as mentioned in RFC of BTP/1.0
    PWP will help in contacting the list of peers requesting them chucks 
    of file data. The swarm class implements various algorithms like piece
    downloading stratergy, chocking and unchocking the peers, etc.
"""

"""
    maintaing the state for all the peers participating in the torrent forming 
    a dense network oftenly called as swarm. The swarm class helps in keeping
    track of all the global information about the torrent
"""
class swarm():

    def __init__(self, peers_data, torrent):
        # initialize the peers class with peer data recieved
        self.torrent    = torrent 
        self.interval   = peers_data['interval']
        self.seeders    = peers_data['seeders']
        self.leechers   = peers_data['leechers']
            
        # create a peer instance for all the peers recieved 
        self.peers_list = []
        for peer_IP, peer_port in peers_data['peers']:
            self.peers_list.append(peer(peer_IP, peer_port, torrent))
        
        # bitfields from all peers
        self.bitfield_pieces_count = dict()

        # peers logger object
        self.swarm_logger = torrent_logger('swarm', SWARM_LOG_FILE, DEBUG)
        
        # bitfield downloaded from peers
        self.bitfield_pieces_downloaded = {i:0 for i in range(torrent.pieces_count)}
            
        # file handler for downloading / uploading file data
        self.file_handler = None


    """
        performs handshakes with all the peers 
    """
    def handshakes(self):
        
        for peer in self.peers_list:
            handshake_log = 'HANDSHAKE EVENT : ' + peer.unique_id + ' '
            if(peer.handshake()):
                handshake_log += SUCCESS
            else:
                handshake_log += FAILURE

            # used for EXCECUTION LOGGING
            self.swarm_logger.log(handshake_log)


    """
        recieves the bifields from all the peers
        Since bitfield is send immediately after handshake response, this
        function must be called after the handshaking event is done
    """
    def initialize_bitfields(self):
        # recieved bitfields from given set of peers
        for peer in self.peers_list:
            # recieve only from handshaked peers
            if(peer.handshake_flag):
                # used for EXCECUTION LOGGING
                init_bitfield_log = 'INIT BITFIELD EVENT : ' + peer.unique_id
                self.swarm_logger.log(init_bitfield_log)

                # initialize the bitfields obtained from peers
                peer.initialize_bitfield()
                # update the total bitfields recieved from all peers
                self.update_bitfield_count(peer.bitfield_pieces)
              
    
    """     
        Updates the bitfield values obtained from the peers
    """
    def update_bitfield_count(self, bitfield_pieces):
        for piece in bitfield_pieces:
            if piece in self.bitfield_pieces_count.keys():
                self.bitfield_pieces_count[piece] += 1
            else:
                self.bitfield_pieces_count[piece] = 1
        
        
    """ 
        The main event loop for the downloading the torrrent file from peers
    """
    def download_file(self):
        if self.file_handler is None:
            self.swarm_logger.log('File handler not instantiated !')
            return None
        
        for piece, peer in enumerate(self.peers_list[:1]):
            peer.download_piece(piece)
   

    """
        The peer class must handle the downloaded file writing and reading 
        thus peer class must have the file handler for this purpose
    """
    def add_file_handler(self, file_path):
        # instantiate the torrent shared file handler class object
        self.file_handler = torrent_shared_file_handler(file_path, self.torrent)
        for peer in self.peers_list:
            peer.add_file_handler(self.file_handler)



