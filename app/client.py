from common import ConnectionHandler
from common import Socket

import logging

def run_client(host: str, port: int):
    sock = Socket()
    logging.info(f"client socket bound to {sock.local_address} on port {sock.local_port}")

    sock.socket.sendto(b"Hello World\n", (host, port))
