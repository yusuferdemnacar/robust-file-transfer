import pathlib
import common.util as util
import json
from frame import *

class Stream:
    def __init__(self, stream_id: int, path: str, direction=None):
        self.stream_id = stream_id
        if not pathlib.Path(path).exists():
            raise FileNotFoundError(f"File {path} not found")
        self.path = path
        self.file = open(path, "a+b")
        # TODO: file checksum calculation
        self.frames_so_far = []  # for debugging
        self.next_offset = 0
        self.payload_size = 128
        self.is_closed = False
        self.direction = direction

    def __repr__(self):
        return json.dumps({
            "stream_id": self.stream_id,
            "path": self.path,
        }, indent=4)

    def __str__(self) -> str:
        return self.__repr__()

    def __del__(self):
        self.file.close()

    @classmethod
    def open(cls, stream_id: int, path: str, direction=None):
        open(path, "a+b").close()
        return cls(stream_id, path, direction)

    def close(self):
        if self.is_closed:
            return
        self.file.close()
        self.is_closed = True
        # if the file is empty, delete it
        if self.get_file_size() == 0:
            pathlib.Path(self.path).unlink()

    def flush(self):
        self.file.flush()

    def get_file_size(self) -> int:
        return pathlib.Path(self.path).stat().st_size

    def get_file_checksum(self) -> str:
        return util.sha256_file_checksum(self.path)

    def get_file_name(self) -> str:
        return pathlib.Path(self.path).name
    
    def get_next_data_frame(self) -> DataFrame:
        if self.is_closed or self.direction == "r":
            return None
        self.file.seek(self.next_offset)
        # print(f"Reading {self.payload_size} bytes from {self.next_offset}")
        data = self.file.read(self.payload_size)
        if not data:
            self.close()
            return DataFrame(self.stream_id, self.next_offset, b"")
        frame = DataFrame(self.stream_id, self.next_offset, data)
        self.next_offset += len(data)
        self.frames_so_far.append(frame)
        return frame
    
    def remove_file(self):
        pathlib.Path(self.path).unlink()
