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
        Updates bitfield count values obtained from peers in swarm
        global state of count of different pieces available in swarm
    """
    def update_bitfield_count(self, bitfield_pieces):
        for piece in bitfield_pieces:
            if piece in self.bitfield_pieces_count.keys():
                self.bitfield_pieces_count[piece] += 1
            else:
                self.bitfield_pieces_count[piece] = 1
    
    """
        function performs the initial connection with peer by doing handshakes 
        initializing bitfields and updating the global bitfield count
    """
    def connect_to_peer(self, peer_index):
        # perfrom handshake with peer
        self.peers_list[peer_index].initiate_handshake()
        # recieve the bitfields from peer
        peer_bitfield_pieces = self.peers_list[peer_index].initialize_bitfield()
        self.swarm_lock.acquire()
        # update the bitfield count value in swarm
        self.update_bitfield_count(peer_bitfield_pieces) 
        self.swarm_lock.release()
        # used for EXCECUTION LOGGING
        self.swarm_logger.log(self.peers_list[peer_index].get_handshake_log())
         

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
        functions checks if the file handler has been added or not
    """
    def have_file_handler(self):
        if self.file_handler is None:
            download_log  = 'Cannot download file : '
            download_log += ' file handler not instantiated ! ' + FAILURE
            self.swarm_logger.log(download_log)
            return False
        return True

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
        if not self.have_file_handler():
            return False
        
        # initialize bitfields asynchronously
        for peer_index in range(len(self.peers_list)):
            connect_peer_thread = Thread(target = self.connect_to_peer, args=(peer_index, ))
            connect_peer_thread.start()
        
        # simultaneouly start downloading the file from peers
        download_thread = Thread(target = self.download_using_stratergies)
        download_thread.start()


    """
        downloads the file from peers in swarm using some stratergies of peice
        selection and peer selection respectively
    """
    def download_using_stratergies(self):
        while not self.download_complete():
            piece = self.piece_selection_startergy()
            if piece is not None:
                peer_index = self.peer_selection_startergy(piece)
                is_piece_downloaded = self.peers_list[peer_index].piece_downlaod_FSM(piece)
                if is_piece_downloaded:
                    self.bitfield_pieces_downloaded.add(piece)
                    del self.bitfield_pieces_count[piece]

    """
        piece selection stratergy is completely based on the bittorrent client
        most used piece selection stratergies are random piece selection stratergy
        and rarest first piece selection startergy
    """
    def piece_selection_startergy(self):
        return self.rarest_piece_first()

    """ 
        rarest first piece selection stratergy always selects the rarest piece
        in the swarm, note if there are multiple rarest pieces then the
        function returns any random rarest piece.
    """
    def rarest_piece_first(self):
        rarest_piece = None
        if len(self.bitfield_pieces_count) != 0:
            rarest_piece_count = min(self.bitfield_pieces_count.values())
            rarest_pieces = [piece for piece in self.bitfield_pieces_count if 
                            self.bitfield_pieces_count[piece] == rarest_piece_count]
            rarest_piece = random.choice(rarest_pieces)
        return rarest_piece

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
            if self.peers_list[peer_index].have_piece(piece):
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



