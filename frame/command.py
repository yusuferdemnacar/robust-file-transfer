import struct
from frame.frame import Frame


class ReadFrame(Frame):
    type = 7

    class Header(Frame.Header):
        size = struct.calcsize('<BHB6s6sIH')

        def __init__(self, stream_id: int, flags: bytes, offset: int, length: int, checksum: int, payload_length: int) -> None:
            self.type = ReadFrame.type
            self.stream_id = stream_id
            self.flags = flags
            self.offset = offset
            self.length = length
            self.checksum = checksum
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHB6s6sIH', self.type, self.stream_id, self.flags, int.to_bytes(self.offset, 6, 'little'), int.to_bytes(self.length, 6, 'little'), self.checksum, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ReadFrame.Header':
            type, stream_id, flags, offset, length, checksum, payload_length = struct.unpack(
                '<BHB6s6sIH', header_bytes)
            if type != ReadFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {ReadFrame.type})')
            return cls(stream_id, flags, int.from_bytes(offset, 'little'), int.from_bytes(length, 'little'), checksum, payload_length)

    class Payload(Frame.Payload):

        def __init__(self, path: str) -> None:
            self.data = path

        def __len__(self) -> int:
            return len(self.data)

        def pack(self) -> bytes:
            return bytes(self.data, 'utf-8')

        @classmethod
        def unpack(cls, payload_bytes: bytes) -> 'ReadFrame.Payload':
            return cls(str(payload_bytes, 'utf-8'))

    def __init__(self, stream_id: int, flags: bytes, offset: int, length: int, checksum: int, payload: str) -> None:
        self.header = self.Header(
            stream_id, flags, offset, length, checksum, len(payload))
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ReadFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        if len(payload) != header.payload_length:
            raise ValueError(
                f'Invalid payload length: {len(payload)} (expected {header.payload_length})')
        return cls(header.stream_id, header.flags, header.offset, header.length, header.checksum, payload.data)


class WriteFrame(Frame):
    type = 8

    class Header(Frame.Header):
        size = struct.calcsize('<BH6s6sH')

        def __init__(self, stream_id: int, offset: int, length: int, payload_length: int) -> None:
            self.type = WriteFrame.type
            self.stream_id = stream_id
            self.offset = offset
            self.length = length
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BH6s6sH', self.type, self.stream_id, self.offset.to_bytes(6, 'little'), self.length.to_bytes(6, 'little'), self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'WriteFrame.Header':
            type, stream_id, offset, length, payload_length = struct.unpack(
                '<BH6s6sH', header_bytes)
            if type != WriteFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {WriteFrame.type})')
            return cls(stream_id, int.from_bytes(offset, 'little'), int.from_bytes(length, 'little'), payload_length)

    class Payload(Frame.Payload):

        def __init__(self, path: str) -> None:
            self.data = path

        def __len__(self) -> int:
            return len(self.data)

        def pack(self) -> bytes:
            return bytes(self.data, 'utf-8')

        @classmethod
        def unpack(cls, payload_bytes: bytes) -> 'WriteFrame.Payload':
            return cls(str(payload_bytes, 'utf-8'))

    def __init__(self, stream_id: int, offset: int, length: int, payload: str) -> None:
        self.header = self.Header(stream_id, offset, length, len(payload))
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'WriteFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        if len(payload) != header.payload_length:
            raise ValueError(
                f'Invalid payload length: {len(payload)} (expected {header.payload_length})')
        return cls(header.stream_id, header.offset, header.length, payload.data)


class ChecksumFrame(Frame):
    type = 9

    class Header(Frame.Header):
        size = struct.calcsize('<BHH')

        def __init__(self, stream_id: int, payload_length: int) -> None:
            self.type = ChecksumFrame.type
            self.stream_id = stream_id
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHH', self.type, self.stream_id, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ChecksumFrame.Header':
            type, stream_id, payload_length = struct.unpack(
                '<BHH', header_bytes)
            if type != ChecksumFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {ChecksumFrame.type})')
            return cls(stream_id, payload_length)

    class Payload(Frame.Payload):

        def __init__(self, path: str) -> None:
            self.data = path

        def __len__(self) -> int:
            return len(self.data)

        def pack(self) -> bytes:
            return bytes(self.data, 'utf-8')

        @classmethod
        def unpack(cls, payload_bytes: bytes) -> 'ChecksumFrame.Payload':
            return cls(str(payload_bytes, 'utf-8'))

    def __init__(self, stream_id: int, payload: str) -> None:

        self.header = self.Header(stream_id, len(payload))
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ChecksumFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        if len(payload) != header.payload_length:
            raise ValueError(
                f'Invalid payload length: {len(payload)} (expected {header.payload_length})')
        return cls(header.stream_id, payload.data)


class StatFrame(Frame):
    type = 10

    class Header(Frame.Header):
        size = struct.calcsize('<BHH')

        def __init__(self, stream_id: int, payload_length: int) -> None:
            self.type = StatFrame.type
            self.stream_id = stream_id
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHH', self.type, self.stream_id, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'StatFrame.Header':
            type, stream_id, payload_length = struct.unpack(
                '<BHH', header_bytes)
            if type != StatFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {StatFrame.type})')
            return cls(stream_id, payload_length)

    class Payload(Frame.Payload):

        def __init__(self, path: str) -> None:
            self.data = path

        def __len__(self) -> int:
            return len(self.data)

        def pack(self) -> bytes:
            return bytes(self.data, 'utf-8')

        @classmethod
        def unpack(cls, payload_bytes: bytes) -> 'StatFrame.Payload':
            return cls(str(payload_bytes, 'utf-8'))

    def __init__(self, stream_id: int, payload: str) -> None:
        self.header = self.Header(stream_id, len(payload))
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'StatFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        if len(payload) != header.payload_length:
            raise ValueError(
                f'Invalid payload length: {len(payload)} (expected {header.payload_length})')
        return cls(header.stream_id, payload.data)


class ListFrame(Frame):
    type = 11

    class Header(Frame.Header):
        size = struct.calcsize('<BHH')

        def __init__(self, stream_id: int, payload_length: int) -> None:
            self.type = ListFrame.type
            self.stream_id = stream_id
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHH', self.type, self.stream_id, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ListFrame.Header':
            type, stream_id, payload_length = struct.unpack(
                '<BHH', header_bytes)
            if type != ListFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {ListFrame.type})')
            return cls(stream_id, payload_length)

    class Payload(Frame.Payload):

        def __init__(self, path: str) -> None:
            self.data = path

        def __len__(self) -> int:
            return len(self.data)

        def pack(self) -> bytes:
            return bytes(self.data, 'utf-8')

        @classmethod
        def unpack(cls, payload_bytes: bytes) -> 'ListFrame.Payload':
            return cls(str(payload_bytes, 'utf-8'))

    def __init__(self, stream_id: int, path: str) -> None:
        self.header = self.Header(stream_id, len(path))
        self.payload = self.Payload(path)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ListFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        if len(payload) != header.payload_length:
            raise ValueError(
                f'Invalid payload length: {len(payload)} (expected {header.payload_length})')
        return cls(header.stream_id, payload.data)
