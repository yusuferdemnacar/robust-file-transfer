from common import (
    ConnectionManager,
    Connection,
    UnknownConnectionIDEvent,
    Stream,
)
from packet import Packet
from frame import *

import logging


class ClientConnection(Connection):
    stream_id_index = 0  # Returns 1 first time due to returning ++0

    def __init__(self, connection_manager, host, port, files: list[str]):
        self.connection_id = None  # will be initialized upon reply from server
        super().__init__(connection_manager, host, port, 0)

        for file in files:
            self.command_read(file)

    def handle_frame(self, frame: Frame):
        if isinstance(frame, ExitFrame):
            logging.info("Server closed connection.")
            self.connection_manager.remove_connection(self)
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
                # self.streams[frame.header.stream_id].close()
                # del self.streams[frame.header.stream_id]
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
            remote_checksum = int.from_bytes(frame.payload.data, "little")
            # Immediately close the stream after checksum is received
            self.streams[frame.header.stream_id].close()
            logging.info(
                "Closed stream with stream id " + str(frame.header.stream_id))
            # Check if the checksum matches the file, if not delete the file

            print("Local checksum: " + str(local_checksum))
            print("Remote checksum: " + str(remote_checksum))
            if local_checksum == remote_checksum:
                logging.info("Checksums match")
            else:
                logging.error("Checksums do not match, deleting file")
                self.streams[frame.header.stream_id].remove_file()

            del self.streams[frame.header.stream_id]

        elif isinstance(frame, ErrorFrame):
            logging.error(
                "Recieved error frame on stream id " + str(frame.header.stream_id) + " with message: " + frame.payload.data)
            # close and remove stream
            self.streams[frame.header.stream_id].close()
            del self.streams[frame.header.stream_id]
        elif isinstance(frame, AckFrame):
            # ignore that, is already handled in connection.py
            pass
        else:
            logging.error(
                "Recieved unknown frame with type \"" + str(frame.type) + "\"")
            self.queue_frame(ErrorFrame(
                frame.header.stream_id, "not implemented yet"))

    def command_read(self, path: str, offset=0, length=0, checkChecksum=False, checksum=0):
        # TODO continue read from partially completed file (maybe use "a" mode instead?)
        stream_id = self.next_stream_id()
        self.streams[stream_id] = Stream.open(stream_id, path)
        flags = 1 if checkChecksum else 0
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


def run_client(host, port, files):
    connection_manager = ConnectionManager()
    connection = ClientConnection(connection_manager, host, port, files)
    logging.info(
        f"client socket bound to {connection_manager.local_address} on port {connection_manager.local_port}")

    connection_manager.add_connection(connection)
    for event in connection_manager.loop():
        logging.info(event)

        if isinstance(event, UnknownConnectionIDEvent):
            # ignore unknown packet, except if connection.connection_id is zero
            if connection.connection_id == 0:
                connection.update_connection_id(
                    event.packet, event.host, event.port)
