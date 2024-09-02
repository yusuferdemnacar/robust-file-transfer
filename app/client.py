from common import (
    ConnectionManager,
    Connection,
    UnknownConnectionIDEvent
)
from packet import Packet
from frame import (
    AnswerFrame,
    ChecksumFrame,
    ErrorFrame,
    DataFrame,
    ReadFrame,
    Frame,
)

import logging

class ClientConnection(Connection):
    streamID = 0 # Returns 1 first time due to returning ++0

    def __init__(self, connection_manager, host, port, files: list[str]):
        self.readJobs = [] # (name, checkChecksum, checksum, fileHandle, streamID)
        self.commandJobs = [] # (type, name, streamID)
        self.connection_id = None # will be initialized upon reply from server
        super().__init__(connection_manager, host, port, 0)

        for file in files:
            self.command_read(file)
    
    def handle_frame(self, frame: Frame):
        if isinstance(frame, DataFrame):
            for i in range(len(self.readJobs)):
                job = name, checkChecksum, checksum, fileHandle, jobStreamID = self.readJobs[i]
                if jobStreamID != frame.header.stream_id:
                    continue
                if frame.header.payload_length == 0:
                    self.readJobs.remove(job)
                    #TODO check checksum
                    logging.info("Transfer of " + name + " completed.")
                    break
                fileHandle.write(frame.payload.data)
                break
        if isinstance(frame, AnswerFrame):
            for i in range(len(self.commandJobs)):
                job = type, name, jobStreamID = self.commandJobs[i]
                if frame.header.stream_id == jobStreamID:
                    self.commandJobs.remove(job)
                    match type:
                        case ChecksumFrame.type:
                            logging.info("File: \"" + name + "\" has the checksum " + frame.payload + ".")
                        case _:
                            logging.error("Unknown response type \"" + type + "\"")
        else:
            logging.error("Recieved unknown frame with type \"" + frame.type + "\"")
            self.queue_frame(ErrorFrame(frame.header.stream_id, "not implemented yet"))
    
    def command_read(self, name: str, offset = 0, length = 0, checkChecksum = False, checksum = 0):
        fileIO = open(name, "w") # TODO continue read from partially completed file (maybe use "a" mode instead?)
        jobStreamID = self.next_streamID()
        flags = 1 if checkChecksum else 0
        self.readJobs.append((name, checkChecksum, checksum, fileIO, jobStreamID))
        self.queue_frame(ReadFrame(jobStreamID, flags, offset, length, checksum, name))
    
    def command_checksum(self, name: str):
        jobStreamID = self.next_streamID()
        self.commandJobs.append((ChecksumFrame.type, name, jobStreamID))
        self.queue_frame(ChecksumFrame(jobStreamID, name))
    
    def command_write(self, name: str, offset = 0, length = 0):
        pass

    def command_stat(self, name: str):
        pass

    def command_list(self, path: str):
        pass

    def next_streamID(self):
        self.streamID = self.streamID + 1
        return self.streamID
    
    def update_connection_id(self, packet: Packet):
        new_id = packet.header.connection_id
        if self.connection_id != 0:
            raise Exception("Can only update the connection id once in the beginning")
        self.connection_id = new_id
        del self.connection_manager.connections[0]
        self.connection_manager.connections[new_id] = self
        self.update(packet)
        self.connection_manager.last_updated.append(self)

def run_client(host, port, files):
    connection_manager = ConnectionManager()
    connection = ClientConnection(connection_manager, host, port, files)
    logging.info(f"client socket bound to {connection_manager.local_address} on port {connection_manager.local_port}")

    connection_manager.add_connection(connection)
    for event in connection_manager.loop():
        logging.info(event)

        if isinstance(event, UnknownConnectionIDEvent):
            # ignore unknown packet, except if connection.connection_id is zero
            if connection.connection_id == 0:
                connection.update_connection_id(event.packet.header.connection_id)
