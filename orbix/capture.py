import cv2
import numpy as np


class FrameSourceError(Exception):
    pass


class FrameSource:
    def __init__(self, source: int | str):
        self._source = source
        self._capture = None

    def open(self):
        if isinstance(self._source, int):
            self._capture = cv2.VideoCapture(self._source, cv2.CAP_DSHOW)
            if not self._capture.isOpened():
                self._capture = cv2.VideoCapture(self._source, cv2.CAP_MSMF)
            if not self._capture.isOpened():
                self._capture = cv2.VideoCapture(self._source)
            if self._capture.isOpened():
                for _ in range(3):
                    self._capture.read()
        else:
            self._capture = cv2.VideoCapture(self._source)

        if not self._capture.isOpened():
            source_desc = (
                f"camera index {self._source}"
                if isinstance(self._source, int)
                else f"file '{self._source}'"
            )
            raise FrameSourceError(
                f"Failed to open {source_desc}. "
                f"Verify the device is connected or the file path is correct."
            )

    def read(self) -> np.ndarray:
        if self._capture is None:
            raise FrameSourceError(
                "FrameSource is not open. Call open() or use as a context manager."
            )

        success, frame = self._capture.read()
        if not success and isinstance(self._source, int):
            for _ in range(2):
                success, frame = self._capture.read()
                if success:
                    break

        if not success or frame is None:
            raise StopIteration

        return frame

    def release(self):
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    @property
    def fps(self) -> float:
        if self._capture is None:
            return 0.0
        return self._capture.get(cv2.CAP_PROP_FPS) or 30.0

    @property
    def frame_size(self) -> tuple[int, int]:
        if self._capture is None:
            return (0, 0)
        w = int(self._capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self._capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (w, h)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.release()
        return False

    def __iter__(self):
        return self

    def __next__(self) -> np.ndarray:
        return self.read()
