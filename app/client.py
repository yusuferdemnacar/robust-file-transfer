from common import ConnectionManager
from common import Connection
from packet import Packet
from frame import (
    ErrorFrame,
    ReadFrame,
)

import logging

class ClientConnection(Connection):
    readJobs = []
    streamID = -1

    def __init__(self, connection_manager, host, port, files: list[str]):
        super().__init__(connection_manager, host, port)
    
    def handle_packet(self, packet: Packet):
        # do something with it
        self.queue_frame(ErrorFrame(0, 0, 0, "not implemented yet"))

    def read_file(self, name: str):
        fileIO = open(name)
        jobStreamID = self.next_ID()
        self.readJobs.add((name, fileIO, jobStreamID))
        self.queue_frame(ReadFrame(jobStreamID, 0, 0, 0, 10, 0, 10, 10 * "a"))

    def next_ID(self):
        streamID = streamID + 1
        return self.streamID


def run_client(host, port, files):
    connection_manager = ConnectionManager()
    connection = ClientConnection(connection_manager, host, port, files)
    logging.info(f"client socket bound to {connection_manager.local_address} on port {connection_manager.local_port}")

    for event in connection_manager.loop(init=connection):
        logging.info(event)

        if isinstance(event, UnknownConnectionIDEvent):
            # ignore unknown packet
            pass
        