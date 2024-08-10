from frame import Frame


class DataFrame(Frame):

    class Header(Frame.Header):

        def __init__(self, type: int, stream_id: int, frame_id: int, offset: int, length: int) -> None:
            super().__init__(type)
            self.stream_id = stream_id
            self.frame_id = frame_id
            self.offset = offset
            self.length = length
