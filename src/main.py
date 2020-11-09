#!/usr/bin/python3
import sys
import argparse

# bittorrent client module for P2P sharing
from client import *

"""
    Client bittorrent protocol implementation in python
"""

def main(user_arguments):
   
    # create torrent client object 
    client = bittorrent_client(user_arguments)
    
    # contact the trackers
    client.contact_trackers()
    
    """ 
    # initialize the swarm of peers
    client.initialize_swarm()
    
    # download the file from the swarm
    client.event_loop()
    """


if __name__ == '__main__':
    # argument parser for bittorrent
    parser = argparse.ArgumentParser(description="Parses command.")
    parser.add_argument(TORRENT_FILE_PATH, help='unix file path of torrent file')
    parser.add_argument("-d", "--" + DOWNLOAD_DIR_PATH, help="unix directory path of downloading file")
    parser.add_argument("-s", "--" + SEEDING_DIR_PATH, help="unix directory path for the seeding file")

    # get the user input option after parsing the command line argument
    options = vars(parser.parse_args(sys.argv[1:]))
    
    if(options[DOWNLOAD_DIR_PATH] is None and options[SEEDING_DIR_PATH] is None):
        print('Bittorrent client works only with either download or upload arguments !')
        sys.exit(1)
        
    main(options)
