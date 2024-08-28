import struct
from frame.frame import Frame


class AckFrame(Frame):
    type = 0

    class Header(Frame.Header):
        size = struct.calcsize('<BI')

        def __init__(self, packet_id: int) -> None:
            self.type = AckFrame.type
            self.packet_id = packet_id

        def pack(self) -> bytes:
            return struct.pack('<BI', self.type, self.packet_id)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'AckFrame.Header':
            type, packet_id = struct.unpack('<BI', header_bytes)
            if type != AckFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {AckFrame.type})')
            return cls(packet_id)

    def __init__(self, stream_id: int) -> None:
        self.header = self.Header(self.type, stream_id)

    def __len__(self) -> int:
        return len(self.header)

    def pack(self) -> bytes:
        return self.header.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'AckFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        return cls(header.type, header.stream_id)


class ExitFrame(Frame):
    type = 1

    class Header(Frame.Header):
        size = struct.calcsize('<B')

        def __init__(self) -> None:
            self.type = ExitFrame.type

        def pack(self) -> bytes:
            return struct.pack('<B', self.type)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ExitFrame.Header':
            type = struct.unpack('<B', header_bytes)
            if type != ExitFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {ExitFrame.type})')
            return cls()

    def __init__(self) -> None:
        self.header = self.Header(self.type)

    def __len__(self) -> int:
        return len(self.header)

    def pack(self) -> bytes:
        return self.header.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ExitFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        return cls(header.type)


class ConnectionIDChangeFrame(Frame):
    type = 2

    class Header(Frame.Header):
        size = struct.calcsize('<BII')

        def __init__(self, old_connection_id: int, new_connection_id: int) -> None:
            self.type = ConnectionIDChangeFrame.type
            self.old_connection_id = old_connection_id
            self.new_connection_id = new_connection_id

        def pack(self) -> bytes:
            return struct.pack('<BII', self.type, self.old_connection_id, self.new_connection_id)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ConnectionIDChangeFrame.Header':
            type, old_connection_id, new_connection_id = struct.unpack(
                '<BII', header_bytes)
            if type != ConnectionIDChangeFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {ConnectionIDChangeFrame.type})')
            return cls(old_connection_id, new_connection_id)

    def __init__(self, old_connection_id: int, new_connection_id: int) -> None:
        self.header = self.Header(self.type, old_connection_id, new_connection_id)

    def __len__(self) -> int:
        return len(self.header)

    def pack(self) -> bytes:
        return self.header.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ConnectionIDChangeFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        return cls(header.type, header.old_connection_id, header.new_connection_id)


class FlowControlFrame(Frame):
    type = 3

    class Header(Frame.Header):
        size = struct.calcsize('<BI')

        def __init__(self, window_size: int) -> None:
            self.type = FlowControlFrame.type
            self.window_size = window_size

        def pack(self) -> bytes:
            return struct.pack('<BI', self.type, self.window_size)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'FlowControlFrame.Header':
            type, window_size = struct.unpack('<BI', header_bytes)
            if type != FlowControlFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {FlowControlFrame.type})')
            return cls(window_size)

    def __init__(self, window_size: int) -> None:
        self.header = self.Header(self.type, window_size)

    def __len__(self) -> int:
        return len(self.header)

    def pack(self) -> bytes:
        return self.header.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'FlowControlFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        return cls(header.type, header.window_size)


class AnswerFrame(Frame):
    type = 4

    class Header(Frame.Header):
        size = struct.calcsize('<BHH')

        def __init__(self, stream_id: int, payload_length: int) -> None:
            self.type = AnswerFrame.type
            self.stream_id = stream_id
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHH', self.type, self.stream_id, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'AnswerFrame.Header':
            type, stream_id, payload_length = struct.unpack(
                '<BHH', header_bytes)
            if type != AnswerFrame.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {AnswerFrame.type})')
            return cls(stream_id, payload_length)

    class Payload(Frame.Payload):

        def __init__(self, payload: bytes) -> None:
            self.data = payload

        def __len__(self) -> int:
            return len(self.data)

        def pack(self) -> bytes:
            return self.data

        @classmethod
        def unpack(cls, payload_bytes: bytes) -> 'AnswerFrame.Payload':
            return cls(payload_bytes)

    def __init__(self, stream_id: int, payload: bytes) -> None:
        self.header = self.Header(self.type, stream_id, len(payload))
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'AnswerFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        if len(payload) != header.payload_length:
            raise ValueError(
                f'Invalid payload length: {len(payload)} (expected {header.payload_length})')
        return cls(header.type, header.stream_id, payload.data)


class ErrorFrame(Frame):
    type = 5

    class Header(Frame.Header):
        size = struct.calcsize('<BHH')

        def __init__(self, stream_id: int, payload_length: int) -> None:
            self.type = ErrorFrame.type
            self.stream_id = stream_id
            self.payload_length = payload_length

        def pack(self) -> bytes:
            return struct.pack('<BHH', self.type, self.stream_id, self.payload_length)

        @classmethod
        def unpack(cls, header_bytes: bytes) -> 'ErrorFrame.Header':
            type, stream_id, payload_length = struct.unpack(
                '<BHH', header_bytes)
            if type != cls.type:
                raise ValueError(
                    f'Invalid header type: {type} (expected {cls.type})')
            return cls(stream_id, payload_length)

    class Payload(Frame.Payload):

        def __init__(self, message: str) -> None:
            self.data = message

        def __len__(self) -> int:
            return len(self.data)

        def pack(self) -> bytes:
            return bytes(self.data, 'utf-8')

        @classmethod
        def unpack(cls, payload_bytes: bytes) -> 'ErrorFrame.Payload':
            return cls(str(payload_bytes, 'utf-8'))

    def __init__(self, stream_id: int, payload: str) -> None:
        self.header = self.Header(stream_id, len(payload))
        self.payload = self.Payload(payload)

    def __len__(self) -> int:
        return len(self.header) + len(self.payload)

    def pack(self) -> bytes:
        return self.header.pack() + self.payload.pack()

    @classmethod
    def unpack(cls, frame_bytes: bytes) -> 'ErrorFrame':
        header = cls.Header.unpack(frame_bytes[:cls.Header.size])
        payload = cls.Payload.unpack(frame_bytes[cls.Header.size:])
        if len(payload) != header.payload_length:
            raise ValueError(
                f'Invalid payload length: {len(payload)} (expected {header.payload_length})')
        return cls(header.type, header.stream_id, payload.data)
