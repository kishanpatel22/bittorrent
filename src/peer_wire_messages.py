import struct

"""
    As per Peer Wire Protocol all the messages exchanged in between 
    any two peers are of format given below 
    
    -----------------------------------------
    | Message Length | Message ID | Payload |
    -----------------------------------------
    
    Message Lenght (4 bytes) : length of message, excluding length part itself. 
    Message ID (1 bytes)     : defines the 9 different types of messages
    Payload                  : variable length stream of bytes

"""

# constants indicating ID's for each message
KEEP_ALIVE      = None
CHOKE           = 0
UNCHOKE         = 1 
INTERESTED      = 2
UNINTERESTED    = 3
HAVE            = 4
BITFIELD        = 5
REQUEST         = 6
PIECE           = 7
CANCEL          = 8
PORT            = 9


# constant handshake message length
HANDSHAKE_MESSAGE_LENGTH = 68

# constants indicating the message sizes in PWM
MESSAGE_LENGTH_SIZE     = 4
MESSAGE_ID_SIZE         = 1



""" class for general peer message exchange in P2P bittorrent """
class peer_wire_message():
    
    # initalizes the attributes of peer wire message
    def __init__(self, message_length, message_id, payload):
        self.message_length = message_length
        self.message_id     = message_id 
        self.payload        = payload

    # returns raw bytes as peer message
    def message(self):
        # pack the message length
        message  = struct.pack("!I", self.message_length)
        # pack the message ID if present in message
        if self.message_id != None:
            message += struct.pack("!B", self.message_id)
        # pack the paylaod is specified 
        if self.payload != None:
            message += self.payload
        return message
    
    # printing the peer wire message
    def __str__(self):
        message_data = 'PEER MESSAGE DATA : '
        message_data += '(message length : ' +  str(self.message_length)   + '), '
        if self.message_id is None:
            message_data += '(message id : None), '
        else:
            message_data += '(message id : ' +  str(self.message_id)       + '), '
        if self.payload is None:
            message_data += '(protocol length : None)'
        else:
            message_data += '(payload length : ' +  str(len(self.payload)) + ')'
        return message_data


""" class for creating handshake messages between the peers """
class handshake():
    # initialize the handshake with the paylaod 
    def __init__(self, info_hash, client_peer_id): 
        # protocol name : BTP 
        self.protocol_name = "BitTorrent protocol"
        # client peer info hash
        self.info_hash = info_hash
        # client peer id 
        self.client_peer_id = client_peer_id


    # creates the handshake payload for peer wire protocol handshake
    def message(self):
        # first bytes the length of protocol name default - 19
        handshake_message  = struct.pack("!B", len(self.protocol_name))
        # protocol name 19 bytes
        handshake_message += struct.pack("!19s", self.protocol_name.encode())
        # next 8 bytes reserved 
        handshake_message += struct.pack("!Q", 0x0)
        # next 20 bytes info hash
        handshake_message += struct.pack("!20s", self.info_hash)
        # next 20 bytes peer id
        handshake_message += struct.pack("!20s", self.client_peer_id)
        # returns the handshake payload
        return handshake_message


    # validate the response handshake with itself
    def validate_handshake(self, response_handshake):
        # compare the handshake length
        response_handshake_length = len(response_handshake)
        if(response_handshake_length != HANDSHAKE_MESSAGE_LENGTH):
            print('recieved invalid handshake length of ' + str(response_handshake_length))
            return None
        
        # extract the info hash of torrent 
        peer_info_hash  = response_handshake[28:48]
        # extract the peer id 
        peer_id         = response_handshake[48:68]

        # check if the info hash is equal 
        if(peer_info_hash != self.info_hash):
            print('recieved info hash of torrent do not match !')
            return None
        # check if peer has got a unique id associated with it
        if(peer_id == self.client_peer_id):
            print('client peer ID and recieved peer ID matches drop the peer!')
            return None

        # succesfully validating returns the handshake response
        return handshake(peer_info_hash, peer_id)


