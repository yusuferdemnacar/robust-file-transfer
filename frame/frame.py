import struct


class Frame:

    class Header:

        def __init__(self, type: int, size: int) -> None:
            self.type = type

        def pack(self, format_string: str) -> bytes:
            return struct.pack(format_string, *self.__dict__.values())

        @classmethod
        def unpack(cls, data: bytes, format_string: str) -> 'Frame.Header':
            return cls(*struct.unpack(format_string, data))

        def __repr__(self):
            fields = ', '.join(f'{key}={value}' for key,
                               value in self.__dict__.items())
            return f'{self.__class__.__name__}({fields})'

    class Payload:

        def __init__(self):
            pass

        def pack(self, format_string: str) -> bytes:
            return struct.pack(format_string, *self.__dict__.values())

        @classmethod
        def unpack(cls, data: bytes, format_string: str) -> 'Frame.Payload':
            return cls(*struct.unpack(format_string, data))

        def __repr__(self):
            fields = ', '.join(f'{key}={value}' for key,
                               value in self.__dict__.items())
            return f'{self.__class__.__name__}({fields})'

    def __init__(self, header: Header, payload: Payload) -> None:
        self.header = header
        self.payload = payload

    def pack(self, header_format_string: str, payload_format_string: str) -> bytes:
        return self.header.pack(header_format_string) + self.payload.pack(payload_format_string)

    @classmethod
    def unpack(cls, data: bytes, header_format_string: str, payload_format_string: str) -> 'Frame':
        header_size = struct.calcsize(header_format_string)
        header = cls.Header.unpack(data[:header_size], header_format_string)
        payload = cls.Payload.unpack(data[header_size:], payload_format_string)
        return cls(header, payload)

    def __repr__(self):
        return f'{self.__class__.__name__}({self.header}, {self.payload})'
