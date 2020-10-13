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

""" class for general peer message exchange in P2P bittorrent """
class peer_wire_message():
    
    # initalizes the attributes of peer wire message
    def __init__(self, message_length, message_id, payload):
        self.message_length = message_length
        self.message_id     = message_id 
        self.payload        = payload

    # returns raw bytes as peer message
    def message(self):
        message  = struct.pack("!I", self.message_length)
        message += struct.pack("!B", self.message_id)
        if self.payload != None:
            message += self.payload
        return message


""" class for creating handshake messages between the peers """
class handshake():
    def __init__(self): 
        # protocol name : BTP 
        self.protocol_name = "BitTorrent protocol"

    # creates the handshake payload for peer wire protocol handshake
    def message(self, info_hash, client_peer_id):
        # first bytes the length of protocol name default - 19
        handshake_message  = struct.pack("!B", len(self.protocol_name))
        # protocol name 19 bytes
        handshake_message += struct.pack("!19s", self.protocol_name.encode())
        # next 8 bytes reserved 
        handshake_message += struct.pack("!Q", 0x0)
        # next 20 bytes info hash
        handshake_message += struct.pack("!20s", info_hash)
        # next 20 bytes peer id
        handshake_message += struct.pack("!20s", client_peer_id)
        # returns the handshake payload
        return handshake_message


""" This message is send to remote peer informing 
     remote peer is begin choked 
"""
class choke(peer_wire_message):
    def __init__(self):   
        message_length = 1                              # 4 bytes message length
        message_id     = 0                              # 1 byte message ID
        payload        = None                           # no payload
        super().__init__(message_length, message_id, payload)


""" This message is send to remote peer informing 
    remote peer is no longer being choked
"""
class unchoke(peer_wire_message):
    def __init__(self):   
        message_length = 1                              # 4 bytes message length
        message_id     = 1                              # 1 byte message ID
        payload        = None                           # no payload
        super().__init__(message_length, message_id, payload)


"""
    This message is send to remote peer informing 
    remote peer its desire to request data
"""
class interested(peer_wire_message):
    def __init__(self):   
        message_length = 1                              # 4 bytes message length
        message_id     = 2                              # 1 byte message ID
        payload        = None                           # no payload
        super().__init__(message_length, message_id, payload)


"""
    This message is send to remote peer informing remote
    peer it's not interested in any pieces from it
"""
class uninterested(peer_wire_message):
    def __init__(self):   
        message_length = 1                              # 4 bytes message length
        message_id     = 3                              # 1 byte message ID
        payload        = None                           # no payload
        super().__init__(message_length, message_id, payload)


""" 
    This message tells the remote peers what pieces 
    does the client peer has succesfully downloaded
"""
class have(peer_wire_message):
    # initializes the message with given paylaod
    def __init__(self, piece_index):   
        message_length = 5                              # 4 bytes message length
        message_id     = 4                              # 1 byte message ID
        payload        = struct.pack("!I", piece_index) # 4 bytes payload
        super.__init__(message_length, message_id, payload)






# TODO : implementation left
"""
    This message must be send immediately after handshake, telling the remote
    peer what peicies does the clinet peer has. However the client peer may 
    avoid replying this message in case if doesn't have any pieces downloaded
"""
class bitfield():
    # Message length : var | Message ID(1 byte) : 5 | paylaod : variable length

    # Note that piece_index is the payload length of 4 bytes 
    def message(self, piece_index):
        self.message_id = 5
        message  = struct.pack("!I", len(piece_index) + 1)
        message += struct.pack("!B", self.message_id)
        return message


class request():
    # Message length(4 bytes): 13 | Message ID(1 byte): 6 | paylaod(12 bytes): 3 integers

    # payload can be described as given below 
    # | Piece Index(4 bytes) | Block Offset(4 bytes) | Block Length(4 bytes) |
    
    def message(self, piece_index, block_offset, block_length):
        self.message_id = 6
        message  = struct.pack("!I", 13) 
        message += struct.pack("!B", self.message_id)
        message += struct.pack("!I", piece_index)
        message += struct.pack("!I", block_offset)
        message += struct.pack("!I", block_length)
        return message


class piece():
    # Message length(4 bytes): 9 | Message ID(1 byte): 7 | paylaod(8 bytes): 2 integers
    
    def message(self, piece_index, block_offset, block_length):
        self.message_id = 7
        return message



