#!/usr/bin/python3
import sys
from client import torrent_client

"""
    Client bittorrent protocol implementation in python
"""

def main(argv):
    # torrent file path as command line argument
    torrent_file_path = argv[1]
    # torrent client
    client = torrent_client(torrent_file_path)


if __name__ == '__main__':
    if(len(sys.argv) != 2):
        print('Usage of program is : python3 main.py <torrent_file>')
        sys.exit()
    else:
        main(sys.argv)
