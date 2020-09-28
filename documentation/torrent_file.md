## Torrent file

* A torrent file contains a list of files and metadata about the pieces of the
  file. Also the torrent file is bencoded dictionary which is lexicographically 
  sorted.

> annouce : the URL of the tracker
> info : maps to a dictionary whose keys are dependent on whether one or more files are being shared
>   + files : list of dictionaries each corresponding to a file
>   + length : size of the file in bytes
>   + path : string corresponding to the subdirectory names
> length : size of the files in bytes 
> name : name of the file
> piece length : number of bytes per piece (commonly used is 256 KB)
> pieces : a hash list - SHA1 hash of length 20B

