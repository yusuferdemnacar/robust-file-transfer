import pathlib
import zlib

class Stream:
    def __init__(self, stream_id: int, path: str):
        self.stream_id = stream_id
        if not pathlib.Path(path).exists():
            raise FileNotFoundError(f"File {path} not found")
        self.path = path
        self.file_size = pathlib.Path(path).stat().st_size
        self.file_name = pathlib.Path(path).name
        self.file = open(path, "rb")
        # TODO: file checksum calculation
        self.checksum = 0
        self.frames_so_far = [] # for debugging
