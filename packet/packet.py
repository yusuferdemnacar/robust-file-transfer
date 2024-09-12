import struct
import json
from frame.command import *
from frame.data import *
from frame.control import *
from zlib import crc32

frame_types = {
    0: AckFrame,
    1: ExitFrame,
    2: ConnectionIDChangeFrame,
    3: FlowControlFrame,
    4: AnswerFrame,
    5: ErrorFrame,
    6: DataFrame,
    7: ReadFrame,
    8: WriteFrame,
    9: ChecksumFrame,
    10: StatFrame,
    11: ListFrame,
}


class Packet:

    class Header:

        size = struct.calcsize('<BII3s')

        def __init__(self, version: int, connection_id: int, packet_id: int, checksum: int) -> None:
            self.version = version
            self.connection_id = connection_id
            self.packet_id = packet_id
            self.checksum = checksum

        def __repr__(self) -> str:
            return json.dumps(self.to_dict(), indent=4)

        def __str__(self) -> str:
            return self.__repr__()

        def __len__(self) -> int:
            return self.size

        def pack(self) -> bytes:
            return struct.pack('<BII3s', self.version, self.connection_id, self.packet_id, self.checksum.to_bytes(4, "little")[:3])

        @classmethod
        def unpack(cls, packet_bytes: bytes):
            version, connection_id, packet_id, checksum = struct.unpack(
                '<BII3s', packet_bytes[:cls.size])
            return cls(version, connection_id, packet_id, int.from_bytes(checksum, "little"))

        def to_dict(self):
            return {
                "version": self.version,
                "connection_id": self.connection_id,
                "packet_id": self.packet_id,
                "checksum": self.checksum
            }

    def __init__(self, version: int, connection_id: int, packet_id: int, frames: list) -> None:
        self.header = Packet.Header(version, connection_id, packet_id, 0)
        self.frames = frames
        self.header.checksum = self.calculateChecksum()

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=4)

    def __str__(self) -> str:
        return self.__repr__()

    def __len__(self) -> int:
        return self.header.size + sum([len(frame) for frame in self.frames])

    def pack(self) -> bytes:
        return self.header.pack() + b''.join(frame.pack() for frame in self.frames)

    def createCopy(header: Header, frames: list):
        packet = Packet(header.version, header.connection_id,
                        header.packet_id, frames)
        packet.header.checksum = header.checksum
        return packet

    @classmethod
    def unpack(cls, packet_bytes: bytes) -> 'Packet':
        try:
            header = Packet.Header.unpack(packet_bytes[:Packet.Header.size])
        except struct.error:
            raise ValueError("Invalid packet header")
        frames = []
        frames_bytes = packet_bytes[Packet.Header.size:]
        while frames_bytes:
            frame_type = frames_bytes[0]
            frame_header = frame_types[frame_type].Header.unpack(
                frames_bytes[:frame_types[frame_type].Header.size])
            # if freame has a payload
            if hasattr(frame_header, "payload_length"):
                frame = frame_types[frame_type].unpack(
                    frames_bytes[:frame_types[frame_type].Header.size + frame_header.payload_length])
            else:
                frame = frame_types[frame_type].unpack(
                    frames_bytes[:frame_types[frame_type].Header.size])
            frames.append(frame)
            frames_bytes = frames_bytes[len(frame):]
        return cls.createCopy(header, frames)

    def calculateChecksum(self):
        data = self.pack()
        data = b"".join([data[:Packet.Header.size-3],
                        bytes(b"\x00\x00\x00"), data[Packet.Header.size:]])

        return int.from_bytes(crc32(data).to_bytes(4, "little")[:3], "little")

    @property
    def correctChecksum(self):
        return self.header.checksum == self.calculateChecksum()

    def to_dict(self):
        return {
            "header": self.header.to_dict(),
            "frames": [frame.to_dict() for frame in self.frames]
        }
    
    def contains_non_ack_frame(self):
        return any([not isinstance(frame, AckFrame) for frame in self.frames])
