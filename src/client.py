import sys

# torrent file hander module for reading .torrent files
from torrent_file_handler import torrent_file_reader

# tracker module for making tracker request and recieving peer data
from tracker import torrent_tracker

# torrent module holds all the information about the file
from torrent import *

# swarm module controls the operations over the multiple peers
from swarm import swarm

# share file handler module provides file I/O interface
from shared_file_handler import torrent_shared_file_handler

TORRENT_FILE_PATH = 'torrent_file_path'
DOWNLOAD_DIR_PATH = 'download_directory_path'
SEEDING_DIR_PATH  = 'seeding_directory_path'

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
        
        # read metadata from the torrent torrent file 
        self.torrent_info = torrent_file_reader(torrent_file_path)
        
        # decide whether the user want to download or seed the torrent
        self.client_state = {'seeding' : None, 'downloading': None}
        
        # check if user wants to seed or download the torrent 
        if user_arguments[DOWNLOAD_DIR_PATH] != None:
            self.client_state['downloading'] = user_arguments[DOWNLOAD_DIR_PATH]
        elif user_arguments[SEEDING_DIR_PATH] != None:
            self.client_state['seeding'] = user_arguments[SEEDING_DIR_PATH]

        # make torrent class instance from torrent data extracted from torrent file
        self.torrent = torrent(self.torrent_info.get_data(), self.client_state)
        print(self.torrent)
    
    """
        functions helps in contacting the trackers requesting for 
        swarm information in which multiple peers are sharing file
    """
    def contact_trackers(self):
        # get list of torrent tracker object from torrent file
        self.trackers_list = torrent_tracker(self.torrent)
        
        # get active tracker object from the list the trackers
        self.active_tracker = self.trackers_list.request_connection()

        print(self.trackers_list)
        print(self.active_tracker)

    """
        function initilizes swarm from the active tracker connection 
        response peer data participating in file sharing
    """
    def initialize_swarm(self):
        # get the peer data from the recieved from the tracker
        peers_data = self.active_tracker.get_peers_data()
            
        if self.client_state['downloading'] != None:
            # create swarm instance from the list of peers 
            self.swarm = swarm(peers_data, self.torrent)
        
        if self.client_state['seeding'] != None:
            # no need for peers recieved from tracker
            peers_data['peers'] = []
            # create swarm instance for seeding 
            self.swarm = swarm(peers_data, self.torrent)

    
    """
        function helps in uploading the torrent file that client has 
        downloaded completely, basically the client becomes the seeder
    """
    def seed(self):
        # download file initialization 
        upload_file_path = self.client_state['seeding'] 
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
        download_file_path = self.client_state['downloading'] + self.torrent.torrent_metadata.file_name
        # create file handler for downloading data from peers
        file_handler = torrent_shared_file_handler(download_file_path, self.torrent)
        # initialize file handler for downloading
        file_handler.initialize_for_download()
        # distribute file handler among all peers for reading/writing
        self.swarm.add_shared_file_handler(file_handler)
        # lastly download the whole file
        self.swarm.download_file() 

    """
        the event loop that either downloads / uploads a file
    """
    def event_loop(self):
        if self.client_state['downloading'] is not None:
            self.download()
        if self.client_state['seeding'] is not None:
            self.seed()


