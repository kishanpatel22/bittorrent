## Peer Wire Protocol 

* The aim of the peer wire protocol is facililate communication between 
  neighboring peers for the purpose of sharing file content.
* PWP is layered on top of TCP and handles all its communication using
  asynchronous messages.

### Working with Peers
* Manage Peer State
    + Choked
    + Interested
* Handle Peer messages
    + Handshake
    + Keep Alive
    + Choke 
    + Unchoke
    + Interested
    + Not Interested
    + Have
    + Bitfield
    + Request
    + Piece

### Communication Messages with the peer 

|Message order |   Client side     |     Message      |    Peer side        |
|--------------|-------------------|------------------|---------------------|
|1             | TCP connection    |      --->        |                     |
|2             |                   |      <---        | TCP connection      |
|3             | Handshake request |      --->        |                     |
|4             |                   |      <---        | Handshake response  |
|5             |                   |      <---        | Bitfields/Have      |
|6             | Interested        |      --->        |                     |
|7             |                   |      <---        | Unchoke/Choke       |
|8             | Request1          |      --->        |                     |
|9             |                   |      <---        | Piece1              |
|10            | Request2          |      --->        |                     |
|11            |                   |      <---        | Piece2              |
|k             | ...               |      --->        |                     |
|k + 1         |                   |      <---        | ...                 |


### Messages send/recieve 

* All the messages to peer need to send asynchronously as mentioned in the BTP,
  However this handled by creating threads for each peer message, however
  multithreading enviornment allocates lot of CPU resources 

* Polling is another method to excecute the tasks asynchronously, in python
  select module helps in polling the requests, and helps to identfy that any
  socket is ready with sending or recieving the data.

* Advantages of polling -
    + polling frees CPU for other works when waiting for sending/recieving data.
    + CPU resources used are less 


## Algorithms are Bittorrent client implements 

### Queuing 
* 

### Piece selection startergy 

* Before requesting the any piece for peer, the client must be unchoked by that
  peer and client must obviously be interested in downloading the piece.
* There are many types of piece selection stratergy some of them are given below
    + **Random first policy** 
        * In this policy random piece which is not downloaded is requested first.
    + **Rarest first policy**
        * In this policy rareset first piece is requested first.
    + **End game policy**
        * get the last remaining pieces.

### Peer selection startergy 

*




