from common import (
    Stream,
    Connection,
    ConnectionManager,
    UnknownConnectionIDEvent,
    ZeroConnectionIDEvent,
    ConnectionTerminatedEvent,
)
from packet import Packet
from frame import *

import logging
import pathlib
import common.util as util


class ServerConnection(Connection):

    def __init__(self, connection_manager: ConnectionManager, host: str, port: int, connection_id: int):
        super().__init__(connection_manager, host, port, connection_id)

    def handle_frame(self, frame: Frame):
        # this function is called upon reception of a frame
        # do something with it
        # self.queue_frame(ErrorFrame(0, 0, 0, "not implemented yet"))

        if isinstance(frame, AckFrame):
            pass
            return

        elif isinstance(frame, ExitFrame):
            logging.info("got an exit frame on connection id " +
                         str(self.connection_id))
            self.close()
            # self.connection_manager.remove_connection(self)
            return

        elif isinstance(frame, ReadFrame):
            # if ReadFrame with an existing stream id is received, queue an ErrorFrame
            logging.info("queued frames: " + str(len(self.frame_queue)))
            self.flush()
            if frame.header.stream_id in self.streams:
                # check error codes
                self.queue_frame(ErrorFrame(
                    frame.header.stream_id, "stream id already exists"))
                return
            # if the path does not exist, send an error frame
            if not pathlib.Path(frame.payload.data).exists():
                self.queue_frame(ErrorFrame(
                    frame.header.stream_id, "file not found"))
                return
            # check if the offset+length is greater than the file size
            if (frame.header.offset + frame.header.length) > pathlib.Path(frame.payload.data).stat().st_size:
                self.queue_frame(ErrorFrame(
                    0, "offset+length greater than file size"))
                return
            
            if frame.header.flags & 0b00000001:
                logging.info("Resumption chekcsum check requested")
                checksum_until_offset = util.crc32_file_checksum(frame.payload.data, offset=0, length=frame.header.offset)
                if frame.header.checksum != checksum_until_offset:
                    self.queue_frame(ErrorFrame(
                        0, "checksum mismatch"))
                    return

            # create a new stream if everything is fine
            stream = Stream(frame.header.stream_id, frame.payload.data, "w")
            self.streams[frame.header.stream_id] = stream
            return

        elif isinstance(frame, ChecksumFrame):
            # if the stream id does not exist, send an error frame
            if frame.header.stream_id not in self.streams:
                self.queue_frame(ErrorFrame(
                    frame.header.stream_id, "stream id does not exist"))
                return
            # send the checksum of the file
            self.queue_frame(AnswerFrame(
                frame.header.stream_id, self.streams[frame.header.stream_id].get_file_checksum()))
            return

        else:
            logging.error(
                "Recieved unknown frame with type \"" + str(frame.type) + "\"")
            self.queue_frame(ErrorFrame(0, "not implemented yet"))


# Socket -> ConnectionManager
# ConnectionHander -> Connection
# Connection -> ServerConecion ClientConnection

def run_server(port: int, p = 1, q = 0, ipv6 = False):
    connection_manager = ConnectionManager(port, p, q, ipv6)
    logging.info(
        f"server listening at {connection_manager.local_address} on port {connection_manager.local_port}")

    for event in connection_manager.loop():
        logging.info(type(event).__name__)
        # Send to different ServerConnections depending on header
        if isinstance(event, UnknownConnectionIDEvent):
            logging.info("got an unknown connection id event, ignoring...")

        elif isinstance(event, ZeroConnectionIDEvent):
            logging.info("got a zero connection id event")
            # if the connection id is 0, then it is a new connection request, and it should either have no frames, or a single ReadFrame
            if len(event.packet.frames) > 1 and not isinstance(event.packet.frames[0], ReadFrame):
                continue
            logging.info(f"adding a new client connection...")
            # if the checks pass, create a new ServerConnection
            conn = ServerConnection(
                connection_manager, event.host, event.port, connection_manager.next_connection_id())
            connection_manager.add_connection(conn)
            conn.update(event.packet, (event.host, event.port))
        elif isinstance(event, ConnectionTerminatedEvent):
            # server continues to listen for new connections in this case
            pass