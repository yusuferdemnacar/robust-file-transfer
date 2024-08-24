import socket
import logging

# no functional code yet, but a lot of notes

"""

The classes in this file are intended to be independent of whether we have
a client or a server at hand. For a simple server and simple client implementation
ususally only a single socket would exist. For a simple client, one ConnectionHandler
would exist. For a simple server, one ConnectionHandler per client would exist. The
socket is bound to a local ip/port. The connectionhandler stores the remote ip/port.

In contrast:

The connection and stream classes know what file(s) they need to transmit/receive.
And they know whether they are a client or a server. They keep track of some sort of state
machine, decide what commands to send, they read the files from disk, and store the file
to the disk, they generate error frames, etc, etc.
The connection and stream classes can use the queue_frames() function to queue frames
for transmission. And they provide some sort of handle_frame() function so that received
frames can be processed.

I'd draw the line between connection and connection handler at information/functionality
that is independent of server/client logic (connection handler), or info/functionality
that depends on server/client logic (connection).




------------------------------------------------------------
|      connection (N) |    stream  |  stream   | stream    |
------------------------------------------------------------
        v                        ^                      ^
        v queue_frames()         ^ handle_frame()       ^
        v                        ^                      ^ accept connection (server), initiate connection (client),
        v                        ^                      ^ instruct connection to do XY, ...
----------------------------------------------          ^
|     connection handler (N)  |   socket (1)  |         ^            <------ I (Desiree) intend to implement these classes
----------------------------------------------          ^                    The classes are NOT aware of whether they are server/client.
            ^                                           ^                    The classes do NOT care about the content in frames (apart from ack).
            ^                                           ^
            ^ flush(), update(), loop()                 ^            <------ these functions deal with (1) ack/seq/retransmit, (2) packaging, and (3) congestion control
            ^                                           ^
            ^                                           ^
 --------------------------------------------------------------
|           control loop of server/client (1)                  |
 --------------------------------------------------------------
"""

class Socket:

    def __init__(self, local_port=0) -> None:
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        # disabling ipv6only maps any ipv4 addresses to an ipv6 address
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        # TODO: set socket timeout option value to reasonable value
        self.socket.settimeout(10)

        self.socket.bind(("", local_port))

        self.local_address, self.local_port, _, _ = self.socket.getsockname()
        logging.info(f"local address is {self.local_address} at port {self.local_port}")
    
    def loop(self, connections: dict[int, 'ConnectionHandler'], last_updated=None):
        # server and client applications call this function repeatedly
        # (in case of the client the list of connections has probably only one element)
        # TODO not sure yet what parts belong to Socket and what parts belong to client/server application

        if last_updated is not None:
            last_updated.flush()

        timeout, timedout_connection = min([c.retransmit_timeout, c for c in connections])
        rlist, _, _ = select([self.socket], [], [], timeout)

        if len(rlist) == 0:
            # timeout occured!
            timedout_connection.update(None)
            continue

        # 64kib is the maximum ip payload size anyway
        data, addrinfo = self.socket.recvfrom(65536)
        logging.info(addrinfo)

        try:
            packet = parse_data(data)
        except ParseError:
            continue

        if packet.connection_id not in connections:
            # if client, ignore
            # if server, open new connection
            recent = ...
        else:
            recent = connections[packet.connection_id]

        recent.update(packet)


class ConnectionHandler:

    def __init__(self, socket: socket.socket) -> None:
        # underlying socket instance can be shared across multiple connections (in case of server)
        self.socket = socket


        self.connection: Connection = ...

        self.remote_host: str = ...
        self.remote_port: int = ...

        # congestion and flow control is on a per-connection basis

        # acknowledgements are on a per-packet basis
        # connection handler stores remote host and port for generating responses
        pass

    def flush(self):
        # this is the only function that actually causes the transmission of data.
        # returns a float indicating after what amount of time the update() function should be called again

        # send all frames that are currently within the send window of this connection
        # connection has socket attribute
        # connection has remote host and remote port attributes

        # TODO: replay packets that need retransmission. count how many times a packet has been
        # transmitted. Connection dies after a certain amount of retransmissions.
        # TODO: build packets from queued frames and put them into send window queue
        # TODO: look into send window and transmit outstanding data

        pass

    def update(self, data: Packet = None, addrinfo = None) -> float:
        # this function applies updates to the connection/streams from a packets.

        # TODO: update remote ip/port if changed.

        # TODO: get current timestamp and determine if retransmission is outstanding.
        # TODO: if retransmission is necessary, mark the packet for retransmission.

        # TODO: handle global packet header: checksum, ack+seq.
        # TODO: generate an ack packet for this packet.
        # TODO: look for ack number in packet and move send window accordingly.

        # TODO: detect increase/decrease of send window size.

        #  TODO: pass connection-specific frames to Connection object (frames that
        #  have no stream ID)
        #  TODO: pass stream-specific frames to Stream objects (maybe over Connection object?)
        #  Idea is, that connection/stream object can, in turn, use queue_frames()
        #  (or maybe another function of ConnectionHandler that does not exist yet)
        #  to react to whatever was received here. What the reaction to a packet is,
        #  might depend on if it is a server/client.

        pass

    def queue_frames(self):
        # server/client or connection/stream (don't know yet) can use this function
        # to queue frames (e.g. data frames or get frames)

        # TODO: put frames into queue

        pass

    def is_closed(self):
        # returns if this connection is closed
        # connection is closed when
        # transmission is done, or connection timed out, or on irrecoverable error
        # depends on both the state of Connection as well as ConnectionHandler

        pass
