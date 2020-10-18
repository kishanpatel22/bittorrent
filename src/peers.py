import time
import struct
from torrent_error import *
from torrent_logger import *
from peer_wire_messages import *
from socket import *


"""
    peer class instance maintains the information about the peer participating
    in the file sharing. The class provides function like handshake, request
    chunk, etc and also keeps track of upload and download speed.
"""
class peer():
    # parameterized constructor does the peer class initialization
    def __init__(self, peer_IP, peer_port, torrent):
        # peer IP, port and torrent instance
        self.IP         = peer_IP
        self.port       = peer_port
        self.torrent    = torrent
        
        # string used for idenfiying the peer
        self.unique_id  = '(' + self.IP + ' : ' + str(self.port) + ')'
        
        # peer connection
        self.peer_connection = False

        # unique peer ID recieved from peer
        self.peer_id = None

        # maximum message length
        self.max_message_length = 1024

        # handshake flag with peer
        self.handshake_flag = False
        
        # keep track of upload and download speed
        self.upload_speed   = None
        self.download_speed = None
        
        # Initialize the states of the peer 
        # Initial state of the peer is choked and not interested
        self.am_choking         = True
        self.am_interested      = False
        self.peer_choking       = True
        self.peer_interested    = False
    
        # bitfield representing which data file pieces peer has
        self.bitfield_pieces = set([])

        # initializing a peer socket for TCP communiction 
        self.peer_sock = socket(AF_INET, SOCK_STREAM)
        self.peer_sock.settimeout(8)
        
        # peer logger object with unique ID 
        self.peer_logger = torrent_logger(self.unique_id, PEER_LOG_FILE, DEBUG)
        

        # response message handler for recieved message
        self.response_handler = { KEEP_ALIVE    : self.recieved_keep_alive,
                                  CHOKE         : self.recieved_choke,
                                  UNCHOKE       : self.recieved_unchoke,
                                  INTERESTED    : self.recieved_interested,
                                  UNINTERESTED  : self.recieved_uninterested,
                                  HAVE          : self.recieved_have, 
                                  BITFIELD      : self.recieved_bitfield,
                                  PIECE         : self.recieved_piece,
                                  CANCEL        : self.recieved_cancel,
                                  PORT          : self.recieved_port }
    


    # attempts to connect the peer using TCP connection 
    # returns success/failure for connection
    def connect(self):
        try:
            self.peer_sock.connect((self.IP, self.port))
            return True
        except Exception as err_msg:
            err_log = '\t' + self.unique_id + ' error : ' + err_msg.__str__()
            self.peer_logger.log(err_log)
            return False

    """
        function helps in work of recieving data from peers
        function returns raw data if recieved from peer else returns None
    """
    def recieve(self, data_size):
        # attempt to recieve the message length from message
        try:
            peer_raw_data = self.peer_sock.recv(data_size)
        except:
            return None
        return peer_raw_data 
    
    """
        function helps sends raw data to the peer connection
    """
    def send(self, raw_data):
        self.peer_sock.send(raw_data)
     

    """
        function helps in sending peer messgae given peer wire message 
        class object as an argument to the function
    """
    def send_message(self, peer_request):
        if self.handshake_flag:
            self.peer_sock.send(peer_request.message())

    """
        functions helpes in recieving peer wire protocol messages. Note that 
        function uses low level function to recieve data and creates peer
        wire message class object as return value is no had no error and also
        only one message is recieved by the given function at any time.
    """
    def recieve_message(self):
        # extract the peer wire message information by receiving chunks of data
        
        # recieve the message length 
        raw_message_length = self.recieve(MESSAGE_LENGTH_SIZE)
        if raw_message_length is None or raw_message_length == 0:
            return None

        # unpack the message length which is 4 bytes long
        message_length = struct.unpack_from("!I", raw_message_length)[0]
        # keep alive messages have no message ID and payload
        if message_length == 0:
            return peer_wire_message(message_length, None, None)

        # attempt to recieve the message ID from message
        raw_message_ID =  self.recieve(MESSAGE_ID_SIZE)
        if raw_message_ID is None:
            return None
       
        # unpack the message length which is 4 bytes long
        message_id  = struct.unpack_from("!B", raw_message_ID)[0]
        # messages having no payload 
        if message_length == 1:
            return peer_wire_message(message_length, message_id, None)
       
        # extract all the payload
        payload_length = message_length - 1
        
        # extract the message payload 
        message_payload = b''
        while(payload_length != 0):
            recieved_payload = self.recieve(payload_length)
            if recieved_payload is None:
                return None
            message_payload += recieved_payload
            payload_length = payload_length - len(recieved_payload)

        # return peer wire message object given the three parameters
        return peer_wire_message(message_length, message_id, message_payload)
 

    """
        functions helps in doing a handshake with peer connection
        functions returns success/failure result of handshake 
    """
    def handshake(self):
        # only do handshake if not done earlier and connection established with peer
        if not self.handshake_flag and self.connect():
            info_hash = self.torrent.torrent_metadata.info_hash
            peer_id   = self.torrent.peer_id

            # create a handshake object instance for request
            handshake_request = handshake(info_hash, peer_id)
            # send the handshake message
            self.send(handshake_request.message())
            
            # used for EXCECUTION LOGGING
            handshake_req_log = 'Handshake initiated -----> ' + self.unique_id
            self.peer_logger.log('\t' + handshake_req_log + '\n')

            # recieve message for the peer
            raw_handshake_response = self.recieve(HANDSHAKE_MESSAGE_LENGTH)
            if raw_handshake_response is None:
                # used for EXCECUTION LOGGING
                handshake_res_log = 'Handshake not recived from ' + self.unique_id
                self.peer_logger.log('\t' + handshake_res_log + '\n')
                return False
            
            # used for EXCECUTION LOGGING
            handshake_res_log = 'Handshake recived   <----- ' + self.unique_id
            self.peer_logger.log('\t' + handshake_res_log + '\n')
            
            # attempt validation of raw handshake response with handshake request
            validation_log = 'Handshake validation : '
            try:
                handshake_response = handshake_request.validate_handshake(raw_handshake_response)
                validation_log += SUCCESS
                # used for EXCECUTION LOGGING
                self.peer_logger.log('\t' + validation_log + '\n')
            except Exception as err_msg:
                validation_log += FAILURE + ' ' + err_msg.__str__()
                # used for EXCECUTION LOGGING
                self.peer_logger.log('\t' + validation_log + '\n')
                return False
            
            # get the client peer id for the handshake response
            self.peer_id = handshake_response.client_peer_id
            self.handshake_flag = True
            
            # handshake success 
            return True
        
        # already attempted handshake with the peer
        return False
       

    """
        The function helps in initializing the bitfield values obtained 
        from peer note that his function must be immediately be called 
        after the handshake is done successfully. 
        Note : some peer actaully even sends multiple have requests, unchoke 
        message in any order that condition is also handled currently
    """
    def initialize_bitfield(self):
        # recieve only if handshake is done successfully
        if not self.handshake_flag:
            return None
            
        # loop for all the message that are recieved by the peer
        messages_begin_recieved = True
        while(messages_begin_recieved):
            peer_response_message = self.recieve_message()

            # if there is no response from the peer
            if peer_response_message is None:
                messages_begin_recieved = False
                continue

            # deocde the bitfield message response
            decoded_message = PEER_MESSAGE_DECODER.decode(peer_response_message)
            
            # used for EXCECUTION LOGGING
            recieved_message_log = 'recieved message <----- ' + decoded_message.__str__() 
            self.peer_logger.log('\t' + recieved_message_log + '\n')

            # react to the message accordingly
            self.handle_message(decoded_message)


    """
        The function is used to handle the decoded message. 
        The function reacts to the message recieved by the peer
    """
    def handle_message(self, decoded_message):
        # select the respective message handler 
        message_handler = self.response_handler[decoded_message.message_id]
        # handle the deocode response message
        message_handler(decoded_message)



    """
        recieved keepalive      : indicates peer is still alive in file sharing
    """
    def recieved_keep_alive(self, keep_alive_message):
        # informs that peer is alive
        self.peer_connection = True


    """
        recieved choke          : client is choked by the peer 
                                  peer will not response to clinet requests
    """
    def recieved_choke(self, choke_message):
        # the peer is choking the client
        self.peer_choking = True


    """
        recieved unchoke        : client is unchoked by the peer
                                  peer will respond to client requests
    """
    def recieved_unchoke(self, unchoke_message):
        # the peer is unchoking the client
        self.peer_choking = False
        # sending it interested message for requesting pieces in future
        self.send_message(interested())
        # indicate that you are interested in peer
        self.am_interested = True


    """
        recieved interested     : peer is interested in downloading from client 
    """
    def recieved_interested(self, interested_message):
        # the peer is interested in client
        self.peer_interested = True
        # TODO : send the peer what you have


    """
        recieved uninterested   : peer is not interested in downloading from client
    """
    def recieved_uninterested(self, uninterested_message): 
        # the peer is not interested in client
        self.peer_interested = False
        # TODO : can simply ignore ?


    """
        recieved bitfields      : peer sends the bitfiled values to client 
    """
    def recieved_bitfield(self, bitfield_message):
        # extract the bitfield piece information from the message
        self.bitfield_pieces = bitfield_message.extract_pieces()


    """
        recieved have           : peer sends information of piece that it has
    """
    def recieved_have(self, have_message):
        # update the piece information in the peer bitfiled 
        self.bitfield_pieces.add(have_message.piece_index) 
    
        
    """
        recieved request        : peer has requested some piece from client
    """
    def recieved_request(self, request_message):
        # TODO : return the bitfield available to the peer
        pass


    """
        recieved piece          : peer has responed with the piece to client
    """
    def recieved_piece(self, piece_message):
        # TODO : write in the file 
        print(piece_message.payload)


    """ 
        recieved cancel         : message to cancel a block request from client
    """
    def recieved_cancel(self, cancel_message):
        # TODO : implementation coming soon
        pass

    """ 
        recieved port           : 
    """
    def recieved_port(self, cancel_message):
        # TODO : implementation coming soon
        pass






