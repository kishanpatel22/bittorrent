import os
from threading import *

"""
    General file input and output class, provides read and write data options
    However note that default mode of operations on file in read/write both
"""
class file_io():
    # initializes the file descripter
    def __init__(self, file_path):
        # file descriptor
        self.file_descriptor = os.open(file_path, os.O_RDWR | os.O_CREAT) 

    # writes in file given bitstream
    def write(self, byte_stream):
        os.write(self.file_descriptor, byte_stream)   

    # reads from file given size of data to be read
    def read(self, buffer_size):
        byte_stream = os.read(self.file_descriptor, buffer_size)
        return byte_stream
    
    # writes file with all values to 0(null) given the size of file
    def write_null_values(self, data_size):
        # maximum write buffer
        max_write_buffer = (2 ** 14)
        # move the file descriptor position
        self.move_descriptor_position(0)
        while(data_size > 0):
            if data_size >= max_write_buffer:
                data_size = data_size - max_write_buffer
                data = b'\x00' * max_write_buffer
            else:
                data = b'\x00' * data_size
                data_size = 0
            self.write(data)
        
    # moves the file descripter to the given index position from start of file
    def move_descriptor_position(self, index_position):
        os.lseek(self.file_descriptor, index_position, os.SEEK_SET)


"""
    The peers use this class object to write pieces downloaded into file in 
    any order resulting into forming of orignal file using Bittorrent's 
    P2P architecture. Simply class helps in writing/reading pieces in file 
"""
# TODO : case of multiple torrent files initialization needs to be handled
class torrent_shared_file_handler():
    
    # initialize the class with torrent and path where file needs to be downloaded
    def __init__(self, download_file_path, torrent):
        self.download_file_path = download_file_path
        self.torrent = torrent
        
        # file size in bytes
        self.file_size = torrent.torrent_metadata.file_size
        # piece size in bytes of torrent file data
        self.piece_size = torrent.torrent_metadata.piece_length

        # initlizes the file input/output object instance 
        self.download_file = file_io(self.download_file_path)
        
        # shared file lock
        self.shared_file_lock = Lock()
    
    # initialize the file before downloading 
    # function writes all null values in the file 
    def initialize_for_download(self):
        # initialize the file with all the null values 
        self.download_file.write_null_values(self.file_size)
   

    # calculates the position index in file given piece index and block offset
    def calculate_file_position(self, piece_index, block_offset):
        return piece_index * self.piece_size + block_offset
   

    # initialize the file descriptor given the piece index and block offset
    def initalize_file_descriptor(self, piece_index, block_offset):
        
        # calulcate the position in file using piece index and offset
        file_descriptor_position = self.calculate_file_position(piece_index, block_offset)

        # move the file descripter to the desired location 
        self.download_file.move_descriptor_position(file_descriptor_position)


    """
        function helps in writing a block from piece message recieved
    """
    def write_block(self, piece_message):
        # extract the piece index, block offset and data recieved from peer  
        piece_index     = piece_message.piece_index
        block_offset    = piece_message.block_offset
        data_block      = piece_message.block
        
        self.shared_file_lock.acquire()

        # initialize the file descriptor at given piece index and block offset
        self.initalize_file_descriptor(piece_index, block_offset)

        # write the block of data into the file
        self.download_file.write(data_block)

        self.shared_file_lock.release()


    """
        function helps in reading a block for file given piece index and block offset
        function returns the block of bytes class data that is read
    """
    def read_block(self, piece_index, block_offset, block_size):
            
        self.shared_file_lock.acquire()
        
        # initialize the file descriptor at given piece index and block offset
        self.initalize_file_descriptor(piece_index, block_offset)
        
        # read the block of data into the file
        data_block  = self.download_file.read(block_size)

        self.shared_file_lock.release()
        
        # return the read block of data
        return data_block
    


