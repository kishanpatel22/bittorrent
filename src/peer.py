import sys
import time
import struct
import hashlib
from threading import *
from copy import deepcopy

# user defined libraries 
from torrent_error import torrent_error
from torrent_logger import *
from peer_wire_messages import *
from shared_file_handler import torrent_shared_file_handler
from peer_socket import *
from peer_state import *

"""
    peer class instance maintains the information about the peer participating
    in the file sharing. The class provides function like handshake, request
    chunk, etc and also keeps track of upload and download speed.
"""
class peer():
    # parameterized constructor does the peer class initialization
    def __init__(self, peer_IP, peer_port, torrent, init_peer_socket = None):
        # peer IP, port and torrent instance
        self.IP         = peer_IP
        self.port       = peer_port
        self.torrent    = deepcopy(torrent)
        
        # initialize the peer_state
        self.state = peer_state()

        # string used for idenfiying the peer
        self.unique_id  = '(' + self.IP + ' : ' + str(self.port) + ')'
        
        # unique peer ID recieved from peer
        self.peer_id = None

        # maximum download block message length 
        self.max_block_length = torrent.block_length
        
        # handshake flag with peer
        self.handshake_flag = False
        
        # bitfield representing which data file pieces peer has
        self.bitfield_pieces = set([])
        
        # peer socket for communication
        self.peer_sock = peer_socket(self.IP, self.port, init_peer_socket)
            
        # file handler used for reading/writing the file file
        self.file_handler = None

        # peer logger object with unique ID 
        logger_name = 'peer' + self.unique_id
        self.peer_logger = torrent_logger(logger_name, PEER_LOG_FILE, DEBUG)
        if torrent.client_request['seeding'] != None:
            self.peer_logger.set_console_logging()

        # response message handler for recieved message
        self.response_handler = { KEEP_ALIVE    : self.recieved_keep_alive,
                                  CHOKE         : self.recieved_choke,
                                  UNCHOKE       : self.recieved_unchoke,
                                  INTERESTED    : self.recieved_interested,
                                  UNINTERESTED  : self.recieved_uninterested,
                                  HAVE          : self.recieved_have, 
                                  BITFIELD      : self.recieved_bitfield,
                                  REQUEST       : self.recieved_request,
                                  PIECE         : self.recieved_piece,
                                  CANCEL        : self.recieved_cancel,
                                  PORT          : self.recieved_port }

        # keep alive timeout : 10 second
        self.keep_alive_timeout = 10
        # keep alive timer
        self.keep_alive_timer = None

    
    """
        initializes the socket for seeding the torrent
    """
    def initialize_seeding(self):
        # first make the socket start seeding
        self.peer_sock.start_seeding()
    
    """
        sets all the bitfield values
    """
    def set_bitfield(self):
        for i in range(self.torrent.pieces_count):
            self.bitfield_pieces.add(i)

    """
        function attempts to recieve any external TCP connection
        returns the connection socket and address if connection 
        if recieved else returns None
    """
    def recieve_connection(self):
        return self.peer_sock.accept_connection()
    
    """
        attempts to connect the peer using TCP connection 
        returns success/failure for the peer connection
    """
    def send_connection(self):
        connection_log = 'SEND CONNECTION STATUS : ' + self.unique_id + ' '
        connection_status = None
        if self.peer_sock.request_connection():
            # user for EXCECUTION LOGGING
            connection_log += SUCCESS
            connection_status = True
        else:
            # user for EXCECUTION LOGGING
            connection_log += FAILURE 
            connection_status = False
         
        self.peer_logger.log(connection_log)
        return connection_status

    """
        disconnects the peer socket connection
    """
    def close_peer_connection(self):
        self.state.set_null()
        self.peer_sock.disconnect()

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
        if not self.peer_sock.send_data(raw_data):
            send_log = self.unique_id +  ' peer connection closed ! ' + FAILURE
            self.peer_logger.log(send_log)
            self.close_peer_connection()

    """
        function helps in sending peer messgae given peer wire message 
        class object as an argument to the function
    """
    def send_message(self, peer_request):
        if self.handshake_flag:
            # used for EXCECUTION LOGGING
            peer_request_log = 'sending message  -----> ' + peer_request.__str__() 
            self.peer_logger.log(peer_request_log)
            # send the message 
            self.send(peer_request.message())

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
        
        # keep alive timer updated 
        self.keep_alive_timer = time.time()
        # return peer wire message object given the three parameters
        return peer_wire_message(message_length, message_id, message_payload)
 
    """
        functions helps in initiating handshake with peer connection
        functions returns success/failure result of handshake 
    """
    def initiate_handshake(self):
        # only do handshake if not earlier and established TCP connection
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
        # if handshake already done then return True
        if self.handshake_flag:
            return True
        # keep alive timer
        self.keep_alive_timer = time.time()
        # check if you recieve any handshake message from the peer
        while not self.check_keep_alive_timeout():
            raw_handshake_response = self.recieve_handshake()
            if raw_handshake_response is not None:
                break
        # case where timeout occured and couldn't recieved message
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
        # peer connection not established
        if not self.peer_sock.peer_connection_active():
            return self.bitfield_pieces
        # recieve only if handshake is done successfully
        if not self.handshake_flag:
            return self.bitfield_pieces
        # loop for all the message that are recieved by the peer
        messages_begin_recieved = True
        while(messages_begin_recieved):
            # handle responses recieved
            response_message = self.handle_response()
            # if you no respone message is recieved 
            if response_message is None: 
                messages_begin_recieved = False
        # returns bitfield obtained by the peer
        return self.bitfield_pieces

    """
        returns the string format information about the handshake process
    """
    def get_handshake_log(self):
        log = 'HANDSHAKE with ' + self.unique_id + ' : '
        if self.handshake_flag:
            log += SUCCESS + '\n'
        else:
            log += FAILURE + '\n'
        peer_bitfield_count = len(self.bitfield_pieces)
        log += 'COUNT BITFIELDs with ' + self.unique_id + ' : '
        if peer_bitfield_count == 0:
            log += 'did not recieved !'
        else:
            log += str(peer_bitfield_count) + ' pieces'
        return log


    """
        function handles any peer message that is recieved on the port
        function manages -> recieving, decoding and reacting to recieved message 
        function returns decoded message if successfully recieved, decoded
        and reacted, else returns None
    """
    def handle_response(self):
        # recieve messages from the peer
        peer_response_message = self.recieve_message()
        # if there is no response from the peer
        if peer_response_message is None:
            return None

        # DECODE the peer wire message into appropriate peer wire message type type
        decoded_message = PEER_MESSAGE_DECODER.decode(peer_response_message)
        if decoded_message is None:
            return None

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
        ======================================================================
                         RECIVED MESSAGES HADNLER FUNCTIONS 
        ======================================================================
    """

    """
        recieved keepalive      : indicates peer is still alive in file sharing
    """
    def recieved_keep_alive(self, keep_alive_message):
         # reset the timer when keep alive is recieved
         self.keep_alive_timer = time.time()

    
    """
        recieved choke          : client is choked by the peer 
                                  peer will not response to clinet requests
    """
    def recieved_choke(self, choke_message):
        # peer is choking the client
        self.state.set_peer_choking()
        # client will also be not interested if peer is choking
        self.state.set_client_not_interested()


    """
        recieved unchoke        : client is unchoked by the peer
                                  peer will respond to client requests
    """
    def recieved_unchoke(self, unchoke_message):
        # the peer is unchoking the client
        self.state.set_peer_unchoking()
        # the peer in also interested in the client
        self.state.set_client_interested()

    """
        recieved interested     : peer is interested in downloading from client 
    """
    def recieved_interested(self, interested_message):
        # the peer is interested in client
        self.state.set_peer_interested()

    """
        recieved uninterested   : peer is not interested in downloading from client
    """
    def recieved_uninterested(self, uninterested_message): 
        # the peer is not interested in client
        self.state.set_peer_not_interested()
        # closing the connection
        self.close_peer_connection()

    """
        recieved bitfields      : peer sends the bitfiled values to client 
                                  after recieving the bitfields make client interested
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
        # extract block requested
        piece_index     = request_message.piece_index
        block_offset    = request_message.block_offset
        block_length    = request_message.block_length
        # validate the block requested exits in file
        if self.torrent.validate_piece_length(piece_index, block_offset, block_length):
            # read the datablock 
            data_block = self.file_handler.read_block(piece_index, block_offset, block_length)
            # create response piece message and send it the peer
            response_message = piece(piece_index, block_offset, data_block)
            self.send_message(response_message)
        else:
            request_log = self.unique_id + ' dropping request since invalid block requested !' 
            self.peer_logger.log(request_log)

    """
        recieved piece          : peer has responed with the piece to client
                                  after recieving any piece, it is written into file
    """
    def recieved_piece(self, piece_message):
        # write the block of piece into the file
        self.file_handler.write_block(piece_message) 
     
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
        ======================================================================
                            SEND MESSAGES HADNLER FUNCTIONS 
        ======================================================================
    """
    
    """
        send keep alive         : client message to keep the peer connection alive
    """
    def send_keep_alive(self):
        self.send_message(keep_alive())

        
    """
        send choke              : peer is choked by the client
                                  client will not response to peer requests
    """
    def send_choke(self):
        self.send_message(choke())
        self.state.set_client_choking()


    """
        send unchoke            : client is unchoked by the peer
                                  peer will respond to client requests
    """
    def send_unchoke(self):
        self.send_message(unchoke())
        self.state.set_client_unchoking()


    """
        send interested         : client is interested in the peer
    """
    def send_interested(self):
        self.send_message(interested())
        self.state.set_client_interested()

    """
        send uninterested       : client is not interested in the peer 
    """
    def send_uninterested(self):
        self.send_message(uninterested())
        self.state.set_client_not_interested()

    """
        send have               : client has the given piece to offer the peer
    """
    def send_have(self, piece_index):
        self.send_message(have(piece_index))
    
    """
        send bitfield           : client sends the bitfield message of pieces
    """
    def send_bitfield(self):
        bitfield_payload = create_bitfield_message(self.bitfield_pieces, self.torrent.pieces_count)
        self.send_message(bitfield(bitfield_payload))
    
    
    """
        send request            : client sends request to the peer for piece
    """
    def send_request(self, piece_index, block_offset, block_length):
        self.send_message(request(piece_index, block_offset, block_length))
    

    """
        send piece              : client sends file's piece data to the peer 
    """
    def send_piece(self, piece_index, block_offset, block_data):
        self.send_message(piece(piece_index, block_offset, block_data))


    """
        downloading finite state machine(FSM) for bittorrent client 
        the below function implements the FSM for downloading piece from peer
    """
    def piece_downlaod_FSM(self, piece_index):
        # if the peer doesn't have the piece
        if not self.have_piece(piece_index):
            return False
        # initializing keep alive timer
        self.keep_alive_timer = time.time()
        # download status of piece
        download_status = False
        # exchanges message with 
        exchange_messages = True
        while exchange_messages:
            # checking for timeouts in states 
            if(self.check_keep_alive_timeout()):
                self.state.set_null()
            # client state 0    : (client = not interested, peer = choking)
            if(self.state == DSTATE0):
                self.send_interested()
            # client state 1    : (client = interested,     peer = choking)
            elif(self.state == DSTATE1):
                response_message = self.handle_response()
            # client state 2    : (client = interested,     peer = not choking)
            elif(self.state == DSTATE2):
                download_status = self.download_piece(piece_index)
                exchange_messages = False
            # client state 3    : (client = None,           peer = None)
            elif(self.state == DSTATE3):
                exchange_messages = False
        return download_status


    """
        function helps in downloading the given piece from the peer
        function returns success/failure depending upon that piece is 
        downloaed successfully and validated successfully
    """
    def download_piece(self, piece_index):
        if not self.have_piece(piece_index) or not self.download_possible():
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
        while self.download_possible() and block_offset < piece_length:
            # find out how much max length of block that can be requested
            if piece_length - block_offset >= self.max_block_length:
                block_length = self.max_block_length
            else:
                block_length = piece_length - block_offset
            
            block_data = self.download_block(piece_index, block_offset, block_length)
            if block_data:
                # increament offset according to size of data block recieved
                recieved_piece += block_data
                block_offset   += block_length
        
        # check for connection timeout
        if self.check_keep_alive_timeout():
            return False
        
        # validate the piece and update the peer downloaded bitfield
        if(not self.validate_piece(recieved_piece, piece_index)):
            return False
        
        # used for EXCECUTION LOGGING
        download_log  = self.unique_id + ' downloaded piece : '
        download_log += str(piece_index) + ' ' + SUCCESS  
        self.peer_logger.log(download_log)
        
        # successfully downloaded and validated piece 
        return True

    
    """
        function helps in downlaoding given block of the piece from peer
        function returns block of data if requested block is successfully 
        downloaded else returns None 
    """
    def download_block(self, piece_index, block_offset, block_length):
        # create a request message for given piece index and block offset
        request_message = request(piece_index, block_offset, block_length)
        # send request message to peer
        self.send_message(request_message)
        
        # torrent statistics starting the timer
        self.torrent.statistics.start_time()
        # recieve response message and handle the response
        response_message = self.handle_response()
        # torrent statistics stopping the timer
        self.torrent.statistics.stop_time()
        
        # if the message recieved was a piece message
        if not response_message or response_message.message_id != PIECE:
            return None
        # validate if correct response is recieved for the piece message
        if not self.validate_request_piece_messages(request_message, response_message):
            return None

        # update the torrent statistics for downloading
        self.torrent.statistics.update_download_rate(piece_index, block_length)

        # successfully downloaded and validated block of piece
        return response_message.block

    """ 
        piece can be only downloaded only upon given conditions
        -> the connection still exits 
        -> handshake done by peer and client successfully
        -> state of client can download the file
        -> timeout has not occured
        function returns true if all above condition are satisfied else false
    """
    def download_possible(self):
        # socket connection still active to recieve/send
        if not self.peer_sock.peer_connection_active():
            return False
        # if peer has not done handshake piece will never be downloaded
        if not self.handshake_flag:
            return False
        # finally check if peer is interested and peer is not choking
        if self.state != DSTATE2:
            return False
        if self.check_keep_alive_timeout():
            return False
        # all conditions satisfied 
        return True

    """
        function returns true or false depending upon peer has piece or not
    """
    def have_piece(self, piece_index):
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
        function validates if correct block was recieved from peer for the request
    """
    def validate_request_piece_messages(self, request, piece):
        if request.piece_index != piece.piece_index:
            return False
        if request.block_offset != piece.block_offset:
            return False
        if request.block_length != len(piece.block):
            return False
        return True

    """
        function validates piece recieved and given the piece index.
        validation is comparing the sha1 hash of the recieved piece 
        with the torrent file pieces value at particular index.
    """
    def validate_piece(self, piece, piece_index):
        # compare the length of the piece recieved
        piece_length = self.torrent.get_piece_length(piece_index)
        if (len(piece) != piece_length):
            # used for EXCECUTION LOGGING
            download_log  = self.unique_id + 'unable to downloaded piece ' 
            download_log += str(piece_index) + ' due to validation failure : ' 
            download_log += 'incorrect lenght ' + str(len(piece)) + ' piece recieved '
            download_log += FAILURE
            self.peer_logger.log(download_log)
            return False

        piece_hash = hashlib.sha1(piece).digest()
        index = piece_index * 20
        torrent_piece_hash = self.torrent.torrent_metadata.pieces[index : index + 20]
        
        # compare the pieces hash with torrent file piece hash
        if piece_hash != torrent_piece_hash:
            # used for EXCECUTION LOGGING
            download_log  = self.unique_id + 'unable to downloaded piece ' 
            download_log += str(piece_index) + ' due to validation failure : ' 
            download_log += 'info hash of piece not matched ' + FAILURE
            self.peer_logger.log(download_log)
            return False
        # return true if valid
        return True
    
    """
        function does initial handshake and immediately sends bitfields to peer
    """
    def initial_seeding_messages(self):
        if not self.respond_handshake():
            return False
        # after handshake immediately send the bitfield response
        bitfield = create_bitfield_message(self.bitfield_pieces, self.torrent.pieces_count)
        self.send_message(bitfield)
        return True
    
    """
        uploading finite state machine(FSM) for bittorrent client (seeding)
        the below function implements the FSM for uploading pieces to peer
    """
    def piece_upload_FSM(self):
        # initializing keep alive timer
        self.keep_alive_timer = time.time()
        # download status of piece
        download_status = False
        # exchanges message with 
        exchange_messages = True
        while exchange_messages:
            # checking for timeouts in states 
            if(self.check_keep_alive_timeout()):
                self.state.set_null()
            # client state 0    : (client = not interested, peer = choking)
            if(self.state == USTATE0):
                response_message = self.handle_response()
            # client state 1    : (client = interested,     peer = choking)
            elif(self.state == USTATE1):
                self.send_unchoke()
            # client state 2    : (client = interested,     peer = not choking)
            elif(self.state == USTATE2):
                self.upload_pieces()
                exchange_messages = False
            # client state 3    : (client = None,           peer = None)
            elif(self.state == USTATE3):
                exchange_messages = False
       
    """
        function helps in uploading the torrent file with peer, the function 
        exchanges the request/piece messages with peer and helps peer get the 
        pieces of the file that client has in the seeding file
    """
    def upload_pieces(self):
        while self.upload_possible():
            # torrent statistics starting the timer
            self.torrent.statistics.start_time()
            # handle all the request messages
            request_message = self.handle_response()
            # torrent statistics starting the timer
            self.torrent.statistics.stop_time()
            if request_message and request_message.message_id == REQUEST:
                piece_index = request_message.piece_index
                block_length = request_message.block_length
                self.torrent.statistics.update_upload_rate(piece_index, block_length)
                self.peer_logger.log(self.torrent.statistics.get_upload_statistics())

    """ 
        piece can be only uploaded only upon given conditions
        -> the connection still exits 
        -> handshake done by client and peer successfully
        -> state of client can download the file
        -> timeout has not occured
        function returns true if all above condition are satisfied else false
    """
    def upload_possible(self):
        # socket connection still active to recieve/send
        if not self.peer_sock.peer_connection_active():
            return False
        # if peer has not done handshake piece will never be downloaded
        if not self.handshake_flag:
            return False
        # finally check if peer is interested and peer is not choking
        if self.state != USTATE2:
            return False
        if self.check_keep_alive_timeout():
            return False
        # all conditions satisfied 
        return True
 
    """
        function checks for timeouts incase of no keep alive recieved from peer
    """
    def check_keep_alive_timeout(self):
        if(time.time() - self.keep_alive_timer >= self.keep_alive_timeout):
            keep_alive_log  = self.unique_id + ' peer keep alive timeout ! ' + FAILURE 
            keep_alive_log += ' disconnecting the peer connection!'
            self.close_peer_connection()
            self.peer_logger.log(keep_alive_log)
            return True
        else:
            return False

