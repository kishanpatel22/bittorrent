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
        
        # torrent peer port reserved for bittorrent, this will be used 
        # for listening to the peer request for uploading (seeding)
        self.port = 6881
            
        # downloaded and uploaded values
        self.uploaded = 0 
        self.downloaded = 0                                                    
        self.left = 0    

        # the count of the number pieces that the files is made of
        self.pieces_count = int(len(self.torrent_metadata.pieces) / 20)

        # Azureus-style encoding for peer id
        self.peer_id = ('-PC0001-' + ''.join([str(rd.randint(0, 9)) for i in range(12)])).encode()
    
    
    # gets the length of the piece given the piece index
    # note that the code handles the case when last piece index is requested
    def get_piece_length(self, piece_index):
        # check if piece if the last piece of file
        if piece_index == self.pieces_count - 1:
            return self.torrent_metadata.file_size - self.torrent_metadata.piece_length * (piece_index)
        else:
            return self.torrent_metadata.piece_length
   


    # logs the torrent information of torrent
    def __str__(self):
        logging_info =  'TORRENT INFORMATION : '+ '\n'
        logging_info += 'Trackers List  : ' + str(self.torrent_metadata.trackers_url_list)      + '\n'
        logging_info += 'File name      : ' + str(self.torrent_metadata.file_name)              + '\n'
        logging_info += 'File size      : ' + str(self.torrent_metadata.file_size) + ' B'       + '\n'
        logging_info += 'Piece length   : ' + str(self.torrent_metadata.piece_length) + ' B'    + '\n'
        logging_info += 'Info hash      : ' + str(self.torrent_metadata.info_hash)              + '\n'
        logging_info += 'Files          : ' + str(self.torrent_metadata.files)                  + '\n'
        logging_info += 'No. of Pieces  : ' + str(self.pieces_count)                            + '\n'
        logging_info += 'Client port    : ' + str(self.port)                                    + '\n'
        logging_info += 'Client peer ID : ' + str(self.peer_id)                                 + '\n'
        logging_info += '\n'
        return logging_info




