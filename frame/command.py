import struct
from frame.frame import Frame


class ReadFrame(Frame):
    type = 7

    class Header(Frame.Header):
        size = struct.calcsize('<BHIB6s6sIH')

        def __init__(self, type: int, stream_id: int, frame_id: int, flags: bytes, offset: int, length: int, checksum: int, payload_length: int) -> None:
            self.type = type
            self.stream_id = stream_id
            self.frame_id = frame_id
            self.flags = flags
            self.offset = offset
            self.length = length
            self.checksum = checksum
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHIB6s6sIH', self.type, self.stream_id, self.frame_id, self.flags, int.to_bytes(self.offset, 6, 'little'), int.to_bytes(self.length, 6, 'little'), self.checksum, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ReadFrame.Header':
            type, stream_id, frame_id, flags, offset, length, checksum, payload_length = struct.unpack(
                '<BHIB6s6sIH', header_bytes)
            return cls(type, stream_id, frame_id, flags, int.from_bytes(offset, 'little'), int.from_bytes(length, 'little'), checksum, payload_length)

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

    def __init__(self, type: int, stream_id: int, frame_id: int, flags: bytes, offset: int, length: int, checksum: int, payload_length: int, payload: str) -> None:
        self.header = self.Header(
            type, stream_id, frame_id, flags, offset, length, checksum, payload_length)
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ReadFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        return cls(header.type, header.stream_id, header.frame_id, header.flags, header.offset, header.length, header.checksum, header.payload_length, payload.data)


class WriteFrame(Frame):
    type = 8

    class Header(Frame.Header):
        size = struct.calcsize('<BHI6s6sH')

        def __init__(self, type: int, stream_id: int, frame_id: int, offset: int, length: int, payload_length: int) -> None:
            self.type = type
            self.stream_id = stream_id
            self.frame_id = frame_id
            self.offset = offset
            self.length = length
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHI6s6sH', self.type, self.stream_id, self.frame_id, self.offset.to_bytes(6, 'little'), self.length.to_bytes(6, 'little'), self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'WriteFrame.Header':
            type, stream_id, frame_id, offset, length, payload_length = struct.unpack(
                '<BHI6s6sH', header_bytes)
            return cls(type, stream_id, frame_id, int.from_bytes(offset, 'little'), int.from_bytes(length, 'little'), payload_length)

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

    def __init__(self, type: int, stream_id: int, frame_id: int, offset: int, length: int, payload_length: int, payload: str) -> None:
        self.header = self.Header(
            type, stream_id, frame_id, offset, length, payload_length)
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'WriteFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        return cls(header.type, header.stream_id, header.frame_id, header.offset, header.length, header.payload_length, payload.data)


class ChecksumFrame(Frame):
    type = 9

    class Header(Frame.Header):
        size = struct.calcsize('<BHIH')

        def __init__(self, type: int, stream_id: int, frame_id: int, payload_length: int) -> None:
            self.type = type
            self.stream_id = stream_id
            self.frame_id = frame_id
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHIH', self.type, self.stream_id, self.frame_id, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ChecksumFrame.Header':
            type, stream_id, frame_id, payload_length = struct.unpack(
                '<BHIH', header_bytes)
            return cls(type, stream_id, frame_id, payload_length)

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

    def __init__(self, type: int, stream_id: int, frame_id: int, payload_length: int, payload: str) -> None:

        self.header = self.Header(
            type, stream_id, frame_id, payload_length)
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ChecksumFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        return cls(header.type, header.stream_id, header.frame_id, header.payload_length, payload.data)


class StatFrame(Frame):
    type = 10

    class Header(Frame.Header):
        size = struct.calcsize('<BHIH')

        def __init__(self, type: int, stream_id: int, frame_id: int, payload_length: int) -> None:
            self.type = type
            self.stream_id = stream_id
            self.frame_id = frame_id
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHIH', self.type, self.stream_id, self.frame_id, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'StatFrame.Header':
            type, stream_id, frame_id, payload_length = struct.unpack(
                '<BHIH', header_bytes)
            return cls(type, stream_id, frame_id, payload_length)

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

    def __init__(self, type: int, stream_id: int, frame_id: int, payload_length: int, payload: str) -> None:

        self.header = self.Header(
            type, stream_id, frame_id, payload_length)
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'StatFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        return cls(header.type, header.stream_id, header.frame_id, header.payload_length, payload.data)


class ListFrame(Frame):
    type = 11

    class Header(Frame.Header):
        size = struct.calcsize('<BHIH')

        def __init__(self, type: int, stream_id: int, frame_id: int, payload_length: int) -> None:
            self.type = type
            self.stream_id = stream_id
            self.frame_id = frame_id
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHIH', self.type, self.stream_id, self.frame_id, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ListFrame.Header':
            type, stream_id, frame_id, payload_length = struct.unpack(
                '<BHIH', header_bytes)
            return cls(type, stream_id, frame_id, payload_length)

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

    def __init__(self, type: int, stream_id: int, frame_id: int, payload_length: int, payload: str) -> None:

        self.header = self.Header(
            type, stream_id, frame_id, payload_length)
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ListFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        return cls(header.type, header.stream_id, header.frame_id, header.payload_length, payload.data)
