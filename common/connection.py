from packet import Packet
from frame import *
from common import (
    Stream,
    ConnectionManager,
)
from abc import abstractmethod
from collections import deque

import time
import logging

class Connection:

    def __init__(
            self,
            connection_manager: ConnectionManager,
            remote_host: str,
            remote_port: int,
            connection_id: int,
        ) -> None:
        self.connection_manager = connection_manager
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.connection_id = connection_id
        self.streams: dict[int, Stream] = {}


        # underlying socket instance can be shared across multiple connections (in case of server)
        self.last_flushed = None

        # congestion and flow control is on a per-connection basis
        # acknowledgements are on a per-packet basis
        # connection handler stores remote host and port for generating responses

        # frames are scheduled using a double-ended queue (also see queue_frame() function)
        self.frame_queue = deque()
        self.next_packet_id = 1

        pass

    def flush(self):
        # this is the only function that actually causes the transmission of data.
        # returns a float indicating after what amount of time the update() function should be called again

        # send all frames that are currently within the send window of this connection
        # connection has socket attribute
        # connection has remote host and remote port attributes

        if len(self.frame_queue) == 0:
            return

        # 1500 - 40 (ipv6) - 8 (udp)
        MTU_SIZE = 1452  # TODO: what value to use here?

        packet_size = 8 # global header
        frames = []
        while True:
            if len(self.frame_queue) == 0:
                break
            frame: Frame = self.frame_queue.pop()
            raw_frame = frame.pack()
            if packet_size + len(raw_frame) > MTU_SIZE:
                self.frame_queue.append(frame)
            else:
                frames.append(frame)
                packet_size = packet_size + len(raw_frame)

        packet_id = self.next_packet_id
        self.next_packet_id += 1
        packet = Packet(Packet.Header(1, self.connection_id, packet_id, 0))

        # TODO: replay packets that need retransmission. count how many times a packet has been
        # transmitted. Connection dies after a certain amount of retransmissions.
        # TODO: build packets from queued frames and put them into send window queue
        # TODO: look into send window and transmit outstanding data

        self.last_flushed = time.monotonic_ns()

    def update(self, packet: Packet, addrinfo) -> float:
        # this function applies updates to the connection/streams from a packets.

        # TODO: update remote ip/port if changed.

        # TODO: get current timestamp and determine if retransmission is outstanding.
        # TODO: if retransmission is necessary, mark the packet for retransmission.

        # TODO: handle global packet header:
            # - version
            # - connectionID
            # - packet checksum
        # TODO: generate an ack packet for this packet.

        # TODO: look for ack number in packet and move send window accordingly.
        # TODO: detect increase/decrease of send window size.


        for frame in packet:
            # TODO: handle some of the control frames here:
            # - ack frame
            # - exit frame
            # - flow control frame (?)
            # - conn id change frame (?)

            # TODO: do connection server/client specific stuff:
            #  Idea is, that connection/stream object can, in turn, use queue_frames()
            #  (or maybe another function of ConnectionHandler that does not exist yet)
            #  to react to whatever was received here. What the reaction to a packet is,
            #  might depend on if it is a server/client.
            self.handle_frame(frame)

        pass

    def queue_frame(self, frame: Frame, transmit_first=None):
        # server/client or connection/stream (don't know yet) can use this function
        # to queue frames (e.g. data frames or read frames)

        # a simple fifo queue doesn't do it: assuming that a lot of data frames are
        # taking up space in the queue, just appending an ack frame at the end of the
        # queue would make the ack be sent out last.

        # thus we in some cases need a very simplistic frame scheduling here.
        # we're doing a queue where we can insert frames at both ends of the queue.
        # appendleft():
        # - inserts at end of queue (will be transmitted last)
        # - keeps order of insertion if called multiple times (like a fifo queue)
        # append():
        # - inserts at front of queue (will be transmitted first)
        # - reverses order of insertion if called multiple times (like a stack)

        if transmit_first is not None:
            if transmit_first:
                self.frame_queue.append(frame)
            else:
                self.frame_queue.appendleft(frame)
        else:
            # heuristically guess what is best based on frame type:
            if isinstance(frame, DataFrame):
                self.frame_queue.appendleft(frame)
            elif isinstance(frame, ReadFrame):
                self.frame_queue.appendleft(frame)
            elif isinstance(frame, ChecksumFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, WriteFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, StatFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, ListFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, ConnectionIDChangeFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, ExitFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, AckFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, FlowControlFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, AnswerFrame):
                self.frame_queue.append(frame)
            elif isinstance(frame, ErrorFrame):
                self.frame_queue.append(frame)
            else:
                # we can still schedule it, but let's print a warning...
                self.frame_queue.append(frame)
                logging.warning(f"Scheduled unknown frame type {frame} for transmission")

    def is_closed(self):
        # returns if this connection is closed
        # connection is closed when
        # transmission is done, or connection timed out, or on irrecoverable error
        # depends on both the state of Connection as well as ConnectionHandler

        pass

    @abstractmethod
    def handle_frame(self, frame: Frame):
        # to be implemented by server/client
        ...