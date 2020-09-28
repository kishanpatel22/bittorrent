#!/usr/bin/python3

import sys
from torrent_file_handler import torrent_file_reader

"""
    Torrent client would help interacting with the tracker server and
    download the files from other peers which are participating in sharing
"""

class torrent_client():
    def __init__(self, torrent_file_path):
        self.torrent_info = torrent_file_reader(torrent_file_path)
        self.torrent_info.log_metadata()

