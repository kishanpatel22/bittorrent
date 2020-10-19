import os
from queue import Queue 


"""
    General file input and output class, provides read and write data options
    However note that default mode of operations on file in read/write both
"""
class file_io():
    # initializes the file descripter
    def __init__(self, file_path):
        self.file_descriptor = os.open(file_path, os.O_RDWR | os.O_CREAT) 
        self.max_write_buffer = 1024
    
    # writes in file given bitstream
    def write(self, byte_stream):
        os.write(self.file_descriptor, byte_stream)   

    # reads from file given size of data to be read
    def read(self, buffer_size):
        byte_stream = os.read(self.file_descriptor, buffer_size)
        return byte_stream
    
    # writes file with all values to 0(null) given the size of file
    def write_null_values(self, data_size):
        while(data_size > 0):
            if data_size >= self.max_write_buffer:
                data_size = data_size - self.max_write_buffer
                data = b'\x00' * self.max_write_buffer
            else:
                data = b'\x00' * data_size
                data_size = 0
            self.write(data)
    
        
    # moves the file descripter to the given index position from start of file
    def move_descriptor_position(self, index_position):
        os.lseek(self.file_descriptor, index_position, SEEK_SET)


"""
    The peers use this class object to write pieces downloaded into file in 
    any order resulting into forming of orignal file using Bittorrent's 
    P2P architecture. Simply the class helps in writing pieces of the file 

    Queue is used for for managing the requests for read/write operations
    the python inbuild queue will help in handling these requests note that
    this function of request will e multithreaded 
"""

class torrent_shared_file_handler(file_io):
    
    # initialize the class with torrent and path where file needs to be downloaded
    def __init__(self, download_file_path, torrent):
        self.download_file_path = download_file_path
        self.torrent = torrent
        
        # file size in bytes
        self.file_size = torrent.torrent_metadata.file_size
        # piece size in bytes of torrent file data
        self.piece_size = torrent.torrent_metadata.piece_size

        # initlizes the file input/output object instance 
        self.download_file = file_io(self.download_file_path)
        # initialize the file with all the null values 
        self.download_file.max_write_buffer(self.file_size)
        
        
        # queue for handling all the file piece read/write request
        self.file_requests = Queue()


    # writes the given block of pieces into the file 
    # note that fiven datablock must be byte class object
    def write_block(self, piece_index, block_offset, data_block):

        # calulcate the position of fd using piece index and offset
        file_descriptor_position = pieces * self.piece_size + block_offset

        # move the file descripter to the desired location 
        self.download_file.move_descriptor_position(file_descriptor_position)
        
        # write the while block of data into the file
        self.download_file.write(data_block)


    # TODO : piece writing is different than the block writing in the file
    #        1) we need to validate the piece after writing in the file
    #        2) how do we do this process of validating and writing
    def write_piece(self, piece_index):
        pass


    def add_write_request(self, peer_message):
        self.file_requests(peer_message)





