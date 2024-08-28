from common import ConnectionHandler
from common import Socket

import logging

def run_server(port: int):
    sock = Socket(port)
    logging.info(f"server listening at {sock.local_address} on port {sock.local_port}")

    while True:
        data, addrinfo = sock.socket.recvfrom(65536)
        logging.info(f"received a datagram from {addrinfo}")
