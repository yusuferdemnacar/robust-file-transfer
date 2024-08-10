import struct


class Packet:

    class Header:

        def __init__(self, version: int, connection_id: int, checksum: int):
            self.version = version
            self.connection_id = connection_id
            self.checksum = checksum

        def pack(self) -> bytes:
            return struct.pack('!BI3s', *self.__dict__.values())

        @classmethod
        def unpack(cls, data: bytes):
            return cls(*struct.unpack('!BI3s', data))

        def __repr__(self):
            fields = ', '.join(f'{key}={value}' for key,
                               value in self.__dict__.items())
            return f'{self.__class__.__name__}({fields})'
