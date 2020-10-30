from threading import *
from peer import peer
from torrent_error import *
from torrent_logger import *
import time
import random

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
            self.peers_list.append(peer(peer_IP, peer_port, torrent))
        
        # bitfields from all peers
        self.bitfield_pieces_count = dict()

        # peers logger object
        self.swarm_logger = torrent_logger('swarm', SWARM_LOG_FILE, DEBUG)
        
        # bitfield for pieces downloaded from peers
        self.bitfield_pieces_downloaded = set([])
            
        # file handler for downloading / uploading file data
        self.file_handler = None
        
        # check if the torrent file is for seeding
        if torrent.client_state['seeding'] != None:
            # client peer only need incase of seeding torrent
            self.client_peer = peer(self.torrent.client_IP, self.torrent.client_port, self.torrent)
            self.client_peer.initialize_seeding()
        
        # swarm lock for required for updating the global state
        self.swarm_lock = Lock()
        

    """
        performs handshakes with all the peers 
    """
    def handshakes(self):
        handshake_thread_pool = []
        for peer in self.peers_list:
            t = Thread(target = peer.initiate_handshake)
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
        initializes the particular peer bitfield state and also 
        updates the swarm bitfield count state accordingly 
    """
    def initialize_peer_bitfield(self, peer_index):
        # recieve the peer bitfields 
        peer_bitfield_pieces = self.peers_list[peer_index].initialize_bitfield()
        
        # lock while updating the global state of swarm
        self.swarm_lock.acquire()
        # update the bitfield count
        self.update_bitfield_count(peer_bitfield_pieces) 
        self.swarm_lock.release()
         
        # used for EXCECUTION LOGGING
        peer = self.peers_list[peer_index]
        init_bitfield_log  = 'INITIALIZE BITFIELD EVENT : ' + peer.unique_id 
        init_bitfield_log += ' has ' + str(len(peer.bitfield_pieces)) + ' file pieces'
        self.swarm_logger.log(init_bitfield_log)
        
               
    """
        Updates bitfield values obtained from peers
        global state of count of pieces available in the swarm
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
        function checks if the download is completed or not
    """
    def download_complete(self):
        return len(self.bitfield_pieces_downloaded) == self.torrent.pieces_count

       
    """ 
        function helps in downloading torrrent file from peers
        implementation of rarest first algorithm as downloading stratergy
    """
    def download_file(self):
        if self.file_handler is None:
            self.swarm_logger.log('File handler not instantiated !')
            return 
        
        # initialize bitfields asynchronously
        for peer_index in range(len(self.peers_list)):
            bitfield_thread = Thread(target = self.initialize_peer_bitfield, args=(peer_index, ))
            bitfield_thread.start()
            bitfield_thread.join()

        # simultaneouly start downloading the file from peers
        # download_thread = Thread(target = self.download_using_stratergies)
        # download_thread.start()
        self.download_using_stratergies()
        

    """
        downloads the file from peers in swarm using some stratergies of peice
        selection and peer selection respectively
    """
    def download_using_stratergies(self):
        while not self.download_complete():
            piece       = self.piece_selection_startergy()
            if piece is not None:
                peer_index  = self.peer_selection_startergy(piece)
                is_piece_downloaded = self.peers_list[peer_index].download_piece(piece)
                download_log  = 'download of piece ' + str(piece) + ' from peer ' 
                download_log += self.peers_list[peer_index].unique_id + ''
                if is_piece_downloaded:
                    self.bitfield_pieces_downloaded.add(piece)
                    download_log += SUCCESS
                else:
                    download_log += FAILURE
                self.swarm_logger.log(download_log) 

    """
        piece selection stratergy is completely based on the bittorrent client
        most used piece selection stratergies are random piece selection stratergy
        and rarest first piece selection startergy
    """
    def piece_selection_startergy(self):
        return self.rarest_piece_first()

    """ 
        rarest first piece selection stratergy is implemented as below
    """
    def rarest_piece_first(self):
        try:
            rarest_piece = min(self.bitfield_pieces_count, key=self.bitfield_pieces_count.get)
            return rarest_piece
        except:
            return None

    """
        peer selection stratergy for selecting peer having particular piece
        function returns the peer index from the list of peers in swarm
    """
    def peer_selection_startergy(self, piece):
        return self.select_random_peer(piece)
        
    """
        random peer selection is implemented as given below.
    """
    def select_random_peer(self, piece):
        peers_having_piece = []
        for peer_index in range(len(self.peers_list)):
            if self.peers_list[peer_index].has_piece(piece):
                peers_having_piece.append(peer_index)
        return random.choice(peers_having_piece)

    """
        function helps in seeding the file in swarm
    """
    def seed_file(self):
        seeding_file_forever = True
        while seeding_file_forever:
            recieved_connection = self.client_peer.recieve_connection()
            if recieved_connection != None:
                # extract the connection socket and IP address of connection
                peer_socket, peer_address = recieved_connection
                peer_IP, peer_port = peer_address
                
                # make peer class object  
                peer_object = peer(peer_IP, peer_port, self.torrent, peer_socket)
                peer_object.set_bitfield() 
                peer_object.add_file_handler(self.file_handler)
                
                # start uploading pieces to this peer
                Thread(target = peer_object.upload_pieces).start()
                break
            else:
                time.sleep(1)




