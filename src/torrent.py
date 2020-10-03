import sys
import os
import hashlib
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
        
        # torrent peer socket for communicating with the tracker
        self.peer_socket = socket(AF_INET, SOCK_STREAM)
        self.peer_port = 12345
        self.peer_hostname = ''
        self.peer_socket.bind((self.peer_hostname, self.peer_port)) 
        self.peer_socket.listen(1)

        # information about the file being downloaded/uploaded
        self.uploaded = 0
        self.downloaded = 0
        self.left = 0
        self.bitfield = set([])
        self.requested_pieces = None
        self.downloaded_piece_offset = None
    
        # urlencoded 20-byte string used as a unique ID for the torrent
        peer_id_sha = hashlib.sha1()
        peer_id_sha.update(str(os.getpid()).encode())
        peer_id_sha.update(str(datetime.now()).encode())
        self.peer_id = peer_id_sha.digest()



