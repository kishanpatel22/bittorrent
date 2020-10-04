import sys
import requests
import bencodepy
from torrent_file_handler import torrent_metadata

"""
    Trackers are required to obtain the list of peers currently participating
    in the file sharing process and client must know how to communicate with 
    the list of trackers provided in the torrent file
"""


"""
    Tracker class stores the information that is needed for communicating with
    the tracker URL servers. The request paramters are included as given below
"""

class tracker_data():
        
    # contructs the tracker request data 
    def __init__(self, torrent):
        self.compact = 1
        # the request parameters of the torrent 
        self.request_parameters = {
            'info_hash' : torrent.torrent_metadata.info_hash,
            'peer_id'   : torrent.peer_id,
            'port'      : torrent.peer_port,
            'uploaded'  : torrent.uploaded,
            'downloaded': torrent.downloaded,
            'left'      : torrent.left,
            'compact'   : self.compact
        }

    # extract the important information for the response dictionary 
    def parse_tracker_response(self, raw_response_dict):
        
        # interval : specifies minimum time client show wait for sending next request 
        if b'interval' in raw_response_dict:
            self.interval = raw_response_dict[b'interval']

        # list of peers form the participating the torrent
        if b'peers' in raw_response_dict:
            self.peers_list = []
            # extract the raw peers data 
            raw_peers_data = raw_response_dict[b'peers']
            # create a list of each peer information which is of 6 bytes
            raw_peers_list = (raw_peers_data[i : 6 + i] for i in range(0, len(raw_peers_data), 6))
            # extract all the peer id, peer IP and peer port
            for raw_peer_data in raw_peers_list:
                # extract the peer IP address 
                peer_IP = ".".join(str(a) for a in raw_peer_data[0:4])
                # extract the peer port number
                peer_port = int("".join(str(a) for a in raw_peers_data[5:6]))
                self.peers_list.append((peer_IP, peer_port))
            
        # number of peers with the entire file
        if b'complete' in raw_response_dict:
            self.complete = raw_response_dict[b'complete']

        # number of non-seeder peers, aka "leechers"
        if b'incomplete' in raw_response_dict:
            self.incomplete = raw_response_dict[b'incomplete']
        
        # tracker id must be sent back by the user on announcement
        if b'tracker id' in raw_response_dict:
            self.tracker_id = raw_response_dict[b'tracker id']


"""
    Class HTTP torrent tracker helps the client communicate to any HTTP torrent 
    tracker. However the base class containing data of torrent remains the 
    same only way to communicate changes
"""
class http_torrent_tracker(tracker_data):
    # contructor : initializes the torrent information
    def __init__(self, torrent, tracker_url):
        self.tracker_url = tracker_url
        super().__init__(torrent)
    
    # attempts to connect to HTTP tracker
    # returns true if conncetion is established false otherwise
    def request_torrent_information(self):
        # try establishing a connection to the tracker
        try:
            # the reponse from HTTP tracker is an bencoded dictionary 
            bencoded_response = requests.get(self.tracker_url, self.request_parameters)
            # decode the bencoded dictionary to python ordered dictionary 
            raw_response_dict = bencodepy.decode(bencoded_response.content)
            # parse the dictionary containing raw data
            self.parse_tracker_response(raw_response_dict)
            return True
        # TODO : except block must log why it was not able to connect the tracker
        except:
            # cannont establish a connection with the tracker
            return False


"""
    Class UDP torrent tracker helps the client communicate to any HTTP torrent 
    tracker. However the base class data of torrent remains the same only way
    to communicate will change
"""
# TODO : implementation is left
class udp_torrent_tracker(tracker_data):
    pass


"""
    Torrent tracker class helps then client to connect to any of the trackers
    provided. Note it will identify http or udp trackers and will communicate
    with them accordingly
"""
class torrent_tracker():
    # tracker for the torrent
    tracker = None
    
    # contructors initializes a torernt tracker connection given 
    # the tracker urls from the torrent metadata file
    def __init__(self, torrent):
        # get all the trackers list of the torrent data
        self.trackers_list = []
        for tracker_url in torrent.torrent_metadata.trackers_url_list:
            # classify HTTP and UDP torrent trackers
            if 'http' in tracker_url[:4]:
                tracker = http_torrent_tracker(torrent, tracker_url)
            if 'udp' in tracker_url[:4]:
                tracker = udp_torrent_tracker(torrent, tracker_url)
            self.trackers_list.append(tracker)
        
        # try connecting with any of the tracker obtained in the list
        for tracker in self.trackers_list:
            if(tracker.request_torrent_information()):
                self.tracker = tracker
                break

