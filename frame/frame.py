import abc
from typing import Self


class Frame(abc.ABC):
    type = ...

    class Header(abc.ABC):
        size = ...

        def __repr__(self) -> str:
            fields = ', '.join(f'{key}={value}' for key,
                               value in self.__dict__.items())
            return f'{self.__class__.__name__}({fields})'

        def __str__(self) -> str:
            return self.__repr__()

        def __len__(self) -> int:
            return self.size

        @abc.abstractmethod
        def pack(self) -> bytes:
            ...

        @classmethod
        @abc.abstractmethod
        def unpack(cls, header_bytes: bytes) -> Self:
            ...

    class Payload(abc.ABC):

        def __repr__(self) -> str:
            fields = ', '.join(f'{key}={value}' for key,
                               value in self.__dict__.items())
            return f'{self.__class__.__name__}({fields})'

        def __str__(self) -> str:
            return self.__repr__()

        @abc.abstractmethod
        def __len__(self) -> int:
            ...

        @abc.abstractmethod
        def pack(self) -> bytes:
            ...

        @classmethod
        @abc.abstractmethod
        def unpack(cls, payload_bytes: bytes) -> Self:
            ...

    @property
    def frameType(self):
        return self.header.type

    def __repr__(self) -> str:
        fields = ', '.join(f'{key}={value}' for key,
                           value in self.__dict__.items())
        return f'{self.__class__.__name__}({fields})'

    def __str__(self) -> str:
        return self.__repr__()

    @abc.abstractmethod
    def __len__(self) -> int:
        ...

    @abc.abstractmethod
    def pack(self) -> bytes:
        ...

    @classmethod
    @abc.abstractmethod
    def unpack(cls, frame_bytes: bytes) -> Self:
        ...
