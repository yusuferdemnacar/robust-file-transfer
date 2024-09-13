import pathlib
import common.util as util
import json


class Stream:
    def __init__(self, stream_id: int, path: str):
        self.stream_id = stream_id
        if not pathlib.Path(path).exists():
            raise FileNotFoundError(f"File {path} not found")
        self.path = path
        self.file = open(path, "a+b")
        # TODO: file checksum calculation
        self.frames_so_far = []  # for debugging
        self.is_closed = False

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
    def open(cls, stream_id: int, path: str):
        open(path, "a+b").close()
        return cls(stream_id, path)

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

    def remove_file(self):
        pathlib.Path(self.path).unlink()
