import sys
import time
import random
from copy import deepcopy
from datetime import timedelta
from threading import *
from peer import peer
from torrent_error import *
from torrent_logger import *

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
        self.torrent    = deepcopy(torrent)
        self.interval   = peers_data['interval']
        self.seeders    = peers_data['seeders']
        self.leechers   = peers_data['leechers']
    
        # create a peer instance for all the peers recieved 
        self.peers_list = []
        # used for AWS Cloud test
        if self.torrent.client_request['AWS']:
            self.peers_list.append(peer('34.238.166.126', 6881, torrent))

        for peer_IP, peer_port in peers_data['peers']:
            self.peers_list.append(peer(peer_IP, peer_port, torrent))
        
        # bitfields from all peers
        self.bitfield_pieces_count = dict()

        # selecting the top N peers / pieces
        self.top_n = self.torrent.client_request['max peers']

        # peers logger object
        self.swarm_logger = torrent_logger('swarm', SWARM_LOG_FILE, DEBUG)
        # torrent stats logger object
        self.torrent_stats_logger = torrent_logger('torrent_statistics', TORRENT_STATS_LOG_FILE, DEBUG)
        self.torrent_stats_logger.set_console_logging()

        # bitfield for pieces downloaded from peers
        self.bitfield_pieces_downloaded = set([])
                
        # file handler for downloading / uploading file data
        self.file_handler = None
    
        # minimum pieces to recieve randomly
        self.minimum_pieces = 10

        # check if the torrent file is for seeding
        if torrent.client_request['seeding'] != None:
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
        function checks if there are any active connections in swarm
    """
    def have_active_connections(self):
        for peer in self.peers_list:
            if peer.peer_sock.peer_connection_active():
                return True
        return False
      
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
        # check if file handler is initialized
        if not self.have_file_handler():
            return False
        # initialize bitfields asynchronously
        for peer_index in range(len(self.peers_list)):
            connect_peer_thread = Thread(target = self.connect_to_peer, args=(peer_index, ))
            connect_peer_thread.start()
        # asynchornously start downloading pieces of file from peers
        download_thread = Thread(target = self.download_using_stratergies)
        download_thread.start()

    """
        downloads the file from peers in swarm using some stratergies of peice
        selection and peer selection respectively
    """
    def download_using_stratergies(self):
        self.download_start_time = time.time()
        while not self.download_complete():
            # select the pieces and peers for downloading
            pieces = self.piece_selection_startergy()
            peer_indices = self.peer_selection_startergy()

            # asynchornously download the rarest pieces from the top four peers
            downloading_thread_pool = []
            for i in range(min(len(pieces), len(peer_indices))):
                piece = pieces[i]
                peer_index = peer_indices[i]
                downloading_thread = Thread(target=self.download_piece, args=(piece, peer_index, ))
                downloading_thread_pool.append(downloading_thread)
                downloading_thread.start()
            # wait untill you finish the downloading of the pieces
            for downloading_thread in downloading_thread_pool:
                downloading_thread.join()
        self.download_end_time = time.time()
        
        # used for EXCECUTION LOGGING
        download_log  = 'File downloading time : '
        download_log += str(timedelta(seconds=(self.download_end_time - self.download_start_time))) 
        download_log += ' Average download rate : ' 
        download_log += str(self.torrent.statistics.avg_download_rate) + ' Kbps\n'
        download_log += 'Happy Bittorrenting !'
        self.torrent_stats_logger.log(download_log)

    """
        function downloads piece given the peer index and updates the 
        of downloaded pieces from the peers in swarm
    """
    def download_piece(self, piece, peer_index):
        start_time = time.time()
        is_piece_downloaded = self.peers_list[peer_index].piece_downlaod_FSM(piece)
        end_time = time.time()
        if is_piece_downloaded:
            # acquire lock for update the global data items
            self.swarm_lock.acquire() 
            # update the bifields pieces downloaded
            self.bitfield_pieces_downloaded.add(piece)
            # delete the pieces from the count of pieces
            del self.bitfield_pieces_count[piece]
            # update the torrent statistics
            self.torrent.statistics.update_start_time(start_time)
            self.torrent.statistics.update_end_time(end_time)
            self.torrent.statistics.update_download_rate(piece, self.torrent.piece_length)
            self.torrent_stats_logger.log(self.torrent.statistics.get_download_statistics())
            # release the lock after downloading
            self.swarm_lock.release() 

    """
        piece selection stratergy is completely based on the bittorrent client
        most used piece selection stratergies are random piece selection stratergy
        and rarest first piece selection startergy
    """
    def piece_selection_startergy(self):
        return self.rarest_pieces_first()

    """ 
        rarest first piece selection stratergy always selects the rarest piece
        in the swarm, note if there are multiple rarest pieces then the
        function returns any random rarest piece.
    """
    def rarest_pieces_first(self):
        # check if bitfields are recieved else wait for some time
        while(len(self.bitfield_pieces_count) == 0):
            time.sleep(5)
        # get the rarest count of the pieces
        rarest_piece_count = min(self.bitfield_pieces_count.values())
        # find all the pieces with the rarest piece
        rarest_pieces = [piece for piece in self.bitfield_pieces_count if 
                         self.bitfield_pieces_count[piece] == rarest_piece_count] 
        # shuffle among the random pieces 
        random.shuffle(rarest_pieces)
        # rarest pieces
        return rarest_pieces[:self.top_n]

    """
        peer selection stratergy for selecting peer having particular piece
        function returns the peer index from the list of peers in swarm
    """
    def peer_selection_startergy(self):
        # used for AWS Cloud test
        if self.torrent.client_request['AWS']:
            return [self.select_specific_peer()]
        # select random peers untill you have some pieces
        if len(self.bitfield_pieces_downloaded) < self.minimum_pieces:
            return self.select_random_peers()
        # select the top peers with high download rates
        else:
            return self.top_peers()

    """
        random peer selection is implemented as given below.
    """
    def select_random_peers(self):
        peer_indices = []
        # select all the peers that have pieces to offer
        for index in range(len(self.peers_list)):
            if len(self.peers_list[index].bitfield_pieces) != 0:
                peer_indices.append(index)
        random.shuffle(peer_indices)
        return peer_indices[:self.top_n]
    
    """
        selects the specific peer in the list(used only for testing of seeding)
    """
    def select_specific_peer(self):
        peer_index = 0
        return peer_index
        
    """
        selects the top fours peer having maximum download rates
        sort the peers in by the rate of downloading and selects top four
    """
    def top_peers(self):
        # sort the peer list according peer comparator
        self.peers_list = sorted(self.peers_list, key=self.peer_comparator, reverse=True)
        # top 4 peer index
        return [peer_index for peer_index in range(self.top_n)]

    """
        comparator function for sorting the peer with highest downloading rate
    """
    def peer_comparator(self, peer):
        if not peer.peer_sock.peer_connection_active():
            return -sys.maxsize
        return peer.torrent.statistics.avg_download_rate
    
    """
        function helps in seeding the file in swarm
    """
    def seed_file(self):
        seeding_log = 'Seeding started by client at ' + self.client_peer.unique_id
        self.swarm_logger.log(seeding_log)
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
                # start uploading file pieces to this peer
                Thread(target = self.upload_file, args=(peer_object,)).start()
            else:
                time.sleep(1)

    """
        function helps in uploading the file pieces to given peer when requested
    """
    def upload_file(self, peer):
        # initial seeding messages
        if not peer.initial_seeding_messages():
            return 
        # after inital messages start exchanging uploading message
        peer.piece_upload_FSM()


