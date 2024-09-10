from __future__ import annotations
import common

import socket
import logging
import select
import time
import queue
import random

from packet import Packet

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
    def __init__(self, packet, addrinfo):
        self.packet: Packet = packet
        self.host: str = addrinfo[0]
        self.port: int = addrinfo[1]


class ZeroConnectionIDEvent:
    def __init__(self, packet, addrinfo):
        self.packet: Packet = packet
        self.host: str = addrinfo[0]
        self.port: int = addrinfo[1]

class ConnectionTerminatedEvent:
    def __init__(self, connection):
        self.connection = connection

class ConnectionManager:

    def __init__(self, local_port=0, p = 1, q = 0) -> None:
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        # disabling ipv6only maps any ipv4 addresses to an ipv6 address:
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        self.socket.bind(("", local_port))

        self.local_address, self.local_port, _, _ = self.socket.getsockname()
        logging.info(
            f"local address is {self.local_address} at port {self.local_port}")

        self.connections: dict[int, common.Connection] = {}

        self.p = p
        self.q = q
        self.lastSendSuccessful = True

    def add_connection(self, connection: common.Connection):
        if connection.connection_id in self.connections:
            raise Exception(
                "Cannot have two connections with the same ID at once")
        self.connections[connection.connection_id] = connection

    def remove_connection(self, connection: common.Connection):
        del self.connections[connection.connection_id]

    def next_connection_id(self):
        return max(self.connections.keys(), default=0) + 1

    def loop(self):

        while True:

            for con in self.connections.values():
                if not con.is_closed():
                    con.flush()
                else:
                    yield ConnectionTerminatedEvent(con)
                    del self.connections[con.connection_id]

            # timeout so that retransmissions can be handled
            current_time = time.time()
            timeout, timedout_connection = min(
                filter(
                    lambda tc: tc[0] is not None, # connections without inflight packets don't have a timeout
                    [(c.current_timeout(current_time), c) for c in self.connections.values()]
                ),
                key=lambda tt: tt[0],
                default=(None, None)
            )
            logging.info(f"select: {timeout} {timedout_connection}")
            rlist, _, _ = select.select([self.socket], [], [], timeout)

            if len(rlist) == 0:
                # timeout occured!
                timedout_connection.timed_out(time.time())
                continue

            # 64kib is the maximum ip payload size
            data, addrinfo = self.socket.recvfrom(65536)
            logging.info(addrinfo)

            try:
                packet = Packet.unpack(data)
                connection_id = packet.header.connection_id
            except Exception as e:
                # ignore packets that are not parseable --> read again
                logging.error("Could not parse the packet!")
                logging.error(str(e))
                continue

            logging.info(f"received packet: {packet}")

            # ignore any packet with unknown conn_id as per RFC section 5.1.2
            if connection_id == 0:
                # this event occurs during a handshake on the server side
                yield ZeroConnectionIDEvent(packet, addrinfo)
                continue

            if connection_id not in self.connections:
                # this event occurs during a handshake on the client side
                yield UnknownConnectionIDEvent(packet, addrinfo)
                continue

            # check if the connection is created thruough the event above
            # it may not be as the client may ignore the event
            if connection_id in self.connections:
                logging.info(f"updating connection with id {connection_id}")
                self.connections[connection_id].update(packet, addrinfo)

    def sendto(self, data, address):
        if self.lastSendSuccessful:
            if random.uniform(0, 1) > self.p:
                self.socket.sendto(data, address)
            else:
                self.lastSendSuccessful = False
        else:
            if random.uniform(0, 1) > self.q:
                self.lastSendSuccessful = True
                self.socket.sendto(data, address)
            else:
                pass
        