"""
    Implementation of Peer Wire Protocol as mentioned in RFC of BTP/1.0
    PWP will help in contacting the list of peers requesting them chucks 
    of file data. The peer class implements various algorithms like piece
    downloading stratergy, chocking and unchocking the peers, etc.
"""
class peers():

    def __init__(self, peers_data, torrent):
        # initialize the peers class with peer data recieved
        self.interval   = peers_data['interval']
        self.seeders    = peers_data['seeders']
        self.leechers   = peers_data['leechers']
            
        # create a peer instance for all the peers recieved 
        self.peers_list = []
        for peer_IP, peer_port in peers_data['peers']:
            self.peers_list.append(peer(peer_IP, peer_port, torrent))
        
        # bitfields from all the peers
        self.bitfield_pieces_count = dict()

        # peers logger object
        self.peers_logger = torrent_logger('peers', PEERS_LOG_FILE, DEBUG)


    """
        performs handshakes with all the peers 
    """
    def handshakes(self):
        for peer in self.peers_list[:1]:
            handshake_log = 'HANDSHAKE EVENT : ' + peer.unique_id
            if(peer.handshake()):
                handshake_log += SUCCESS
            else:
                handshake_log += FAILURE
            # used for EXCECUTION LOGGING
            self.peers_logger.log('\t' + handshake_log + '\n')


    """
        recieves the bifields from all the peers
        Note bitfield is send immediately after handshake response
    """
    def initialize_bitfields(self):
        # recieved bitfields from given set of peers
        for peer in self.peers_list[:1]:
            # recieve only from handshaked peers
            if(peer.handshake_flag):
                # used for EXCECUTION LOGGING
                init_bitfield_log = 'INIT BITFIELD EVENT : ' + peer.unique_id
                self.peers_logger.log('\t' + init_bitfield_log + '\n')

                # initialize the bitfields obtained from peers
                peer.initialize_bitfield()
                self.update_bitfield_count(peer.bitfield_pieces)
               
    """     
        Updates the bitfield values obtained from the peers
    """
    def update_bitfield_count(self, bitfield_pieces):
        for piece in bitfield_pieces:
            if piece in self.bitfield_pieces_count.keys():
                self.bitfield_pieces_count[piece] += 1
            else:
                self.bitfield_pieces_count[piece] = 1

    """ 
        The main event loop for the downloading the torrrent file
    """
    def event_loop(self):
        pass





