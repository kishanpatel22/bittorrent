import sys
import time
import requests
import bencodepy
import random as rd
import struct
from torrent_error import torrent_error
from socket import *
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
            'port'      : torrent.port,
            'uploaded'  : torrent.uploaded,
            'downloaded': torrent.downloaded,
            'left'      : torrent.left,
            'compact'   : self.compact
        }
       


"""
    Class HTTP torrent tracker helps the client communicate to any HTTP torrent 
    tracker. However the base class containing data of torrent remains the 
    same only way to communicate changes
"""
class http_torrent_tracker(tracker_data):
    
    # contructor : initializes the torrent information
    def __init__(self, torrent, tracker_url):
        super().__init__(torrent)
        self.tracker_url = tracker_url
       

    # attempts to connect to HTTP tracker
    # returns true if conncetion is established false otherwise
    def request_torrent_information(self):
        # try establishing a connection to the tracker
        try:
            # the reponse from HTTP tracker is an bencoded dictionary 
            bencoded_response = requests.get(self.tracker_url, self.request_parameters, timeout=5)
            # decode the bencoded dictionary to python ordered dictionary 
            raw_response_dict = bencodepy.decode(bencoded_response.content)
            # parse the dictionary containing raw data
            self.parse_http_tracker_response(raw_response_dict)
            return True
        except Exception as error_msg:
            # cannont establish a connection with the tracker
            print('Error is : ', error_msg)
            return False


    # extract the important information for the HTTP response dictionary 
    def parse_http_tracker_response(self, raw_response_dict):
        
        # interval : specifies minimum time client show wait for sending next request 
        if b'interval' in raw_response_dict:
            self.interval = raw_response_dict[b'interval']

        # list of peers form the participating the torrent
        if b'peers' in raw_response_dict:
            self.peers_list = []
            # extract the raw peers data 
            raw_peers_data = raw_response_dict[b'peers']
            # create a list of each peer information which is of 6 bytes
            raw_peers_list = [raw_peers_data[i : 6 + i] for i in range(0, len(raw_peers_data), 6)]
            # extract all the peer id, peer IP and peer port
            for raw_peer_data in raw_peers_list:
                # extract the peer IP address 
                peer_IP = ".".join(str(int(a)) for a in raw_peer_data[0:4])
                # extract the peer port number
                peer_port = raw_peer_data[4] * 256 + raw_peer_data[5]
                # append the (peer IP, peer port)
                self.peers_list.append((peer_IP, peer_port))
            
        # number of peers with the entire file aka seeders
        if b'complete' in raw_response_dict:
            self.complete = raw_response_dict[b'complete']

        # number of non-seeder peers, aka "leechers"
        if b'incomplete' in raw_response_dict:
            self.incomplete = raw_response_dict[b'incomplete']
        
        # tracker id must be sent back by the user on announcement
        if b'tracker id' in raw_response_dict:
            self.tracker_id = raw_response_dict[b'tracker id']


    # API function for creating the getting the peer data recivied by HTTP tracker
    def get_peers_data(self):
        peer_data = {'interval' : self.interval, 'peers' : self.peers_list,
                     'leechers' : self.incomplete, 'seeders'  : self.complete}
        return peer_data


    # logs the information obtained by the HTTP tracker 
    def __str__(self):
        logging_info =  'HTTP TRACKER RESPONSE :'                       + '\n'
        logging_info += 'HTTP Tracker URL : ' + self.tracker_url        + '\n'
        logging_info += 'Interval         : ' + str(self.interval)      + '\n'
        logging_info += 'Leechers         : ' + str(self.incomplete)    + '\n'
        logging_info += 'Seeders          : ' + str(self.complete)      + '\n'
        logging_info += 'Peers            : peer IP : peer port' + '\n'
        for peer_IP, peer_port in self.peers_list:
            logging_info += '                 : ' + peer_IP + ' : ' + str(peer_port) + '\n'
        logging_info += '\n'
        return logging_info



