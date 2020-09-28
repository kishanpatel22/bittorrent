#!/usr/bin/python3

import sys

# bencodepy module : reads the bencoded data of the torrent file
from bencodepy import decode_from_file as torrent_extractor

# metadata format in the torrent file
from collections import OrderedDict 

"""
    Torrent file hanlders contain code related to torrent file reading and
    extracting useful information related to the metadata of the torrent file.
"""

# The class contains important metadata from the torrent file
class torrent_metadata():

    # usefull metadata from torrent file
    def __init__(self, trackers_list, file_name, file_size, piece_length, sha1_hash):
        self.trackers_list  = trackers_list     # list   : URL of trackers
        self.file_name      = file_name         # string : file name 
        self.file_size      = file_size         # int    : file size in bytes
        self.piece_length   = piece_length      # int    : piece length in bytes
        self.sha1_hash      = sha1_hash         # bytes  : sha1 hash of the file

"""
    Torrent file reader reads the benocoded file with torrent extension and 
    member functions of the class help in extracting data of type bytes class
    The torrent files contains the meta data in given format

    * announce          : the URL of the tracker
    * info              : ordered dictionary containing key and values 
        * files         : list of directories each containg the one file
            * length    : length of file in bytes
            * path      : contains path of each file
        * length        : length of the file
        * name          : name of the file
        * piece length  : number of bytes per piece
        * pieces        : list of SHA1 hash of the given files
"""

# Torrent File reader function
class torrent_file_reader(torrent_metadata):
    
    # encoding format of torrent files
    encoding = 'unicode_escape'
    
    # parameterized constructor 
    def __init__(self, torrent_file_path = None):
        try :
            # raw extract of the torrent file 
            self.torrent_file_raw_extract = torrent_extractor(torrent_file_path)
        except Exception as err:
            print('Error in reading given torrent file ! \n' + str(err))
            sys.exit()

        # formatted metadata from the torrent file
        self.torrent_file_extract = self.extract_torrent_metadata(self.torrent_file_raw_extract)
        
        # check if there is list of trackers 
        if 'announce-list' in self.torrent_file_extract.keys():
            trackers_list = self.torrent_file_extract['announce-list'] 
        else:
            trackers_list = [self.torrent_file_extract['announce']]
        
        # file name 
        file_name    = self.torrent_file_extract['info']['name']
        # file size in bytes 
        file_size    = self.torrent_file_extract['info']['length']
        # piece length in bytes
        piece_length = self.torrent_file_extract['info']['piece length']
        # sha1 hash 
        sha1_hash    = self.torrent_file_extract['info']['pieces']
    
        # base class constructor 
        super().__init__(trackers_list, file_name, file_size, piece_length, sha1_hash)
     

    # extracts the metadata from the raw data of given torrent extract
    # Note that in the given function the metadata of pieces is kept
    # in bytes class since the decode cannot decode the SHA1 hash

    def extract_torrent_metadata(self, torrent_file_raw_extract):

        # torrent metadata is ordered dictionary 
        torrent_extract = OrderedDict()
        
        # extract all the key values pair in raw data and decode them
        for key, value in torrent_file_raw_extract.items():
            # decoding the key
            new_key = key.decode(self.encoding)
            # if type of value is of type dictionary then do deep copying
            if type(value) == OrderedDict:
                torrent_extract[new_key] = self.extract_torrent_metadata(value)
            # if type of value is of type list
            elif type(value) == list :
                torrent_extract[new_key] = list(map(lambda x : x[0].decode(self.encoding), value))
            # if type of value if of types byte
            elif type(value) == bytes and new_key != 'pieces':
                torrent_extract[new_key] = value.decode(self.encoding)
            else :
                torrent_extract[new_key] = value

        # torrent extracted metadata
        return torrent_extract


    # logs the partial meta data of torrent
    def log_metadata(self):
        print('=================== TORRENT_FILE METADATA ===================')
        print('Trackers List : ' + str(self.trackers_list))
        print('File name     : ' + str(self.file_name))
        print('File size     : ' + str(self.file_size) + ' B')
        print('Piece length  : ' + str(self.piece_length) + ' B')
        print('=============================================================')


    # provides torrent file full information
    def __str__(self):
        logging_info = ""
        for key, value in self.torrent_file_extract.items():
            logging_info = logging_info + str(key) + "\t: " + str(value) + "\n"
        return logging_info





