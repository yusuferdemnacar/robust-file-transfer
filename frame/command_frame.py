from frame import Frame
import struct


class CommandFrame(Frame):

    class Header(Frame.Header):

        def __init__(self, type: int, stream_id: int, frame_id: int) -> None:
            super().__init__(type)
            self.stream_id = stream_id
            self.frame_id = frame_id

    class Payload(Frame.Payload):

        def __init__(self, path: str):
            self.path = path

        def pack(self) -> bytes:
            super().pack('!{}s'.format(len(self.path)), self.path.encode('utf-8'))

        @classmethod
        def unpack(cls, data: bytes) -> 'CommandFrame.Payload':
            super().unpack(data, '!{}s'.format(len(data)))

    def __init__(self, header: Header, payload: Payload) -> None:
        super().__init__(header, payload)


class ReadCommandFrame(CommandFrame):

    class Header(CommandFrame.Header):
        TYPE = 0x01

        def __init__(self, stream_id: int, frame_id: int, checksum_check_flag: bool, offset: int, length: int, checksum: int) -> None:
            super().__init__(self.TYPE, stream_id, frame_id)
            self.checksum_check_flag = int(checksum_check_flag)
            self.offset = offset
            self.length = length
            self.checksum = checksum

        def pack(self) -> bytes:
            return super().pack()

        @classmethod
        def unpack(cls, data: bytes) -> 'ReadCommandFrame.Header':
            return super().unpack('!BHIB6s6sI', data)

    TYPE = 0x01

    def __init__(self, stream_id: int, frame_id: int, path: str) -> None:
        super().__init__(self.TYPE, stream_id, frame_id)
        self.payload = self.Payload(path)

    def pack(self) -> bytes:
        return super().pack() + self.payload.pack()

    @classmethod
    def unpack(cls, data: bytes) -> 'ReadCommandFrame':
        header = cls.Header.unpack(data[:7])
        payload = cls.Payload.unpack(data[7:])
        return cls(header.stream_id, header.frame_id, payload.path)
