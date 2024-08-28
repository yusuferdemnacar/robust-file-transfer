import socket
import logging
import select
import time
import queue

from common import Connection
from frame import Frame

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
|   Server|ClientConnection |    stream  |  stream   | stream    |
------------------------------------------------------------
        v                        ^                      ^
        v queue_frames()         ^ handle_frame()       ^
        v                        ^                      ^ accept connection (server), initiate connection (client),
        v                        ^                      ^ instruct connection to do XY, ...
----------------------------------------------          ^
|     Connection (N)  |   ConnectionManager (1)  |         ^            <------ I (Desiree) intend to implement these classes
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
"""


class Connection:
    __init__()
    flush()
    update()
    queue_frames()
    handle_frames() <<--- prototype/abstract function


class ServerConnection(Connection):
    __init__() <-- initial received packet
    handle_frames():
        ....
    read_from_disk()

        
class ClientConnection(Connection):
    __init__() <-- list of files
    handle_frames():
    request_stats(...)
    add_file_request(fileIOhandle)
    write_to_disk()





"""



class UnknownConnectionIDEvent:
    def __init__(self, packet, host, port):
        self.packet = packet
        self.port = port
        self.host = host


class ConnectionManager:

    def __init__(self, local_port=0) -> None:
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        # disabling ipv6only maps any ipv4 addresses to an ipv6 address:
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.socket.settimeout(10) # TODO: set socket timeout option value to reasonable value
        self.socket.bind(("", local_port))

        self.local_address, self.local_port, _, _ = self.socket.getsockname()
        logging.info(f"local address is {self.local_address} at port {self.local_port}")

        self.connections: dict[int, Connection] = {}
        self.last_updated: list[Connection | None] = None

    def loop(self, init: Connection | None = None):
        
        if init:
            self.connections[init.connection_id] = Connection(self.socket, init)
            self.last_updated = [init.handler]

        while True: # TODO: termination condition

            for con in self.last_updated:
                con.flush()

            #timeout, timedout_connection = min([c.retransmit_timeout, c for c in connections])
            timeout = None # TODO: timeouts and retransmissions
            rlist, _, _ = select.select([self.socket], [], [], timeout)

            #if len(rlist) == 0:
                # timeout occured!
                #timedout_connection.update(None)
                #continue

            # 64kib is the maximum ip payload size
            data, addrinfo = self.socket.recvfrom(65536)
            logging.info(addrinfo)


            #try:
            #    packet = parse_data(data)
            #except ParseError:
                ##continue

            if packet.connection_id not in self.connections:
                # if client, ignore
                # if server, open new connection
                yield UnknownConnectionIDEvent(packet, addrinfo[0], addrinfo[1])
            else:
                self.last_updated = self.connections[packet.connection_id]
            
            self.last_updated.update(packet)

