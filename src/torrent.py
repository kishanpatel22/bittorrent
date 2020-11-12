import hashlib
import random as rd

# module problems torrent statistics 
from torrent_statistics import *

# module for printing data in Tabular format
from beautifultable import BeautifulTable

"""
    The actual infomation about the file that is being shared among the peers
    along with information about the client overall downloaded/uploaded data
    chunks and additional information required 
"""

class torrent():

    def __init__(self, torrent_metadata, client_request):
        # store the orginal metadata extracted from the file
        self.torrent_metadata   = torrent_metadata
        self.client_request     = client_request

        # torrent peer port reserved for bittorrent, this will be used 
        # for listening to the peer request for uploading (seeding)
        self.client_port = 6881
        self.client_IP = ''
            
        # downloaded and uploaded values 
        self.statistics = torrent_statistics(self.torrent_metadata)
            
        # pieces divided into chunks of fixed block size
        self.block_length   = 16 * (2 ** 10) 
        
        # piece length of torrent file
        self.piece_length = torrent_metadata.piece_length

        # if the client wants to upload the file 
        if self.client_request['seeding'] != None:
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
        column_header =  'CLIENT TORRENT DATA\n (client state = '
        if self.client_request['downloading'] != None:
            column_header += 'downloading)\n'
        if self.client_request['seeding'] != None:
            column_header += 'seeding)\n'
        
        torrent_file_table = BeautifulTable()
        torrent_file_table.columns.header = [column_header, "DATA VALUE"]
        
        # file name
        torrent_file_table.rows.append(['File name', str(self.torrent_metadata.file_name)])
        # file size
        torrent_file_table.rows.append(['File size', str(round(self.torrent_metadata.file_size / (2 ** 20), 2)) + ' MB'])
        # piece length 
        torrent_file_table.rows.append(['Piece length', str(self.torrent_metadata.piece_length)])
        # info hash
        torrent_file_table.rows.append(['Info hash', '20 Bytes file info hash value'])
        # files (multiple file torrents)
        if self.torrent_metadata.files:
            torrent_file_table.rows.append(['Files', str(len(self.torrent_metadata.files))])
        else:
            torrent_file_table.rows.append(['Files', str(self.torrent_metadata.files)])
        # number of pieces in file 
        torrent_file_table.rows.append(['Number of Pieces', str(self.pieces_count)])
        # client port
        torrent_file_table.rows.append(['Client port', str(self.client_port)])
        torrent_file_table.rows.append(['Client peer ID', str(self.peer_id)])
        
        return str(torrent_file_table)


