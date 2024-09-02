from common import (
    Stream,
    Connection,
    ConnectionManager,
    UnknownConnectionIDEvent,
)
from packet import Packet
from frame import (
    AckFrame,
    ErrorFrame,
    DataFrame,
    ReadFrame,
    Frame,
)

import logging
import pathlib

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

        if isinstance(frame, ReadFrame):
            # if ReadFrame with an existing stream id is received, queue an ErrorFrame
            if frame.header.stream_id in self.streams:
                self.queue_frame(ErrorFrame(0, "stream id already exists")) # check error codes
                return

            # if the path does not exist, send an error frame
            if not pathlib.Path(frame.payload.data).exists():
                self.queue_frame(ErrorFrame(0, "file not found"))
                return

            # check if the offset+length is greater than the file size
            if (frame.header.offset + frame.header.length) > pathlib.Path(frame.payload.data).stat().st_size:
                self.queue_frame(ErrorFrame(0, "offset+length greater than file size"))
                return
            
            # TODO: handle cheksum checking

            # create a new stream if everything is fine
            stream = Stream(frame.stream_id, frame.payload.data)
            self.streams[frame.header.stream_id] = stream

            # assuming 128 bytes chunks for now
            for i in range(0, frame.header.length, 128):
                stream.file.seek(frame.header.offset + i)
                data = stream.file.read(128)
                self.queue_frame(DataFrame(stream.stream_id, frame.header.offset + i, data)),
            return
                



# Socket -> ConnectionManager
# ConnectionHander -> Connection
# Connection -> ServerConecion ClientConnection

def run_server(port: int):
    connection_manager = ConnectionManager(local_port=port)
    logging.info(f"server listening at {connection_manager.local_address} on port {connection_manager.local_port}")

    for event in connection_manager.loop():
        logging.info(event)
        # Send to different ServerConnections depending on header
        if isinstance(event, UnknownConnectionIDEvent):
            logging.info("got an unknown connection id event")
            # if the connection id is not 0, then it is not a new connection request, ignore it
            if event.packet.header.connection_id != 0:
                continue
            # if the connection id is 0, then it is a new connection request, and it should either have no frames, or a single ReadFrame
            if len(event.packet.frames) > 1 and not isinstance(event.packet.frames[0], ReadFrame):
                continue
            logging.info(f"adding a new client connection...")
            # if the checks pass, create a new ServerConnection
            conn = ServerConnection(connection_manager, event.address[0], event.address[1], connection_manager.next_connection_id())
            connection_manager.add_connection(conn)
            # TODO think through if calling self.update() instead is better, eg. to initialize next_recv_packet_id
            # connection is now established, if there is a ReadFrame, open a stream as well
            if len(event.packet.frames) != 0:
                for frame in event.packet.frames:
                    conn.handle_frame(frame)
