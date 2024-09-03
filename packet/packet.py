import struct
from frame.command import *
from frame.data import *
from frame.control import *

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
            fields = ', '.join(f'{key}={value}' for key,
                               value in self.__dict__.items())
            return f'{self.__class__.__name__}({fields})'

        def __str__(self) -> str:
            return self.__repr__()

        def __len__(self) -> int:
            return self.size

        def pack(self) -> bytes:
            return struct.pack('<BII3s', self.version, self.connection_id, self.packet_id, self.checksum.to_bytes(3, "little"))

        @classmethod
        def unpack(cls, packet_bytes: bytes):
            version, connection_id, packet_id, checksum = struct.unpack('<BII3s', packet_bytes[:12])
            return cls(version, connection_id, packet_id, checksum)

    def __init__(self, version: int, connection_id: int, packet_id: int, checksum: int, frames: list) -> None:
        self.header = Packet.Header(version, connection_id, packet_id, checksum)
        self.frames = frames

    def __repr__(self) -> str:
        fields = ', '.join(f'{key}={value}' for key,
                           value in self.__dict__.items())
        return f'{self.__class__.__name__}({fields})'

    def __str__(self) -> str:
        return self.__repr__()
    
    def __len__(self) -> int:
        return self.header.size + sum([len(frame) for frame in self.frames])

    def pack(self) -> bytes:
        return self.header.pack() + b''.join(frame.pack() for frame in self.frames)

    @classmethod
    def unpack(cls, packet_bytes: bytes) -> 'Packet':
        header = Packet.Header.unpack(packet_bytes)
        frames = []
        frames_bytes = packet_bytes[12:]
        while frames_bytes:
            frame_type = frames_bytes[0]
            frame = frame_types[frame_type].unpack(frames_bytes)
            frames.append(frame)
            frames_bytes = frames_bytes[len(frame):]
        return cls(header.version, header.connection_id, header.packet_id, header.checksum, frames)