""" 
    This message is send to remote peer to indicate that 
    it is still alive and participating in file sharing.
"""
class keep_alive(peer_wire_message):
    def __init__(self):   
        message_length  = 0                                 # 4 bytes message length
        message_id      = KEEP_ALIVE                        # no message ID
        payload         = None                              # no payload
        super().__init__(message_length, message_id, payload)


""" This message is send to remote peer informing 
     remote peer is begin choked 
"""
class choke(peer_wire_message):
    def __init__(self):   
        message_length = 1                                  # 4 bytes message length
        message_id     = CHOKE                              # 1 byte message ID
        payload        = None                               # no payload
        super().__init__(message_length, message_id, payload)


""" This message is send to remote peer informing 
    remote peer is no longer being choked
"""
class unchoke(peer_wire_message):
    def __init__(self):   
        message_length = 1                                  # 4 bytes message length
        message_id     = UNCHOKE                            # 1 byte message ID
        payload        = None                               # no payload
        super().__init__(message_length, message_id, payload)


"""
    This message is send to remote peer informing 
    remote peer its desire to request data
"""
class interested(peer_wire_message):
    def __init__(self):   
        message_length = 1                                  # 4 bytes message length
        message_id     = INTERESTED                         # 1 byte message ID
        payload        = None                               # no payload
        super().__init__(message_length, message_id, payload)


"""
    This message is send to remote peer informing remote
    peer it's not interested in any pieces from it
"""
class uninterested(peer_wire_message):
    def __init__(self):   
        message_length = 1                                  # 4 bytes message length
        message_id     = UNINTERESTED                       # 1 byte message ID
        payload        = None                               # no payload
        super().__init__(message_length, message_id, payload)



""" 
    This message tells the remote peers what pieces 
    does the client peer has succesfully downloaded
"""
class have(peer_wire_message):
    # initializes the message with given paylaod
    def __init__(self, piece_index):   
        message_length = 5                                  # 4 bytes message length
        message_id     = HAVE                               # 1 byte message ID
        payload        = struct.pack("!I", piece_index)     # 4 bytes payload
        super().__init__(message_length, message_id, payload)



"""
    This message must be send immediately after handshake, telling the client
    peer what peicies does the remote peer has. However the client peer may 
    avoid replying this message in case if doesn't have any pieces downloaded
"""
class bitfield(peer_wire_message):
    # initialize the message with pieces information
    def __init__(self, pieces_info):
        message_length  = 1 + len(pieces_info)              # 4 bytes message length
        message_id      = BITFIELD                          # 1 byte message id
        payload         = pieces_info                       # variable length payload
        super().__init__(message_length, message_id, payload)
   

    # extract downloaded pieces from bitfield send by peer 
    def extract_pieces(self):
        bitfield_pieces = set([])
        # for every bytes value in payload check for its bits
        for i, byte_value in enumerate(self.payload):
            for j in range(8):
                # check if jth bit is set
                if((byte_value >> j) & 1):
                    piece_number = i * 8 + 7 - j
                    bitfield_pieces.add(piece_number)
        # return the extracted bitfield pieces
        return bitfield_pieces


"""
    This message is send inorder to request a piece of block for the remote peer
    The payload is defined as given below 
    | Piece Index(4 bytes) | Block Offset(4 bytes) | Block Length(4 bytes) |
"""
class request(peer_wire_message):
    def __init__(self, piece_index, block_offset, block_length):
        message_length  = 13                                # 4 bytes message length
        message_id      = REQUEST                           # 1 byte message id
        payload         = struct.pack("!I", piece_index)    # 12 bytes payload
        payload        += struct.pack("!I", block_offset) 
        payload        += struct.pack("!I", block_length) 
        super().__init__(message_length, message_id, payload)



"""
    This message is used to exchange the data among the peers. The payload for
    the message as given below
    | index(index of piece) | begin(offest within piece) | block(actual data) |
"""
class piece(peer_wire_message):
    def __init__(self, index, begin_offset, block):
        message_length  = 9 + len(piece_info)               # 4 bytes message length
        message_id      = PIECE                             # 1 byte message id
        payload         = struct.pack("!I", index)          # variable length payload
        payload        += struct.pack("!I", begin_offset)
        payload        += block
        super().__init__(message_length, message_id, payload)


