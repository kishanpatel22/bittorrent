import time
import struct
import hashlib

# user defined libraries 
from torrent_error import torrent_error
from torrent_logger import *
from peer_wire_messages import *
from shared_file_handler import torrent_shared_file_handler
from peer_socket import *

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
        self.max_message_length = 2 ** 10
        # maximum download block message length (default - 16 KB)
        self.max_block_length = 16 * (2 ** 10)
        
        # handshake flag with peer
        self.handshake_flag = False
        
        # Initialize the states of the peer 
        # Initial state of the peer is choked and not interested
        self.am_choking         = True
        self.am_interested      = False
        self.peer_choking       = True
        self.peer_interested    = False
    
        # bitfield representing which data file pieces peer has
        self.bitfield_pieces = set([])
        
        # peer socket for communication
        self.peer_sock = None
            
        # file handler used for reading/writing the file file
        self.file_handler = None

        # peer logger object with unique ID 
        logger_name = 'peer' + self.unique_id
        self.peer_logger = torrent_logger(logger_name, PEER_LOG_FILE, DEBUG)
        

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
    
    """
        initialize socket of leecher type
    """
    def initialize_leecher(self, psocket = None): 
        self.peer_sock = leecher_socket(self.IP, self.port, psocket)

    """
        initialize socket of seeder type
    """
    def initialize_seeder(self):
        self.peer_sock = seeder_socket(self.IP, self.port)


    """
        function attempts to recieve any external TCP connection
        returns the connection socket and address if connection 
        if recieved else returns None
    """
    def recieve_connection(self):
        connection_log = 'RECIEVE CONNECTION STATUS : ' 
        try:
            connection = self.peer_sock.accept_connection()
            connection_log += SUCCESS
            self.peer_logger.log(connection_log)
            return connection 
        except Exception as err:
            connection_log += FAILURE + ' ' + err.__str__()
            self.peer_logger.log(connection_log)
            return None


    """
        attempts to connect the peer using TCP connection 
        returns success/failure for the peer connection
    """
    def send_connection(self):
        connection_log = 'SEND CONNECTION STATUS : ' + self.unique_id + ' '
        try:
            self.peer_sock.request_connection()
            # user for EXCECUTION LOGGING
            connection_log += SUCCESS
            self.peer_logger.log(connection_log)
            self.peer_connection = True
            return True
        except Exception as err_msg:
            # user for EXCECUTION LOGGING
            connection_log += FAILURE + ' ' + err_msg.__str__()
            self.peer_logger.log(connection_log)
            return False
    
    
    """
        disconnects the peer socket connection
    """
    def disconnect(self):
        self.peer_sock.disconnect()
        self.peer_connection = False

    """
        function helps in recieving data from peers
    """
    def recieve(self, data_size):
        return self.peer_sock.recieve_data(data_size)

    """
        function helps send raw data to the peer connection
        function sends the complete message to peer
    """
    def send(self, raw_data):
        self.peer_sock.send_data(raw_data)
    
    """
        function helps in sending peer messgae given peer wire message 
        class object as an argument to the function
    """
    def send_message(self, peer_request):
        if self.handshake_flag:
            self.peer_sock.send_data(peer_request.message())
            
            # used for EXCECUTION LOGGING
            peer_request_log = 'sending message  -----> ' + peer_request.__str__() 
            self.peer_logger.log(peer_request_log)

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
        if raw_message_length is None or len(raw_message_length) < MESSAGE_LENGTH_SIZE:
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
        message_payload = self.recieve(payload_length)
        if message_payload is None:
            return None
       
        # return peer wire message object given the three parameters
        return peer_wire_message(message_length, message_id, message_payload)
 
    
    """
        functions helps in initiating handshake with peer connection
        functions returns success/failure result of handshake 
    """
    def initiate_handshake(self):
        # only do handshake if not done earlier and connection established with peer
        if not self.handshake_flag and self.send_connection():
            # send handshake message
            handshake_request = self.send_handshake()
            # recieve handshake message
            raw_handshake_response = self.recieve_handshake()
            if raw_handshake_response is None:
                return False
            # validate the hanshake message recieved obtained
            handshake_response = self.handshake_validation(raw_handshake_response)
            if handshake_response is None:
                return False
            # get the client peer id for the handshake response
            self.peer_id = handshake_response.client_peer_id
            self.handshake_flag = True
            # handshake success 
            return True
        # already attempted handshake with the peer
        return False
 

    """
        function helps in responding to incoming handshakes
    """
    def respond_handshake(self):
        if not self.handshake_flag:
            # recieve handshake response 
            raw_handshake_response = self.recieve_handshake()
            if raw_handshake_response is None:
                return False
            # validate the hanshake message response
            handshake_response = self.handshake_validation(raw_handshake_response)
            if handshake_response is None:
                return False 
            # extract the peer id
            self.peer_id = handshake_response.client_peer_id
            # send handshake message after validation 
            self.send_handshake()
            self.handshake_flag = True
            # handshake done successfully
            return True
        # handshake already done
        return False 


    """
        the function helps in building the handshake message
    """
    def build_handshake_message(self):
        info_hash = self.torrent.torrent_metadata.info_hash
        peer_id   = self.torrent.peer_id

        # create a handshake object instance
        return handshake(info_hash, peer_id)
 
    
    """
        function helps in sending the handshake message to the peer
        function returns the handshake request that is made 
    """
    def send_handshake(self):
        # create a handshake object instance for request
        handshake_request = self.build_handshake_message()
        # send the handshake message
        self.send(handshake_request.message())
        
        # used for EXCECUTION LOGGING
        handshake_req_log = 'Handshake initiated -----> ' + self.unique_id
        self.peer_logger.log(handshake_req_log)
        
        # handshake request that is made
        return handshake_request
   

    """
        function helps in recieving the hanshake message from peer
        function returns handshake recieved on success else returns None
    """
    def recieve_handshake(self):
        # recieve message for the peer
        raw_handshake_response = self.recieve(HANDSHAKE_MESSAGE_LENGTH)
        if raw_handshake_response is None:
            # used for EXCECUTION LOGGING
            handshake_res_log = 'Handshake not recived from ' + self.unique_id
            self.peer_logger.log(handshake_res_log)
            return None
        
        # used for EXCECUTION LOGGING
        handshake_res_log = 'Handshake recived   <----- ' + self.unique_id
        self.peer_logger.log(handshake_res_log)
        
        # raw handshake message recieved 
        return raw_handshake_response


    """
        function helps in performing handshake validation of recieved 
        handshake response with the handshake request that is made
    """
    def handshake_validation(self, raw_handshake_response):
        # attempt validation of raw handshake response with handshake request
        validation_log = 'Handshake validation : '
        try:
            handshake_request = self.build_handshake_message()
            handshake_response = handshake_request.validate_handshake(raw_handshake_response)
            validation_log += SUCCESS
            # used for EXCECUTION LOGGING
            self.peer_logger.log(validation_log)
            return handshake_response
        except Exception as err_msg:
            validation_log += FAILURE + ' ' + err_msg.__str__()
            # used for EXCECUTION LOGGING
            self.peer_logger.log(validation_log)
            return None
         

    """
        function helps in initializing the bitfield values obtained from 
        peer note that his function must be immediately be called after 
        the handshake is done successfully. 
        Note : some peer actaully even sends multiple have requests, unchoke,
        have messages in any order that condition is below implementation
    """
    def initialize_bitfield(self):
        # recieve only if handshake is done successfully
        if not self.handshake_flag:
            return None
            
        # loop for all the message that are recieved by the peer
        messages_begin_recieved = True
        while(messages_begin_recieved):
            # handle responses recieved
            response_message = self.handle_response()
            # if you no respone message is recieved 
            if response_message is None: 
                messages_begin_recieved = False

    """
        function handles any peer message that is recieved on the port
        function manages -> recieving, decoding and reacting to recieved message 
        function returns decoded message if successfully recieved, decoded
        and reacted, else returns None
    """
    def handle_response(self):
        # RECIEVE message from peer 
        peer_response_message = self.recieve_message()
        # if there is no response from the peer
        if peer_response_message is None:
            return None

        # DECODE the peer wire message into appropriate peer wire message type type
        decoded_message = PEER_MESSAGE_DECODER.decode(peer_response_message)
        
        # used for EXCECUTION LOGGING
        recieved_message_log = 'recieved message <----- ' + decoded_message.__str__() 
        self.peer_logger.log(recieved_message_log)

        # REACT to the message accordingly
        self.handle_message(decoded_message)
        return decoded_message


    """
        The function is used to handle the decoded message. 
        The function reacts to the message recieved by the peer
    """
    def handle_message(self, decoded_message):
        # select the respective message handler 
        message_handler = self.response_handler[decoded_message.message_id]
        # handle the deocode response message
        return message_handler(decoded_message)


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
                                  after recieving the bitfields make client interested
    """
    def recieved_bitfield(self, bitfield_message):
        # after recieving bitfields make client interested by default
        self.am_interested = True 
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
                                  after recieving any piece, it is written into file
    """
    def recieved_piece(self, piece_message):
        
        # extract the piece index, block offset and data recieved from peer  
        piece_index     = piece_message.piece_index
        block_offset    = piece_message.block_offset
        data_recieved   = piece_message.block
        
        # write the block of piece into the file
        self.file_handler.write_block(piece_index, block_offset, data_recieved) 


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
        function helps in downloading the given piece from the peer note
        whatever piece that you request must be present with the peer
        function returns success/failure depending upon that piece is 
        downloaed sucessfully or not
    """
    def download_piece(self, piece_index):
        # check if peer has the piece index
        if not self.has_piece(piece_index):
            return False
        
        # recieved piece data from the peer
        recieved_piece = b''  

        # block offset for downloading the piece
        block_offset = 0
        # block length 
        block_length = 0
        
        # piece length for torrent 
        piece_length = self.torrent.get_piece_length(piece_index)
        
        # loop untill you download all the blocks in the piece
        while self.can_download() and block_offset < piece_length:
            
            # find out how much max length of block that can be requested
            if piece_length - block_offset >= self.max_block_length:
                block_length = self.max_block_length
            else:
                block_length = piece_length - block_offset
            
            # create a request message for given piece index and block offset
            request_message = request(piece_index, block_offset, block_length)
            # send request message to peer
            self.send_message(request_message)

            # recieve response message 
            response_message = self.handle_response()
            if response_message is None:
                return False

            if response_message.message_id == PIECE:
                # if the message recieved was a piece message
                recieved_piece += response_message.block
                # increament offset according to size of data block recieved
                block_offset += len(response_message.block)
        
        # validate the piece and update the peer downloaded bitfield
        if(self.validate_piece(recieved_piece, piece_index)):
            return True
        else:
            return False


    """ 
        piece can be only downloaded only upon given conditions
        -> handshake done by peer and client successfully
        -> client is interested
        -> peer is not choking client
        function returns true if all above condition are satisfied else false
    """
    def can_download(self):
        # if peer has not done handshake piece will never be downloaded
        if not self.handshake_flag:
            return False

        # if client is not interested then peice will never be downloaded
        if not self.am_interested:
            return False
        
        # if peer is choking the client it will not respond to client requests
        if self.peer_choking:
            interested_request = interested()
             
            # what we can do in this case is send interested request to the peer
            self.send_message(interested_request)
            response_message = self.handle_response()
        
        # finally check if peer is interested and peer is not choking
        if self.am_interested and not self.peer_choking:
            return True
        else:
            return False


    """
        function returns true or false depending upon peer has piece or not
    """
    def has_piece(self, piece_index):
        if piece_index in self.bitfield_pieces:
            return True
        else:
            return False

    """
        function adds file handler abstraction object by which client 
        can read / write block into file which file handler will deal
    """
    def add_file_handler(self, file_handler):
        self.file_handler = file_handler

    """
        function validates piece recieved and given the piece index.
        validation is comparing the sha1 hash of the recieved piece 
        with the torrent file pieces value at particular index.
    """
    def validate_piece(self, piece, piece_index):
        # compare the length of the piece recieved
        piece_length = self.torrent.get_piece_length(piece_index)
        if (len(piece) != piece_length):
            return False

        piece_hash = hashlib.sha1(piece).digest()
        index = piece_index * 20
        torrent_piece_hash = self.torrent.torrent_metadata.pieces[index : index + 20]
        
        # compare the pieces hash with torrent file piece hash
        if piece_hash != torrent_piece_hash:
            self.peer_logger.log("info hash of piece is invalid !")
            return False
        # return true if valid
        return True
    

    """
        function helps in uploading the torrent file with peer
    """
    def upload_file(self):
        # first thing is do handshake
        # send the bitfield information to the client 
        # send unchoke after recieving interested 
        # if everything OK then keep on recieving for requests for pieces
        if not self.respond_handshake() :
            return None
        
        





