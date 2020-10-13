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

### Communication with the peer 

|Message order |   Client side     |     Message      |    Peer side        |
|--------------|-------------------|------------------|---------------------|
|1             | TCP connection    |      <-->        | TCP connection      |
|2             | Handshake request |      --->        |                     |
|3             |                   |      <---        | Handshake response  |





