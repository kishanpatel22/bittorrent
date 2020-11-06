import time

"""
    Torrent statistics included number of pieces downloaded/uploaded. The
    downloading/uploading rate of the torrent file and other information.
    The class provides functionaility to updates the torrent information and
    measure the parameters of downloading/uploading
"""
class torrent_statistics():
    # initialize all the torrent statics information
    def __init__(self):
        self.uploaded               = set([])   # pieces uploaded
        self.downloaded             = set([])   # pieces downloaded
        self.upload_rate            = 0.0       # upload rate   (kbps)
        self.download_rate          = 0.0       # download rate (kbps)
    
        self.max_upload_rate        = 0.0       # max upload rate (kbps)
        self.max_download_rate      = 0.0       # max download rate (kbps)
    
        self.total_upload_rate      = 0.0       # sum upload rate (kbps)
        self.total_download_rate    = 0.0       # sum download rate (kbps)

        self.avg_upload_rate        = 0.0       # avg upload rate (kbps)
        self.avg_download_rate      = 0.0       # avg download rate (kbps)
        
        self.event_start_time       = 0         # start time of event
        self.event_end_time         = 0         # end time of event
        
        self.num_pieces_downloaded  = 0         # pieces downloaded
        self.num_pieces_uploaded    = 0         # pieces uplaoded
        self.num_pieces_left        = 0         # pieces left


    def state_time(self):
        self.event_start_time = time.time()
     
    def stop_time(self):
        self.event_end_time = time.time()
    
    """
        function updates the statistics after downloading 
        given piece index with given piece size
    """
    def update_download_rate(self, piece_index, piece_size):
        # calculate the time for downloading
        time = self.event_end_time - self.event_start_time
        piece_size_kb = piece_size / (2 ** 10)
        self.download_rate = piece_size_kb / time
        
        # update the downloaded piece set
        self.downloaded.add(piece_index)
        
        # update the avg download rate
        self.total_download_rate += self.download_rate
        self.avg_download_rate = self.total_download_rate / len(self.downloaded)
            
        # update the max download rate 
        self.max_download_rate = max(self.max_download_rate, self.download_rate)

    """
        function updates the downloading statistics 
    """
    def update_upload_rate(self, piece_index, piece_size):
        pass

    
    """
        function gets the percentage of the file downloaded 
    """
    def download_percentage(self):
        pass


    def __str__(self):
        torrent_stats_log  = 'TORRENT STATISTICS : \n' 
        torrent_stats_log += 'A) downloaded ' + str(len(self.downloaded)) + ' pieces '
        torrent_stats_log += '[ downloading rate = ' 
        torrent_stats_log += str(round(self.download_rate, 2)) + ' Kbps'
        torrent_stats_log += ', avg downloading rate = ' 
        torrent_stats_log += str(round(self.avg_download_rate, 2)) + ' Kbps'
        torrent_stats_log += ', max downloading rate = ' 
        torrent_stats_log += str(round(self.max_download_rate, 2)) + ' Kbps ]\n'

        torrent_stats_log += 'B) uploading   : [ upload rate = ' 
        torrent_stats_log += str(round(self.upload_rate, 2)) + ' Kbps'
        torrent_stats_log += ', avg uploading rate = '
        torrent_stats_log += str(round(self.avg_upload_rate, 2)) + ' Kbps'
        torrent_stats_log += ', max uploading rate = ' 
        torrent_stats_log += str(round(self.max_upload_rate, 2)) + ' Kbps ]'

        return torrent_stats_log

