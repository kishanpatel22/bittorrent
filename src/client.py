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
        
        # get the peer data from the recieved from the tracker
        peers_data = self.tracker.get_peers_data()
        
        # create peers instance from the list of peers obtained from tracker
        self.peers = peers(peers_data, self.torrent)
        
        self.peers.handshakes()








