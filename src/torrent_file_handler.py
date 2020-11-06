#!/usr/bin/python3

import sys

# import bencodepy for reading the torrent metadata
import bencodepy

# metadata format in the torrent file
from collections import OrderedDict 

# hashlib for generating sha1 hash values
import hashlib

# torrent logger for execution logging
from torrent_logger import *

# user defined class for rasing torrent execptions
from torrent_error import *


"""
    Torrent file hanlders contain code related to torrent file reading and
    extracting useful information related to the metadata of the torrent file.
"""


"""
    Torrent file meta information is stored by this class instance
"""
# The class contains important metadata from the torrent file
class torrent_metadata():

    # usefull metadata from torrent file
    def __init__(self, trackers_url_list, file_name, file_size, piece_length, pieces, info_hash, files):
        self.trackers_url_list  = trackers_url_list     # list   : URL of trackers
        self.file_name      = file_name                 # string : file name 
        self.file_size      = file_size                 # int    : file size in bytes
        self.piece_length   = piece_length              # int    : piece length in bytes
        self.pieces         = pieces                    # bytes  : sha1 hash concatination of file
        self.info_hash      = info_hash                 # sha1 hash of the info metadata
        self.files          = files                     # list   : [length, path] (multifile torrent)

    # logs the meta data of torrent
    def __str__(self):
        logging_info =  'TORRENT FILE METADATA : '                         + '\n'
        logging_info += 'Trackers List : ' + str(self.trackers_url_list)   + '\n'
        logging_info += 'File name     : ' + str(self.file_name)           + '\n'
        logging_info += 'File size     : ' + str(self.file_size)    + ' B' + '\n'
        logging_info += 'Piece length  : ' + str(self.piece_length) + ' B' + '\n'
        logging_info += 'Files         : ' + str(self.files)               + '\n'
        logging_info += '\n'
        return logging_info


"""
    Torrent file reader reads the benocoded file with torrent extension and 
    member functions of the class help in extracting data of type bytes class
    The torrent files contains the meta data in given format

    * announce          : the URL of the tracker
    * info              : ordered dictionary containing key and values 
        * files         : list of directories each containg files (in case of multile files)
            * length    : length of file in bytes
            * path      : contains path of each file
        * length        : length of the file (in case of single files)
        * name          : name of the file
        * piece length  : number of bytes per piece
        * pieces        : list of SHA1 hash of the given files
"""

# Torrent File reader function
class torrent_file_reader(torrent_metadata):
    
    # parameterized constructor 
    def __init__(self, torrent_file_path):
        # the torrent_class logger
        self.torrent_file_logger = torrent_logger('torrent file', TORRENT_LOG_FILE, DEBUG)
        try :
            # raw extract of the torrent file 
            self.torrent_file_raw_extract = bencodepy.decode_from_file(torrent_file_path)
            # used for EXCECUTION LOGGING
            torrent_read_log = 'Torrent file decoded successfully ' + SUCCESS
            self.torrent_file_logger.log(torrent_read_log)
        except Exception as err:
            # used for EXCECUTION LOGGING
            torrent_read_log = 'Torrent file decoding failed ! ' + FAILURE + err.__str__()
            self.torrent_file_logger.log(torrent_read_log)
            sys.exit()
        
        # check if encoding scheme is given in dictionary
        if b'encoding' in self.torrent_file_raw_extract.keys():
            self.encoding = self.torrent_file_raw_extract[b'encoding'].decode()
        else:
            self.encoding = 'UTF-8'
        
        # formatted metadata from the torrent file
        self.torrent_file_extract = self.extract_torrent_metadata(self.torrent_file_raw_extract)
        
        # check if there is list of trackers 
        if 'announce-list' in self.torrent_file_extract.keys():
            trackers_url_list = self.torrent_file_extract['announce-list'] 
        else:
            trackers_url_list = [self.torrent_file_extract['announce']]
        
        # file name 
        file_name    = self.torrent_file_extract['info']['name']
        # piece length in bytes
        piece_length = self.torrent_file_extract['info']['piece length']
        # sha1 hash concatenation of all pieces of files
        pieces       = self.torrent_file_extract['info']['pieces']
        # info hash generated for trackers
        info_hash    = self.generate_info_hash()
            

        # files is list of tuple of size and path in case of multifile torrent
        files = None

        # check if torrent file contains multiple paths 
        if 'files' in self.torrent_file_extract['info'].keys():
            # file information - (length, path)
            files_dictionary = self.torrent_file_extract['info']['files']
            files = [(file_data['length'], file_data['path']) for file_data in files_dictionary]
            file_size = 0
            for file_length, file_path in files:
                file_size += file_length
        else : 
            # file size in bytes 
            file_size = self.torrent_file_extract['info']['length']
       
        # base class constructor 
        super().__init__(trackers_url_list, file_name, file_size, piece_length, pieces, info_hash, files)
            
        # used for EXCECUTION LOGGING
        self.torrent_file_logger.log(self.__str__())


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
            # if the current torrent file could have multiple files with paths
            elif type(value) == list and new_key == 'files':
                torrent_extract[new_key] = list(map(lambda x : self.extract_torrent_metadata(x), value))
            elif type(value) == list and new_key == 'path':
                torrent_extract[new_key] = value[0].decode(self.encoding)
            # url list parameter
            elif type(value) == list and new_key == 'url-list' or new_key == 'collections':
                torrent_extract[new_key] = list(map(lambda x : x.decode(self.encoding), value))
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


    # info_hash from the torrent file
    def generate_info_hash(self):
        sha1_hash = hashlib.sha1()
        # get the raw info value
        raw_info = self.torrent_file_raw_extract[b'info']
        # update the sha1 hash value
        sha1_hash.update(bencodepy.encode(raw_info))
        return sha1_hash.digest()
    

    # return the torrent instance 
    def get_data(self):
        return torrent_metadata(self.trackers_url_list, self.file_name, 
                                self.file_size,         self.piece_length,      
                                self.pieces,            self.info_hash, self.files)
    
    # provides torrent file full information
    def __str__(self):
        torrent_file_log  = 'TORRENT FILE READ CONTAINS DATA : '                + '\n'
        torrent_file_log += 'Trackers List  : ' + self.trackers_url_list[0]     + '\n'
        for tracker_url in self.trackers_url_list[1:]:
            torrent_file_log += '                 ' + tracker_url               + '\n'
        torrent_file_log += 'File name      : ' + str(self.file_name)           + '\n'
        torrent_file_log += 'File size      : ' + str(self.file_size)    + ' B' + '\n'
        torrent_file_log += 'Piece length   : ' + str(self.piece_length) + ' B' + '\n'
        torrent_file_log += 'Info hash      : ' + str(self.info_hash)           + '\n'
        torrent_file_log += 'Files          : ' + str(self.files)               + '\n'
        return torrent_file_log

