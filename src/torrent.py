import hashlib
import random as rd

# module problems torrent statistics 
from torrent_statistics import *


"""
    The actual infomation about the file that is being shared among the peers
    along with information about the client overall downloaded/uploaded data
    chunks and additional information required 
"""

class torrent():

    def __init__(self, torrent_metadata, client_state):
        # store the orginal metadata extracted from the file
        self.torrent_metadata   = torrent_metadata
        self.client_state       = client_state

        # torrent peer port reserved for bittorrent, this will be used 
        # for listening to the peer request for uploading (seeding)
        self.client_port = 6881
        self.client_IP = ''
            
        # downloaded and uploaded values 
        self.statistics = torrent_statistics()
            
        # pieces divided into chunks of fixed block size
        self.block_length   = 16 * (2 ** 10) 
            
        # if the client wants to upload the file 
        if self.client_state['seeding'] != None:
            self.statistics.num_pieces_downloaded = self.torrent_metadata.file_size

        # the count of the number pieces that the files is made of
        self.pieces_count = int(len(self.torrent_metadata.pieces) / 20)

        # Azureus-style encoding for peer id
        self.peer_id = ('-PC0001-' + ''.join([str(rd.randint(0, 9)) for i in range(12)])).encode()
    
    
    # gets the length of the piece given the piece index
    def get_piece_length(self, piece_index):
        # check if piece if the last piece of file
        if piece_index == self.pieces_count - 1:
            return self.torrent_metadata.file_size - self.torrent_metadata.piece_length * (piece_index)
        else:
            return self.torrent_metadata.piece_length
  

    # get validates piece length of given piece
    def validate_piece_length(self, piece_index, block_offset, block_length):
        if block_length > self.block_length:
            return False
        elif block_length + block_offset > self.get_piece_length(piece_index):
            return False
        return True
        

    # logs the torrent information of torrent
    def __str__(self):
        torrent_log  =  'CLIENT TORRENT DATA : (client state = ' 
        if self.client_state['downloading'] != None:
            torrent_log += 'downloading)\n'
        if self.client_state['seeding'] != None:
            torrent_log += 'seeding)\n'

        torrent_log += 'File name       : ' + str(self.torrent_metadata.file_name)              + '\n'
        torrent_log += 'File size       : ' + str(self.torrent_metadata.file_size)    + ' B'    + '\n'
        torrent_log += 'Piece length    : ' + str(self.torrent_metadata.piece_length) + ' B'    + '\n'
        torrent_log += 'Info hash       : ' + str(self.torrent_metadata.info_hash)              + '\n'
        torrent_log += 'Files           : ' + str(self.torrent_metadata.files)                  + '\n'
        torrent_log += 'No. of Pieces   : ' + str(self.pieces_count)                            + '\n'
        torrent_log += 'Client port     : ' + str(self.client_port)                             + '\n'
        torrent_log += 'Client peer ID  : ' + str(self.peer_id)                                 + '\n'
        
        return torrent_log


