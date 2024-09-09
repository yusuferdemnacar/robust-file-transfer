import abc
import json
from typing import Self


class Frame(abc.ABC):
    type = ...

    class Header(abc.ABC):
        size = ...

        def __repr__(self) -> str:
            return json.dumps(self.to_dict(), indent=4)

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

        def to_dict(self):
            return {key: (value.hex() if isinstance(value, bytes) else value)
                    for key, value in self.__dict__.items()}

    class Payload(abc.ABC):

        def __repr__(self) -> str:
            return json.dumps(self.to_dict(), indent=4)

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

        def to_dict(self):
            return {key: (value.hex() if isinstance(value, bytes) else value)
                    for key, value in self.__dict__.items()}

    def __repr__(self) -> str:
        return json.dumps(self.to_dict(), indent=4)

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

    def to_dict(self):
        if hasattr(self, "payload"):
            return {"header": self.header.to_dict(), "payload": self.payload.to_dict()}
        else:
            return {"header": self.header.to_dict()}
