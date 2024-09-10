import pathlib
import zlib
import json


class Stream:
    def __init__(self, stream_id: int, path: str):
        self.stream_id = stream_id
        if not pathlib.Path(path).exists():
            raise FileNotFoundError(f"File {path} not found")
        self.path = path
        self.file = open(path, "r+b")
        # TODO: file checksum calculation
        self.checksum = 0
        self.frames_so_far = []  # for debugging

    def __repr__(self):
        return json.dumps({
            "stream_id": self.stream_id,
            "path": self.path,
            "checksum": self.checksum
        }, indent=4)

    def __str__(self) -> str:
        return self.__repr__()

    def __del__(self):
        self.file.close()

    @classmethod
    def open(cls, stream_id: int, path: str):
        open(path, "w+b").close()
        return cls(stream_id, path)

    def close(self):
        self.file.close()
        # if the file is empty, delete it
        print(f"File size: {self.get_file_size()}")
        if self.get_file_size() == 0:
            pathlib.Path(self.path).unlink()

    def get_file_size(self) -> int:
        return pathlib.Path(self.path).stat().st_size

    def get_file_checksum(self) -> int:
        return zlib.crc32(self.file.read())

    def get_file_name(self) -> str:
        return pathlib.Path(self.path).name
