from common import ConnectionManager
from common import Connection
from packet import Packet
from frame import (
    ErrorFrame,
    DataFrame,
)

import logging

class ServerConnection(Connection):

    def __init__(self, connection_manager: ConnectionManager, host: str, port: int, packet: Packet):
        super().__init__(connection_manager, host, port)
        # if necessary
        self.queue_frame(DataFrame(0, 0, 0, 10 * b"a"))

    def handle_packet(self, packet: Packet):
        # do something with it
        self.queue_frame(ErrorFrame(0, 0, 0, "not implemented yet"))


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
            connection_manager.add_connection(ServerConnection(connection_manager, event.host, event.port, event.packet))
