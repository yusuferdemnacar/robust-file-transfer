from common import (
    ConnectionManager,
    Connection,
    UnknownConnectionIDEvent,
    Stream,
    ConnectionTerminatedEvent,
)
from packet import Packet
from frame import *

import logging
import signal
import pathlib
import common.util as util

class ClientConnection(Connection):
    stream_id_index = 0  # Returns 1 first time due to returning ++0

    def __init__(self, connection_manager, host, port, files: list[str]):
        self.connection_id = None  # will be initialized upon reply from server
        super().__init__(connection_manager, host, port, 0)

        for file_path in files:
            if pathlib.Path(file_path).exists():
                logging.info("File exists, requesting the rest of the file")
                file_size = pathlib.Path(file_path).stat().st_size
                checksum_so_far = util.crc32_file_checksum(file_path, offset=0, length=file_size)
                self.command_read(file_path, offset=file_size, length=0, checkChecksum=True, checksum=checksum_so_far)
            else:
                self.command_read(file_path)
    def handle_frame(self, frame: Frame):
        if isinstance(frame, ExitFrame):
            logging.info("Server closed connection.")
            self.close()
            #self.connection_manager.remove_connection(self)
            return
        elif isinstance(frame, DataFrame):
            # logging.info("Recieved data frame with stream id " +
            #              str(frame.header.stream_id))
            if frame.header.payload_length == 0:
                self.streams[frame.header.stream_id].flush()
                logging.info(
                    "Transfer of " + self.streams[frame.header.stream_id].path + " completed.")
                # ask for checksum
                self.frame_queue.append(ChecksumFrame(
                    frame.header.stream_id, self.streams[frame.header.stream_id].path))
            else:
                self.streams[frame.header.stream_id].file.write(
                    frame.payload.data)
        elif isinstance(frame, AnswerFrame):
            # TODO: Only the checksum answer frame is implemented
            # There is currently no way of knowing which command the answer is for in the spec, so changes are needed to the protocol
            # Assume the answer is for the checksum command for now as it is the only one implemented by the partnering group
            logging.info(
                "File: \"" + self.streams[frame.header.stream_id].path + "\" has been checksummed with value: " + str(frame.payload.data))
            local_checksum = self.streams[frame.header.stream_id].get_file_checksum()
            remote_checksum = frame.payload.data
            logging.info("Local checksum: " + str(local_checksum))
            logging.info("Remote checksum: " + str(remote_checksum))
            # Immediately close the stream after checksum is received
            self.streams[frame.header.stream_id].close()
            logging.info(
                "Closed stream with stream id " + str(frame.header.stream_id))
            # Check if the checksum matches the file, if not delete the file
            if local_checksum == remote_checksum:
                logging.info("Checksums match")
            else:
                logging.error("Checksums do not match, deleting file")
                self.streams[frame.header.stream_id].remove_file()

            del self.streams[frame.header.stream_id]

            if len(self.streams.items()) == 0:
                self.queue_frame(ExitFrame(), transmit_first=True)
                logging.info("Client closing connection.")
                self.close() # pray

        elif isinstance(frame, ErrorFrame):
            logging.error(
                "Recieved error frame on stream id " + str(frame.header.stream_id) + " with message: " + frame.payload.data)
            # close and remove stream
            if frame.header.stream_id == 0:
                logging.error("Error on stream id 0, closing connection")
                stream_ids = list(self.streams.keys())
                for stream_id in stream_ids:
                    self.streams[stream_id].close()
                    del self.streams[stream_id]
                self.queue_frame(ExitFrame())
                self.close()
            else:
                self.streams[frame.header.stream_id].close()
                del self.streams[frame.header.stream_id]
            if all((stream.is_closed for stream in self.streams.values())):
                self.queue_frame(ExitFrame())
                self.close()
        elif isinstance(frame, AckFrame):
            # ignore that, is already handled in connection.py
            pass
        else:
            logging.error(
                "Recieved unknown frame with type \"" + str(frame.type) + "\"")
            self.queue_frame(ErrorFrame(0, "not implemented yet"))

    def command_read(self, path: str, offset=0, length=0, checkChecksum=False, checksum=0):
        # TODO continue read from partially completed file (maybe use "a" mode instead?)
        stream_id = self.next_stream_id()
        self.streams[stream_id] = Stream.open(stream_id, path, "r")
        flags = 0 if not checkChecksum else 0b00000001
        self.queue_frame(ReadFrame(stream_id, flags,
                         offset, length, checksum, path))

    def command_checksum(self, stream_id: int):
        self.queue_frame(ChecksumFrame(
            stream_id, self.streams[stream_id].path))

    def command_write(self, path: str, offset=0, length=0):
        pass

    def command_stat(self, path: str):
        pass

    def command_list(self, path: str):
        pass

    def next_stream_id(self):
        self.stream_id_index += 1
        return self.stream_id_index

    def update_connection_id(self, packet: Packet, host, port):
        new_id = packet.header.connection_id
        if self.connection_id != 0:
            raise Exception(
                "Can only update the connection id once in the beginning")
        self.connection_id = new_id
        del self.connection_manager.connections[0]
        self.connection_manager.connections[new_id] = self
        self.update(packet, (host, port))

def run_client(host, port, files, p = 0, q = 1, ipv6 = False):

    def handle_exit(signum, frame):
        logging.info("Exiting...")
        for connection in connection_manager.connections.values():
            stream_ids = list(connection.streams.keys())
            for stream_id in stream_ids:
                connection.streams[stream_id].close()
                del connection.streams[stream_id]
            connection.queue_frame(ExitFrame())
            connection.close()

        exit(0)
    
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)

    connection_manager = ConnectionManager(0, p, q, ipv6)
    connection = ClientConnection(connection_manager, host, port, files)
    logging.info(
        f"client socket bound to {connection_manager.local_address} on port {connection_manager.local_port}")

    connection_manager.add_connection(connection)
    for event in connection_manager.loop():
        logging.info(type(event).__name__)

        if isinstance(event, UnknownConnectionIDEvent):
            # ignore unknown packet, except if connection.connection_id is zero
            if connection.connection_id == 0:
                connection.update_connection_id(
                    event.packet, event.host, event.port)
        elif isinstance(event, ConnectionTerminatedEvent):
            # exit in this case
            break
