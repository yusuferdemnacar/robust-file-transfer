from __future__ import annotations
import common

from packet import Packet
from frame import *
from abc import abstractmethod
from collections import deque

import time
import logging
import random


class Connection:

    def __init__(
        self,
        connection_manager: common.ConnectionManager,
        remote_host: str,
        remote_port: int,
        connection_id: int,
    ) -> None:
        self.connection_manager = connection_manager
        self.remote_host = remote_host
        self.remote_port = remote_port
        self.connection_id = connection_id
        self.streams: dict[int, common.Stream] = {}
        self.retransmit_timeout = 5  # seconds
        self.connection_timeout = 5 * 60  # seconds
        self.last_updated = time.time()

        self.closed = False

        # small optimization s.t. flush() does not check every single inflight packet every single time
        self.retransmit_timeout_triggered = False

        # congestion and flow control is on a per-connection basis
        # acknowledgements are on a per-packet basis
        # connection handler stores remote host and port for generating responses

        # frames are scheduled using a double-ended queue (also see queue_frame() function)
        self.frame_queue = deque()

        # start out with 32 max-sized packets, usually the receive buffer for sockets under linux can hold that amount
        self.max_packet_size = 1500 - 40 - 8  # TODO do MTU discovery?
        self.max_inflight_bytes = self.max_packet_size
        self.is_slowstart = True
        self.slowstart_threshold = None

        # send windowing
        self.last_sent_packet_id = 0
        self.next_recv_packet_id = 1  # will be initialized upon receiving the first packet
        self.inflight_packets: deque[tuple[float, Packet]] = deque()  # packet cache for retransmissions, queue is ordered by timestamps
        self.inflight_bytes = 0   # should always match with packets in self.inflight_packets !

    def flush(self):
        """
        This is the only function that actually causes the transmission of data.
        It builds as many packets as possible from the frame queue without exceeding the send
        window (max_inflight_bytes) of this connection.
        """

        # (1) TODO: replay packets that need retransmission. count how many times a packet has been
        # transmitted. Connection dies after a certain amount of retransmissions.
        # (2) TODO: setting checksum (and ACK number) in packet objects
        # (3) TODO: packet_id is probably also increased in empty packets
        
        logging.info(f"flush() inflight_packet = {len(self.inflight_packets)}")

        if self.retransmit_timeout_triggered:
            current_time = time.time()
            no_ack_expected = []
            retransmitted = []
            for tp in self.inflight_packets:
                timestamp, packet = tp
                if current_time > timestamp + self.retransmit_timeout:
                    logging.info(f"retransmitting packet: {packet}")
                    # if the packet contained at least one frame other than AckFrame or an ExitFrame send a retransmit
                    if next((frame for frame in packet.frames if
                            (type(frame) != AckFrame) and
                            (type(frame) != ExitFrame)
                            ), None):
                        logging.info("retransmitting ack eliciting packet")
                        retransmitted.append(tp)
                        self.connection_manager.sendto(packet.pack(), (self.remote_host, self.remote_port))
                    else:
                        logging.info("no ack expected for retransmitted packet")
                        no_ack_expected.append(tp)
            for tp in no_ack_expected:
                _, packet = tp
                self.inflight_packets.remove(tp)
                self.inflight_bytes -= len(packet.pack())
            for tp in retransmitted:
                timestamp, packet = tp
                self.inflight_packets.remove(tp)
                self.inflight_packets.appendleft((current_time, packet))
            self.retransmit_timeout_triggered = False

        # max_flush_bytes is the amount of bytes that we are allowed to send out according to the current send window:
        if not self.connection_id and len(self.inflight_packets) == 1:
            # in this case we cannot have more than one inflight packet
            max_flush_bytes = 0
        else:
            max_flush_bytes = self.max_inflight_bytes - self.inflight_bytes

        logging.info(f"max_flush_bytes = {max_flush_bytes}")

        to_be_flushed_packets: list[Packet] = []
        to_be_flushed_bytes: int = 0
        # ... and start packaging:

        while True:
            global_header_size = Packet.Header.size

            # add frames to the packet until either max_packet_size or max_flush_bytes is exceeded:
            to_be_packaged_frames: list[Frame] = []
            to_be_packaged_bytes: int = 0

            while True:
                if len(self.frame_queue) == 0:
                    # no more frames to add
                    break

                # decide if we can package one more frame:
                predicted_packet_size = global_header_size + \
                    to_be_packaged_bytes + len(self.frame_queue[0])

                if predicted_packet_size > self.max_packet_size:
                    logging.info("A")
                    # this should only happen if the to_be_packaged_frames list is not empty, otherwise...
                    if len(to_be_packaged_frames) == 0:
                        logging.error(
                            f"The frame {self.frame_queue[0]} cannot be sent without exceeding the maximum packet size!")
                        # since we can do nothing here, the ill-sized frame is now clogging the queue
                    break
                elif to_be_flushed_bytes + predicted_packet_size > max_flush_bytes:
                    logging.info("B")
                    # let's not trust our own implementation and log an error in case the send window size is too small.
                    if len(to_be_packaged_frames) == 0 and predicted_packet_size > self.max_inflight_bytes:
                        logging.error(
                            f"The frame {self.frame_queue[0]} cannot be sent without exceeding the send window!")
                        # since we can do nothing here, the ill-sized frame/the ill-sized send window is now clogging the queue
                    break
                else:
                    logging.info("C")
                    # we can add this frame to the packet!
                    frame = self.frame_queue.pop()
                    to_be_packaged_frames.append(frame)
                    to_be_packaged_bytes += len(frame)

                logging.info(f"{predicted_packet_size} {to_be_packaged_frames}")
            

            if len(to_be_packaged_frames) == 0:
                logging.info("NO FRAMES TO BUILD PACKETS UH OH")
                # we cannot build another packet with the frame queue.
                # it was either empty, or the max. packet size is exceeded, or the send window is exceeded.
                break

            # let's start packaging frames!
            packet_id = self.last_sent_packet_id + 1
            packet = Packet(1, self.connection_id, packet_id, to_be_packaged_frames)
            self.last_sent_packet_id = packet_id
            to_be_flushed_packets.append(packet)
            to_be_flushed_bytes += len(packet)

        for packet in to_be_flushed_packets:
            data = packet.pack()
            self.inflight_bytes += len(data)
            self.inflight_packets.appendleft((time.time(), packet))
            logging.info(f"sending packet: {self.inflight_packets[-1]}")
            self.connection_manager.sendto(
                data, (self.remote_host, self.remote_port)
            )

    def current_timeout(self, current_time) -> float:
        """
        returns a float indicating the seconds until the next timeout occurs
        (could be either retransmit or connection timeout)
        """

        # self.last_updated = recv timestamp of last seen packet from peer
        connection_timeout = max(0, self.last_updated + self.connection_timeout - current_time)

        if len(self.inflight_packets) != 0:
            # self.inflight_packets[0][0] = _send_ timestamp of "oldest" inflight packet (is updated upon retransmission)
            retransmit_timeout = max(0, self.inflight_packets[0][0] + self.retransmit_timeout - current_time)
            return min(retransmit_timeout, connection_timeout)
        else:
            return connection_timeout

    def timed_out(self, current_time):
        if current_time > self.last_updated + self.connection_timeout:
            self.close()
        if len(self.inflight_packets) > 0:
            if current_time > self.inflight_packets[0][0] + self.retransmit_timeout:
                self.retransmit_timeout_triggered = True  # in that case, flush() needs to do retransmissions

    def update(self, packet: Packet, addrinfo):
        # this function applies updates to the connection/streams from a packets.

        self.last_updated = time.time()

        if self.remote_host != addrinfo[0]:
            logging.info(
                f"Host of connection {self.connection_id} changed from {self.remote_host} to {addrinfo[0]}")
            self.remote_host = addrinfo[0]
        if self.remote_port != addrinfo[1]:
            logging.info(
                f"Port of connection {self.connection_id} changed from {self.remote_port} to {addrinfo[1]}")
            self.remote_port = addrinfo[1]

        # Reasons to drop
        if packet.header.version != 1:
            logging.info("Packet dropped due to invalid header")
            return
        # elif packet.header.connection_id != self.connection_id:
        #     logging.info("Packet dropped due to invalid Connection ID")
        #     return
        elif not packet.correctChecksum:
            logging.info("Packet dropped due to invalid checksum")
            return

        if packet.header.packet_id == self.next_recv_packet_id:
            self.next_recv_packet_id += 1

            # TODO: increase the congestion window here
            if self.is_slowstart:
                pass # TODO double
            else:
                pass # TODO add

            # if the packet contained at least one frame other than AckFrame or an ExitFrame send a response
            if next((frame for frame in packet.frames if
                     (type(frame) != AckFrame and
                      type(frame) != ExitFrame)
                     ), None):
                self.queue_frame(AckFrame(packet.header.packet_id + 1), transmit_first=True)

        else:
            # drop the packet since we don't allow reordered packets for now.
            return

        # TODO: detect increase/decrease of send window size.

        for frame in packet.frames:
            if isinstance(frame, AckFrame):
                acked_packet_id = frame.header.packet_id
                acked_packets = [tp for tp in self.inflight_packets if tp[1].header.packet_id < acked_packet_id]
                for tp in acked_packets:
                    self.inflight_packets.remove(tp)
                    self.inflight_bytes -= len(tp[1].pack())

            self.handle_frame(frame)

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

        #logging.info(f"queue_frame({type(frame)})")

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
                logging.warning(
                    f"Scheduled unknown frame type {frame} for transmission")

    def close(self):
        self.flush()
        self.closed = True

    def is_closed(self):
        # returns if this connection is closed
        # connection is closed when
        # transmission is done, or connection timed out, or on irrecoverable error
        # depends on both the state of Connection as well as ConnectionHandler
        return self.closed

    @abstractmethod
    def handle_frame(self, frame: Frame):
        # to be implemented by server/client
        ...
