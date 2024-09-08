import struct
from frame.frame import Frame


class DataFrame(Frame):
    type = 6

    class Header(Frame.Header):
        size = struct.calcsize('<BH6sH')

        def __init__(self, stream_id: int, offset: int, payload_length: int) -> None:
            self.type = DataFrame.type
            self.stream_id = stream_id
            self.offset = offset
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BH6sH', self.type, self.stream_id, int.to_bytes(self.offset, 6, 'little'), self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'DataFrame.Header':
            type, stream_id, offset, payload_length = struct.unpack(
                '<BH6sH', header_bytes)
            if type != DataFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {DataFrame.type})')
            return cls(stream_id, int.from_bytes(offset, 'little'), payload_length)

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

    def __init__(self, stream_id: int, offset: int, payload: bytes) -> None:
        self.header = self.Header(stream_id, offset, len(payload))
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'DataFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        if len(payload) != header.payload_length:
            raise ValueError(
                f'Invalid payload length: {len(payload)} (expected {header.payload_length})')
        return cls(header.stream_id, header.offset, payload.data)
