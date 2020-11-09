"""
    maintains the state of peer participating in uploading / downloading
"""
class peer_state():
    def __init__(self):
        # Initialize the states of the peer 
        self.am_choking         = True              # client choking peer
        self.am_interested      = False             # client interested in peer
        self.peer_choking       = True              # peer choking client
        self.peer_interested    = False             # peer interested in clinet
    
    def set_client_choking(self):
        self.am_choking = True
    def set_client_unchoking(self):
        self.am_choking = False
 
    def set_client_interested(self):
        self.am_interested = True
    def set_client_not_interested(self):
        self.am_interested = False

    def set_peer_choking(self):
        self.peer_choking = True
    def set_peer_unchoking(self):
        self.peer_choking = False

    def set_peer_interested(self):
        self.peer_interested = True
    def set_peer_not_interested(self):
        self.peer_interested = False
    

    def set_null(self):
        self.am_choking         = None
        self.am_interested      = None
        self.peer_choking       = None
        self.peer_interested    = None

    # overaloading == operation for comparsion with states
    def __eq__(self, other): 
        if self.am_choking      != other.am_choking :
            return False
        if self.am_interested   != other.am_interested:
            return False
        if self.peer_choking    != other.peer_choking: 
            return False
        if self.peer_interested != other.peer_interested:
            return False
        return True
    
    # overaloading != operation for comparsion with states
    def  __ne__(self, other):
        return not self.__eq__(other)

    def __str__(self):
        peer_state_log  = '[ client choking : '     + str(self.am_choking)
        peer_state_log += ', client interested : '  + str(self.am_interested) 
        peer_state_log += ', peer choking : '       + str(self.peer_choking)
        peer_state_log += ', peer interested : '    + str(self.peer_interested) + ']'
        return peer_state_log


"""
        Initializing the downloading states for BTP FSM
"""
# initial state     : client = not interested,  peer = choking
DSTATE0 = peer_state()

# client state 1    : client = interested,      peer = choking
DSTATE1 = peer_state()
DSTATE1.am_interested   = True
    
# client state 2    : client = interested,      peer = not choking
DSTATE2 = peer_state()
DSTATE2.am_interested   = True
DSTATE2.peer_choking    = False

# client state 3    : client : None,            peer = None
DSTATE3 = peer_state()
DSTATE3.set_null()

"""
        Initializing the uploading states for BTP FSM
"""
# initial state     : client = choking,         peer = not interested
USTATE0 = peer_state()

# client state 1    : client = choking,         peer = interested
USTATE1 = peer_state()
USTATE1.peer_interested = True
   
# client state 2    : client = not choking,     peer = interested
USTATE2 = peer_state()
USTATE2.peer_interested = True
USTATE2.am_choking = False

# client state 3    : client : None,            peer = None
USTATE3 = peer_state()
USTATE3.set_null()


