from packet import Packet
from frame import Frame
from common import ConnectionManager

import time


class Connection:

    def __init__(self, connection_manager: ConnectionManager, remote_host: str, remote_port: int) -> None:
        self.connection_manager = connection_manager
        self.remote_host = remote_host
        self.remote_port = remote_port

        # underlying socket instance can be shared across multiple connections (in case of server)
        self.last_flushed = None

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

        self.last_flushed = time.monotonic_ns()

    def update(self, data = None, addrinfo = None) -> float:
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

        # do connection server/client specific stuff:
        self.handle_packet(self)

        pass

    def queue_frame(self, frame: Frame):
        # server/client or connection/stream (don't know yet) can use this function
        # to queue frames (e.g. data frames or get frames)
        
        pass

    def is_closed(self):
        # returns if this connection is closed
        # connection is closed when
        # transmission is done, or connection timed out, or on irrecoverable error
        # depends on both the state of Connection as well as ConnectionHandler

        pass

    def handle_packet(self):
        # to be implemented by server/client
        ...