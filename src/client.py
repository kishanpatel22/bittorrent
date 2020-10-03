#!/usr/bin/python3

import sys
from torrent_file_handler import torrent_file_reader
from tracker import torrent_tracker
from torrent import *

"""
    Torrent client would help interacting with the tracker server and
    download the files from other peers which are participating in sharing
"""

class torrent_client():
    def __init__(self, torrent_file_path):
        # metadata of the raw torrent file 
        self.torrent_info = torrent_file_reader(torrent_file_path)
            
        # make torrent class instance from the torrent data extracted from torrent file
        self.torrent = torrent(self.torrent_info.get_data())

        # any tracker connection from the list of trackers
        self.tracker = torrent_tracker(self.torrent)

