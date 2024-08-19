import struct
from frame.frame import Frame


class DataFrame(Frame):
    type = 6

    class Header(Frame.Header):
        size = struct.calcsize('!BHI6sH')

        def __init__(self, type: int, stream_id: int, frame_id: int, offset: int, payload_length: int) -> None:
            self.type = type
            self.stream_id = stream_id
            self.frame_id = frame_id
            self.offset = offset
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('!BHI6sH', self.type, self.stream_id, self.frame_id, self.offset, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'DataFrame.Header':
            type, stream_id, frame_id,  offset, payload_length = struct.unpack(
                '!BHI6sH', header_bytes)
            print(payload_length)
            return cls(type, stream_id, frame_id, int.from_bytes(offset, 'big'), payload_length)

    class Payload(Frame.Payload):

        def __init__(self, payload: bytes) -> None:
            self.data = payload

        def __len__(self) -> int:
            return len(self.data)

        def pack(self) -> bytes:
            return self.data

        @classmethod
        def unpack(cls, payload_bytes: bytes) -> 'DataFrame.Payload':
            return cls(payload_bytes)

    def __init__(self, type: int, stream_id: int, frame_id: int, offset: int, payload_length: int, payload: str) -> None:
        self.header = self.Header(
            type, stream_id, frame_id, offset, payload_length)
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'DataFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        return cls(header.type, header.stream_id, header.frame_id, header.offset, header.payload_length, payload.data)
