import sys

# torrent file hander module for reading .torrent files
from torrent_file_handler import torrent_file_reader

# tracker module for making tracker request and recieving peer data
from tracker import torrent_tracker

# torrent module holds all the information about the torrent file
from torrent import *

# swarm module controls the operations over the multiple peers
from swarm import swarm

# share file handler module provides file I/O interface
from shared_file_handler import torrent_shared_file_handler

# torrent logger module for execution logging
from torrent_logger import *

TORRENT_FILE_PATH = 'torrent_file_path'
DOWNLOAD_DIR_PATH = 'download_directory_path'
SEEDING_DIR_PATH  = 'seeding_directory_path'
MAX_PEERS         = 'max_peers'
RATE_LIMIT        = 'rate_limit'
AWS               = 'AWS'

"""
    Torrent client would help interacting with the tracker server and
    download the files from other peers which are participating in sharing
"""

class bittorrent_client():
    """
        initialize the BTP client with torrent file and user arguments 
        reads the torrent file and creates torrent class object
    """
    def __init__(self, user_arguments):
        # extract the torrent file path 
        torrent_file_path = user_arguments[TORRENT_FILE_PATH]
        
        # bittorrent client logger
        self.bittorrent_logger = torrent_logger('bittorrent', BITTORRENT_LOG_FILE, DEBUG)
        self.bittorrent_logger.set_console_logging()
        
        self.bittorrent_logger.log('Reading ' + torrent_file_path + ' file ...')

        # read metadata from the torrent torrent file 
        self.torrent_info = torrent_file_reader(torrent_file_path)
        
        # decide whether the user want to download or seed the torrent
        self.client_request = {'seeding' : None,               'downloading': None,
                               'uploading rate' : sys.maxsize,  'downloading rate' : sys.maxsize,
                               'max peers' : 4, 'AWS' : False}
        
        # user wants to download the torrent file
        if user_arguments[DOWNLOAD_DIR_PATH]:
            self.client_request['downloading'] = user_arguments[DOWNLOAD_DIR_PATH]
            if user_arguments[RATE_LIMIT]:
                self.client_request['downloading rate'] = int(user_arguments[RATE_LIMIT])
        # user wants to seed the torrent file
        elif user_arguments[SEEDING_DIR_PATH]:
            self.client_request['seeding'] = user_arguments[SEEDING_DIR_PATH]
            if user_arguments[RATE_LIMIT]:
                self.client_request['uploading rate'] = int(user_arguments[RATE_LIMIT])
        
        # max peer connections 
        if user_arguments[MAX_PEERS]:
            self.client_request['max peers'] = int(user_arguments[MAX_PEERS])
        
        # AWS Cloud test
        if user_arguments[AWS]:
            self.client_request['AWS'] = True
        else:
            self.client_request['AWS'] = False
        
        # make torrent class instance from torrent data extracted from torrent file
        self.torrent = torrent(self.torrent_info.get_data(), self.client_request)
         
        self.bittorrent_logger.log(str(self.torrent))
        

    """
        functions helps in contacting the trackers requesting for 
        swarm information in which multiple peers are sharing file
    """
    def contact_trackers(self):
        self.bittorrent_logger.log('Connecting to Trackers ...')

        # get list of torrent tracker object from torrent file
        self.trackers_list = torrent_tracker(self.torrent)
        
        # get active tracker object from the list the trackers
        self.active_tracker = self.trackers_list.request_connection()
         
        self.bittorrent_logger.log(str(self.active_tracker))

    """
        function initilizes swarm from the active tracker connection 
        response peer data participating in file sharing
    """
    def initialize_swarm(self):
        self.bittorrent_logger.log('Initializing the swarm of peers ...')
        
        # get the peer data from the recieved from the tracker
        peers_data = self.active_tracker.get_peers_data()
            
        if self.client_request['downloading'] != None:

            # create swarm instance from the list of peers 
            self.swarm = swarm(peers_data, self.torrent)
        
        if self.client_request['seeding'] != None:
            # no need for peers recieved from tracker
            peers_data['peers'] = []
            # create swarm instance for seeding 
            self.swarm = swarm(peers_data, self.torrent)

    
    """
        function helps in uploading the torrent file that client has 
        downloaded completely, basically the client becomes the seeder
    """
    def seed(self):
        self.bittorrent_logger.log('Client started seeding ... ')
        
        # download file initialization 
        upload_file_path = self.client_request['seeding'] 
        
        # create file handler for downloading data from peers
        file_handler = torrent_shared_file_handler(upload_file_path, self.torrent)
        
        # add the file handler  
        self.swarm.add_shared_file_handler(file_handler)
        
        # start seeding the file 
        self.swarm.seed_file()


    """
        function helps in downloading the torrent file form swarm 
        in which peers are sharing file data
    """
    def download(self):
        # download file initialization 
        download_file_path = self.client_request['downloading'] + self.torrent.torrent_metadata.file_name

        self.bittorrent_logger.log('Initializing the file handler for peers in swarm ... ')

        # create file handler for downloading data from peers
        file_handler = torrent_shared_file_handler(download_file_path, self.torrent)

        # initialize file handler for downloading
        file_handler.initialize_for_download()
        
        # distribute file handler among all peers for reading/writing
        self.swarm.add_shared_file_handler(file_handler)
        
        self.bittorrent_logger.log('Client started downloading (check torrent statistics) ... ')
        
        # lastly download the whole file
        self.swarm.download_file() 



    """
        the event loop that either downloads / uploads a file
    """
    def event_loop(self):
        if self.client_request['downloading'] is not None:
            self.download()
        if self.client_request['seeding'] is not None:
            self.seed()

