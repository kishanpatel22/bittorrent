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

class tracker():

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

"""
    Class HTTP torrent tracker helps the client communicate to any HTTP torrent 
    tracker. However the base class data of torrent remains the same only way
    to communicate will change
"""

class http_torrent_tracker(tracker):
    def __init__(self, torrent, tracker_url):
        self.tracker_url = tracker_url
        super().__init__(torrent)

"""
    Class UDP torrent tracker helps the client communicate to any HTTP torrent 
    tracker. However the base class data of torrent remains the same only way
    to communicate will change
"""
class udp_torrent_tracker(tracker):
    pass


"""
    Torrent tracker class helps then client to connect to any of the trackers
    provided. Note it will identify http or udp trackers and will communicate
    with them accordingly
"""
class torrent_tracker():
    
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
        
        # try connecting with any of the tracker 
        for tracker in self.trackers_list:
            try:
                response = requests.get(tracker.tracker_url, tracker.request_parameters)
                print(bencodepy.encode(response.text))
            except:
                print(tracker.tracker_url + ' : TRACKER NOT CONNECTED !')


