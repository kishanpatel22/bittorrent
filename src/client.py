#!/usr/bin/python3

import sys
from torrent_file_handler import torrent_file_reader
from tracker import torrent_tracker
from torrent import *
from peers import peers

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
        
        # get the list of torrent tracker instance
        self.trackers_list = torrent_tracker(self.torrent)
        
        # make any tracker connection from the list of tracker
        self.tracker = self.trackers_list.request_connection()
        
        # get the list of all peers from the tracker connection response
        for peer_IP, peer_port in self.tracker.peers_list:
            print(peer_IP, peer_port)
        
        # create peers instance from the list of peers obtained from tracker
        self.peers = peers(self.tracker.peers_list, self.torrent)
        








