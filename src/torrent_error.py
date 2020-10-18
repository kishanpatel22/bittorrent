# unicode characters for success/failure indication
SUCCESS = u"\u2705"
FAILURE = u"\u274C"

"""
    The user defined class helps in raising user defined expection
    occuring during bittorent client transmission and reception
"""
class torrent_error(RuntimeError): 
    
    def __init__(self, error_msg): 
        self.error_msg = error_msg

    def __str__(self):
        return str(self.error_msg)