"""
    Class UDP torrent tracker helps the client communicate to any UDP torrent 
    tracker. However the base class data of torrent remains the same only way
    to communicate will change. Note that given below class implements the
    UDP Tracker Protcol mentioned at "https://libtorrent.org/udp_tracker_protocol.html"
"""
class udp_torrent_tracker(tracker_data):
    
    # contructor : initializes the torrent information
    def __init__(self, torrent, tracker_url):
        super().__init__(torrent)
        # extract the tracker hostname and tracker port number
        self.tracker_url, self.tracker_port = self.parse_udp_tracker_url(tracker_url)
        
        # connection id : initially a magic number
        self.connection_id = 0x41727101980                       
        # action : initially set to connection request action
        self.action = 0x0                                            
        # transaction id : random id to be set by the client
        self.transaction_id = int(rd.randrange(0, 255))          
        
    
    # parse the UDP tracker URL : the function returns (hostname, port)
    def parse_udp_tracker_url(self, tracker_url):
        domain_url = tracker_url[6:].split(':')
        udp_tracker_url = domain_url[0]
        udp_tracker_port = int(domain_url[1].split('/')[0])
        return (udp_tracker_url, udp_tracker_port)


    # attempts to connect to UDP tracker
    # returns true if conncetion is established false otherwise
    def request_torrent_information(self):

        # create a socket for sending request and recieving responses
        self.tracker_sock = socket(AF_INET, SOCK_DGRAM) 
        self.tracker_sock.settimeout(10)

        # connection payload for UDP tracker connection request
        connection_payload = self.build_connection_payload()
        
        # attempt connecting and announcing the UDP tracker
        try:
            # get the connection id from the connection request 
            self.connection_id = self.udp_connection_request(connection_payload)
            
            # annouce payload for UDP tracker 
            announce_payload = self.build_announce_payload()
            self.raw_announce_reponse = self.udp_announce_request(announce_payload)
            
            # extract the peers IP, peer port from the announce response
            self.parse_udp_tracker_response(self.raw_announce_reponse)
            
            # close the socket once the reponse is obtained
            self.tracker_sock.close()
            
            if self.peers_list and len(self.peers_list) != 0:
                return True
            else:
                return False

        except Exception as error_msg:
            # close the socket if the response is not obtained
            self.tracker_sock.close()
            print('Error is ', error_msg)
            return False
            

    # creates the connection payload for the UDP tracker 
    def build_connection_payload(self):
        req_buffer  = struct.pack("!q", self.connection_id)     # first 8 bytes : connection_id
        req_buffer += struct.pack("!i", self.action)            # next 4 bytes  : action
        req_buffer += struct.pack("!i", self.transaction_id)    # next 4 bytes  : transaction_id
        return req_buffer


    # recieves the connection reponse from the tracker
    def udp_connection_request(self, connection_payload):
        # send the connection payload to the tracker
        self.tracker_sock.sendto(connection_payload, (self.tracker_url, self.tracker_port))
        # recieve the raw connection data
        try:
            raw_connection_data, conn = self.tracker_sock.recvfrom(2048)
        except :
            raise newtork_error('UDP tracker connection request failed')
        
        return self.parse_connection_response(raw_connection_data)


    # extracts the reponse connection id send by UDP tracker
    # function also check if tracker not send appropriate response
    def parse_connection_response(self, raw_connection_data):
        # check if it is less than 16 bytes
        if(len(raw_connection_data) < 16):
            raise newtork_error('UDP tracker wrong reponse length of connection ID !')
        
        # extract the reponse action : first 4 bytes
        response_action = struct.unpack_from("!i", raw_connection_data)[0]       
        # error reponse from tracker 
        if response_action == 0x3:
            error_msg = struct.unpack_from("!s", raw_connection_data, 8)
            raise newtork_error('UDP tracker reponse error : ' + error_msg)
        
        # extract the reponse transaction id : next 4 bytes
        response_transaction_id = struct.unpack_from("!i", raw_connection_data, 4)[0]
        # compare the request and response transaction id
        if(response_transaction_id != self.transaction_id):
            raise newtork_error('UDP tracker wrong response transaction ID !')
        
        # extract the response connection id : next 8 bytes
        reponse_connection_id = struct.unpack_from("!q", raw_connection_data, 8)[0]
        return reponse_connection_id


    # returns the annouce request payload
    def build_announce_payload(self):
        # action = 1 (annouce)
        self.action = 0x1            
        # first 8 bytes connection_id
        announce_payload =  struct.pack("!q", self.connection_id)    
        # next 4 bytes is action
        announce_payload += struct.pack("!i", self.action)  
        # next 4 bytes is transaction id
        announce_payload += struct.pack("!i", self.transaction_id)  
        # next 20 bytes the info hash string of the torrent 
        announce_payload += struct.pack("!20s", self.request_parameters['info_hash'])
        # next 20 bytes the peer_id 
        announce_payload += struct.pack("!20s", self.request_parameters['peer_id'])         
        # next 8 bytes the number of bytes downloaded
        announce_payload += struct.pack("!q", self.request_parameters['downloaded'])
        # next 8 bytes the left bytes
        announce_payload += struct.pack("!q", self.request_parameters['left'])
        # next 8 bytes the number of bytes uploaded 
        announce_payload += struct.pack("!q", self.request_parameters['uploaded']) 
        # event 2 denotes start of downloading
        announce_payload += struct.pack("!i", 0x2) 
        # your IP address, set this to 0 if you want the tracker to use the sender
        announce_payload += struct.pack("!i", 0x0) 
        # some random key
        announce_payload += struct.pack("!i", int(rd.randrange(0, 255)))
        # number of peers require, set this to -1 by defualt
        announce_payload += struct.pack("!i", -1)                   
        # port on which response will be sent 
        announce_payload += struct.pack("!H", self.request_parameters['port'])   
        # extension is by default 0x2 which is request string
        # announce_payload += struct.pack("!H", 0x2)
        return announce_payload


    # recieves the announce reponse from the tracker
    # UDP beign an unreliable protocol the function attemps 
    # some trails for requests the annouce response 
    def udp_announce_request(self, announce_payload):
        trails = 0
        raw_announce_data = None
        while(trails < 8):
            print('announce request to ' + self.tracker_url + ', trail number ' + str(trails))
            # try connection request after some interval of time
            # time.sleep(15 * (2 ** trails))
            try:
                self.tracker_sock.sendto(announce_payload, (self.tracker_url, self.tracker_port))    
                # recieve the raw announce data
                raw_announce_data, conn = self.tracker_sock.recvfrom(2048)
                break
            except Exception as error_msg:
                print('Error is : ', error_msg)
            trails = trails + 1
        return raw_announce_data

    
    # parses the UDP tracker annouce response 
    def parse_udp_tracker_response(self, raw_announce_reponse):
        if(len(raw_announce_reponse) < 20):
            raise newtork_error('Invalid response length in announcing!')
        
        # first 4 bytes is action
        response_action = struct.unpack_from("!i", raw_announce_reponse)[0]     
        # next 4 bytes is transaction id
        response_transaction_id = struct.unpack_from("!i", raw_announce_reponse, 4)[0]
        # compare for the transaction id
        if response_transaction_id != self.transaction_id:
            raise newtork_error('The transaction id in annouce response do not match')
        
        # check if the response contains any error message
        if response_action != 0x1:
            error_msg = struct.unpack_from("!s", raw_announce_reponse, 8)
            raise newtork_error("Error while annoucing: %s" % error_msg)

        offset = 8
        # interval : specifies minimum time client show wait for sending next request 
        self.interval = struct.unpack_from("!i", raw_announce_reponse, offset)[0]
        
        offset = offset + 4
        # leechers : the peers not uploading anything
        self.leechers = struct.unpack_from("!i", raw_announce_reponse, offset)[0] 
        
        offset = offset + 4
        # seeders : the peers uploading the file
        self.seeders = struct.unpack_from("!i", raw_announce_reponse, offset)[0] 
        
        offset = offset + 4
        # obtains the peers list of (peer IP, peer port)
        self.peers_list = []
        while(offset != len(raw_announce_reponse)):
            # first 4 bytes is the peer IP address
            raw_peer_IP = struct.unpack_from("!4s", raw_announce_reponse, offset)[0]
            peer_IP = ".".join(str(a) for a in raw_peer_IP)
            # next 2 bytes is the peer port address
            peer_port = int(struct.unpack_from("!H", raw_announce_reponse, offset + 4)[0])
            # append to IP, port tuple to peer list
            self.peers_list.append((peer_IP, peer_port))
            offset = offset + 6


    # API function for creating the getting the peer data recivied by UDP tracker
    def get_peers_data(self):
        peer_data = {'interval' : self.interval, 'peers'    : self.peers_list,
                     'leechers' : self.leechers, 'seeders'  : self.seeders}
        return peer_data
       
    
    # ensure that socket used for tracker request is closed
    def __exit__(self):
        self.tracker_sock.close()

    
    # logs the information obtained by the HTTP tracker 
    def __str__(self):
        logging_info =  'UDP TRACKER RESPONSE :'                 + '\n'
        logging_info += 'UDP Tracker URL : '+ self.tracker_url   + '\n'
        logging_info += 'Interval        : '+ str(self.interval) + '\n'
        logging_info += 'Leechers        : '+ str(self.leechers) + '\n'
        logging_info += 'Seeders         : '+ str(self.seeders)  + '\n'
        logging_info += 'Peers           : peer IP : peer port'  + '\n'
        for peer_IP, peer_port in self.peers_list:
            logging_info += '                 : ' + peer_IP + ' : ' + str(peer_port) + '\n'
        logging_info += '\n'
        return logging_info



