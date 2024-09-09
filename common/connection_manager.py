from __future__ import annotations
import common

import socket
import logging
import select
import time
import queue

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


class UpdateEvent:
    def __init__(self, conn, packet, addrinfo):
        self.connection: common.Connection = conn
        self.packet: Packet = packet
        self.host: str = addrinfo[0]
        self.port: int = addrinfo[1]


class ConnectionManager:

    def __init__(self, local_port=0) -> None:
        self.socket = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)

        # disabling ipv6only maps any ipv4 addresses to an ipv6 address:
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
        # TODO: set socket timeout option value to reasonable value
        self.socket.settimeout(10)
        self.socket.bind(("", local_port))

        self.local_address, self.local_port, _, _ = self.socket.getsockname()
        logging.info(
            f"local address is {self.local_address} at port {self.local_port}")

        self.connections: dict[int, common.Connection] = {}
        self.last_updated: list[common.Connection] = []

    def add_connection(self, connection: common.Connection):
        if connection.connection_id in self.connections:
            raise Exception(
                "Cannot have two connections with the same ID at once")
        self.last_updated.append(connection)
        self.connections[connection.connection_id] = connection

    def remove_connection(self, connection: common.Connection):
        del self.connections[connection.connection_id]

    def next_connection_id(self):
        return max(self.connections.keys(), default=0) + 1

    def loop(self):

        while True:  # TODO: termination condition

            for con in self.last_updated:
                con.flush()
                self.last_updated.remove(con)

            # timeout, timedout_connection = min([c.retransmit_timeout, c for c in connections])
            current_time = time.time()
            timeout, timedout_connection = min([(c.current_retransmit_timeout(current_time), c) for c in self.connections.values()],
                                               key=lambda tt: tt[0],
                                               default=(None, None))
            logging.info(f"select: {timeout} {timedout_connection}")
            rlist, _, _ = select.select([self.socket], [], [], timeout)

            if len(rlist) == 0:
                # timeout occured!
                timedout_connection.update(None, None)
                self.last_updated.append(timedout_connection)
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

            if connection_id not in self.connections:
                yield UnknownConnectionIDEvent(packet, addrinfo)
            else:
                updateEvent = UpdateEvent(self.connections[connection_id], packet, addrinfo)
                if self.connections[connection_id].remote_host != updateEvent.host:
                    self.connections[connection_id].remote_host = updateEvent.host
                    logging.info(f"Host of connection {connection_id} changed from {self.connections[connection_id].remote_host} to {updateEvent.host}")
                if self.connections[connection_id].remote_port != updateEvent.port:
                    self.connections[connection_id].remote_port = updateEvent.port
                    logging.info(f"Port of connection {connection_id} changed from {self.connections[connection_id].remote_port} to {updateEvent.port}")
                yield updateEvent
                # if the update did not remove the connection, add it to the last_updated list
                if connection_id in self.connections:
                    self.last_updated.append(self.connections[connection_id])
