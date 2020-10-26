from threading import *
from peer import peer
from torrent_error import *
from torrent_logger import *
import time

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
        
        # keep track of upload and download speed
        self.upload_speed   = None
        self.download_speed = None
    
        # create a peer instance for all the peers recieved 
        self.peers_list = []
        for peer_IP, peer_port in peers_data['peers']:
            peer_object = peer(peer_IP, peer_port, torrent)
            peer_object.initialize_leecher()
            self.peers_list.append(peer_object)
        
        # bitfields from all peers
        self.bitfield_pieces_count = dict()

        # peers logger object
        self.swarm_logger = torrent_logger('swarm', SWARM_LOG_FILE, DEBUG)
        
        # bitfield for pieces downloaded from peers
        self.bitfield_pieces_downloaded = {i : 0 for i in range(torrent.pieces_count)}
            
        # file handler for downloading / uploading file data
        self.file_handler = None
        
        # client peer only need incase of seeding torrent
        self.client_peer = peer(self.torrent.client_IP, self.torrent.client_port, self.torrent)
        self.client_peer.initialize_seeder()
   
    """
        performs handshakes with all the peers 
    """
    def handshakes(self):
        handshake_thread_pool = []
        for peer in self.peers_list:
            t = Thread(target = peer.handshake)
            t.start()
            handshake_thread_pool.append(t)
        
        for handshake_thread in handshake_thread_pool:
            handshake_thread.join()
        
        # used for EXCECUTION LOGGING
        for peer in self.peers_list:
            handshake_log = 'HANDSHAKE EVENT : ' + peer.unique_id + ' '
            if peer.handshake_flag:
                self.swarm_logger.log(handshake_log + SUCCESS)
            else:
                self.swarm_logger.log(handshake_log + FAILURE)

    """
        recieves the bifields from all the peers
    """
    def initialize_bitfields(self):
        reponse_thread_pool = []
        # recieved bitfields from given set of peers
        for peer in self.peers_list:
            # initialize the bitfields obtained from peers
            t = Thread(target = peer.initialize_bitfield)
            t.start()
            reponse_thread_pool.append(t)

        for reponse_thread in reponse_thread_pool:
            reponse_thread.join()
        
        # update the total bitfields recieved from all peers
        for peer in self.peers_list:
            self.update_bitfield_count(peer.bitfield_pieces)
            # used for EXCECUTION LOGGING
            init_bitfield_log  = 'INIT BITFIELD EVENT : ' + peer.unique_id + ' '
            init_bitfield_log += 'has ' + str(len(peer.bitfield_pieces)) + ' torrent pieces'
            self.swarm_logger.log(init_bitfield_log)
        
        
    """
        Updates bitfield values obtained from peers, global state of pieces is maintained
    """
    def update_bitfield_count(self, bitfield_pieces):
        for piece in bitfield_pieces:
            if piece in self.bitfield_pieces_count.keys():
                self.bitfield_pieces_count[piece] += 1
            else:
                self.bitfield_pieces_count[piece] = 1


    """
        The peer class must handle the downloaded file writing and reading 
        thus peer class must have the file handler for this purpose.
        function helps in making the share copy of handler available to peers
    """
    def add_shared_file_handler(self, file_handler):
        # instantiate the torrent shared file handler class object
        self.file_handler = file_handler
        for peer in self.peers_list:
            peer.add_file_handler(self.file_handler)

       
    """ 
        main event loop for downloading torrrent file from peers
    """
    def download_file(self):
        if self.file_handler is None:
            self.swarm_logger.log('File handler not instantiated !')
            return None
        
        for i in range(self.torrent.pieces_count):
            for peer in self.peers_list:
                if(peer.download_piece(i)):
                    download_log = peer.unique_id + ' downloaded piece ' + str(i) + ' ' + SUCCESS
                    self.swarm_logger.log(download_log)
                    break
                else:
                    download_log = peer.unique_id + ' did not downloaded piece ' + str(i)  + ' ' + FAILURE
                    self.swarm_logger.log(download_log)
   


    """
        the main event loop for uploading torrent file to the peer
    """
    def seed_file(self):
        seeding_file_forever = True
        while seeding_file_forever:
            peer_socket, peer_address = self.client_peer.recieve_connection()
            if recieved_connection != None:
                print(recieved_connection) 
                break
            else:
                time.sleep(5)
             