"""
    Torrent tracker class helps then client to connect to any of the trackers
    provided. Note it will identify http or udp trackers and will communicate
    with them accordingly
"""
class torrent_tracker():

    # contructors initializes a torernt tracker connection given 
    # the tracker urls from the torrent metadata file
    def __init__(self, torrent):
        # the responding tracker instance for client
        self.client_tracker = None
        # connection status of the trackers
        self.connection_success         = 1 
        self.connection_failure         = 2
        self.connection_not_attempted   = 3
        
        # get all the trackers list of the torrent data
        self.trackers_list = []
        self.trackers_connection_status = []

        for tracker_url in torrent.torrent_metadata.trackers_url_list:
            # classify HTTP and UDP torrent trackers
            if 'http' in tracker_url[:4]:
                tracker = http_torrent_tracker(torrent, tracker_url)
            if 'udp' in tracker_url[:4]:
                tracker = udp_torrent_tracker(torrent, tracker_url)
            # append the tracker class instance 
            self.trackers_list.append(tracker)
            # append the connection status 
            self.trackers_connection_status.append(self.connection_not_attempted)


    # the torrent tracker requests for the list of peers 
    # Note : function attempts to connect to tracker for given all the tracker
    #        instances and any tracker url reponse is recieved that is retunred
    def request_connection(self):
        # attempts connecting with any of the tracker obtained in the list
        for i, tracker in enumerate(self.trackers_list):
            # check if you can request for torrent information 
            if(tracker.request_torrent_information()):
                self.trackers_connection_status[i] = self.connection_success
                self.client_tracker = tracker
                break
            else:
                self.trackers_connection_status[i] = self.connection_failure
        
        # returns tracker instance for which successful connection was established
        return self.client_tracker

    
    # logs the tracker connections information 
    def __str__(self):
        logging_info =  'TRACKER CONNECTIONS INFORMATION :'               + '\n'
        logging_info += 'Connection Status' + '\t\t\t\t' + 'Trackers URL' + '\n'
        # log all the trackers and corresponding status connection
        for i, status in enumerate(self.trackers_connection_status):
            if(status == self.connection_success):
                logging_info += 'Tracker connection success !'            + '\t\t\t'
            elif(status == self.connection_failure):
                logging_info += 'Tracker connection failure !'            + '\t\t\t'
            else:
                logging_info += 'Tracker connection not attempted !'      + '\t\t'
            logging_info += self.trackers_list[i].tracker_url             + '\n'
        
        logging_info += '\n'
        return logging_info

