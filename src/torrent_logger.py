import logging
import sys

# root directory for log files
TORRENT_LOG_DIR = './torrent_logs/'

# logging file names
TRACKER_LOG         = 'tracker.log'
TORRENT_LOG         = 'torrent_file.log'
PEER_LOG            = 'peer.log'
SWARM_LOG           = 'swarm.log'
SOCKET_LOG          = 'socket.log'
FILE_LOG            = 'file.log'
TORRENT_STATS_LOG   = 'torrent_statistics.log'
BITTORRENT_LOG      = 'bittorrent.log'

# files paths required by the logger
TRACKER_LOG_FILE        = TORRENT_LOG_DIR + TRACKER_LOG
TORRENT_LOG_FILE        = TORRENT_LOG_DIR + TORRENT_LOG
PEER_LOG_FILE           = TORRENT_LOG_DIR + PEER_LOG
SWARM_LOG_FILE          = TORRENT_LOG_DIR + SWARM_LOG
SOCKET_LOG_FILE         = TORRENT_LOG_DIR + SOCKET_LOG
FILE_LOG_FILE           = TORRENT_LOG_DIR + FILE_LOG
TORRENT_STATS_LOG_FILE  = TORRENT_LOG_DIR + TORRENT_STATS_LOG
BITTORRENT_LOG_FILE     = TORRENT_LOG_DIR + BITTORRENT_LOG

# different logging levels provided
DEBUG       = logging.DEBUG
INFO        = logging.INFO
WARNING     = logging.WARNING
ERROR       = logging.ERROR
CRITICAL    = logging.CRITICAL


"""
    The class provides functionality to use different loggers that log 
    the torrent infomation in the file. Note that defualt logging level
    being used is only in DEGUB mode
"""
class torrent_logger():

    # creates a logging object given the logger name, file_name and verbosity level
    def __init__(self, logger_name, file_name, verbosity_level = logging.DEBUG):
        self.logger_name    = logger_name
        self.file_name      = file_name
        self.verbosity_level  = verbosity_level
        
        # clears the pervious contents of the file if any (log lastest info)
        open(self.file_name, "w").close()
        
        # logger object instance
        self.logger = logging.getLogger(self.logger_name)
        
        verbose_string  = '%(threadName)s - '
        verbose_string += '%(levelname)s - '
        verbose_string += '%(name)s \n'
        verbose_string += '%(message)s'
        
        # verbose formatter for logging
        self.verbose_formatter = logging.Formatter(verbose_string)
        
        # file handler for logging into file
        file_handler = logging.FileHandler(self.file_name)
        file_handler.setFormatter(self.verbose_formatter)
        self.logger.addHandler(file_handler)
        
        # set the verbosity level accordingly
        self.logger.setLevel(self.verbosity_level)
    

    # logs adds console hanlder for printing on screen
    def set_console_logging(self):
        # console handler for logging into stdout
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(self.verbose_formatter)
        self.logger.addHandler(console_handler)


    # logs the data into the file stream and standard output console
    def log(self, message):
        message = message + '\n'
        # log according to verbosity level of the object created
        if self.verbosity_level == logging.DEBUG:
            self.logger.debug(message)
        elif self.verbosity_level == logging.INFO:
            self.logger.info(message)
        elif self.verbosity_level == logging.WARNING:
            self.logger.warning(message)
        elif self.verbosity_level == logging.ERROR:
            self.logger.error(message)
        elif self.verbosity_level == logging.CRITICAL:
            self.logger.critical(message)


