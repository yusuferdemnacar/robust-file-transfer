# main.py
from packet.packet import Packet

if __name__ == "__main__":
    file_path = 'packet.bin'
    with open(file_path, 'rb') as file:
        packet_bytes = file.read()
    p = Packet.unpack(packet_bytes)
    print(p)
