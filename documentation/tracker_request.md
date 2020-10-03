## Tracker HTTP/HTTPS Protocol 

* After extracting the URLs of the trackers from the metadata provided in the 
  torrent file next we actualy have to do HTTP request to any one of the tracker 
  such that you could recieve response from the tracker which includes some
  useful information that helps in file download

#### Tracker Request Parameters

* info-hash     : SHA1 hash value from the metadata from torrent file
* peer id       : urlencoded 20 byte string generated as unique client ID. 
* port          : port on which the client is listening 
* uploaded      : the amount of file uploaded by the client
* downloaded    : the amount of file downloaded by the client
* left          : the amount of fie left to be downloaded by the client
* compact       : 
* no peer id    :
* event         : It must be any one from the given below states
    + started   : First request to tracker must include event key with this value
    + stopped   : sent to the tracker if the client is shutting down gracefully
    + completed : Must be sent to the tracker when the download completes 
