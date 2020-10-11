import sys
import os
import hashlib
import random as rd
from datetime import datetime
from socket import *

"""
    The actual infomation about the file that is being shared among the peers
    along with information about the client overall downloaded/uploaded data
    chunks and additional information required 
"""

class torrent():

    def __init__(self, torrent_metadata):
        # store the orginal metadata extracted from the file
        self.torrent_metadata = torrent_metadata
        
        # torrent peer port revserved for bit torrent 
        self.port = 6881

        # information about the file being downloaded/uploaded
        self.uploaded = 0
        self.downloaded = 0
        self.left = 0
        self.bitfield = set([])
        self.requested_pieces = None
        self.downloaded_piece_offset = None
    
        # Azureus-style encoding for peer id
        self.peer_id = ('-PC0001-' + ''.join([str(rd.randint(0, 9)) for i in range(12)])).encode()





