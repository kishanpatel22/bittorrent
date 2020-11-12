import time
from datetime import timedelta

"""
    Torrent statistics included number of pieces downloaded/uploaded. The
    downloading/uploading rate of the torrent file and other information.
    The class provides functionaility to updates the torrent information and
    measure the parameters of downloading/uploading
"""
class torrent_statistics():
    # initialize all the torrent statics information
    def __init__(self, torrent_metadata):
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
        
        self.num_pieces_downloaded  = 0         # blocks/pieces downloaded
        self.num_pieces_uploaded    = 0         # blocks/pieces uplaoded
        self.num_pieces_left        = 0         # blocks/pieces left
        

        # file in bytes to be downloaded
        self.file_size              = torrent_metadata.file_size
        # total pieces in file to be downloaded
        self.total_pieces           = int(len(torrent_metadata.pieces) / 20)
        # percentage of file downloaded by the client 
        self.file_downloading_percentage = 0.0
        # time remaining for complete download 
        self.expected_download_completion_time = 0.0


    def start_time(self):
        self.event_start_time = time.time()
     
    def stop_time(self):
        self.event_end_time = time.time()
    
    def update_start_time(self, time_t):
        self.event_start_time = time_t

    def update_end_time(self, time_t):
        self.event_end_time = time_t

    """
        function updates the statistics after downloading 
        given piece index with given piece size
    """
    def update_download_rate(self, piece_index, piece_size):
        # calculate the time for downloading
        time = (self.event_end_time - self.event_start_time) / 2

        piece_size_kb = piece_size / (2 ** 10)
        self.download_rate = round(piece_size_kb / time, 2)
        
        # update the downloaded piece set
        self.downloaded.add(piece_index)
        # update the num blocks downloaded
        self.num_pieces_downloaded += 1

        # update the avg download rate
        self.total_download_rate += self.download_rate
        self.avg_download_rate = self.total_download_rate / self.num_pieces_downloaded
        self.avg_download_rate = round(self.avg_download_rate , 2)

        # update the max download rate 
        self.max_download_rate = max(self.max_download_rate, self.download_rate)
        
        # file downloading percentage 
        self.file_downloading_percentage = round((len(self.downloaded) * 100)/self.total_pieces, 2)
        # time remaining for complete download 
        time_left = (self.total_pieces - (len(self.downloaded))) * time
        self.expected_download_completion_time = timedelta(seconds=time_left)

    """
        function updates the downloading statistics 
    """
    def update_upload_rate(self, piece_index, piece_size):
        # calculate the time for uploading
        time = (self.event_end_time - self.event_start_time) / 2

        piece_size_kb = piece_size / (2 ** 10)
        self.upload_rate = round(piece_size_kb / time, 2)
        
        # update the num blocks downloaded
        self.num_pieces_uploaded += 1

        # update the avg download rate
        self.total_upload_rate += self.upload_rate
        self.avg_upload_rate = self.total_upload_rate / self.num_pieces_uploaded
        self.avg_upload_rate = round(self.avg_upload_rate, 2)

        # update the max download rate 
        self.max_upload_rate = max(self.max_upload_rate, self.upload_rate)
        
    """
        function returns the download statistics of the torrent file
    """
    def get_download_statistics(self):
        download_log  = 'File downloaded : ' + str(self.file_downloading_percentage) + ' % '
        download_log += '(Average downloading rate : ' + str(self.avg_download_rate) + ' Kbps  '
        download_log += 'Time remaining : ' + str(self.expected_download_completion_time) + ')'
        return download_log
    
    """
        function returns the upload statistics of the torrent file
    """
    def get_upload_statistics(self):
        upload_log  = 'uploaded : [upload rate = ' 
        upload_log += str(self.upload_rate) + ' Kbps'
        upload_log += ', avg uploading rate = '
        upload_log += str(self.avg_upload_rate) + ' Kbps'
        upload_log += ', max uploading rate = ' 
        upload_log += str(self.max_upload_rate) + ' Kbps]'
        return upload_log


