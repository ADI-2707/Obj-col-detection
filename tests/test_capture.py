import pytest

from orbix.capture import FrameSource, FrameSourceError


class TestFrameSourceErrors:
    def test_invalid_file_path_raises(self):
        source = FrameSource("nonexistent_video_file_12345.mp4")
        with pytest.raises(FrameSourceError, match="file"):
            source.open()

    def test_read_before_open_raises(self):
        source = FrameSource(0)
        with pytest.raises(FrameSourceError, match="not open"):
            source.read()


class TestFrameSourceContextManager:
    def test_release_sets_capture_to_none(self):
        source = FrameSource("nonexistent.mp4")
        source._capture = None
        source.release()
        assert source._capture is None

    def test_exit_calls_release(self):
        source = FrameSource(0)
        source._capture = None
        source.__exit__(None, None, None)
        assert source._capture is None


class TestFrameSourceProperties:
    def test_fps_before_open_returns_zero(self):
        source = FrameSource(0)
        assert source.fps == 0.0

    def test_frame_size_before_open_returns_zero(self):
        source = FrameSource(0)
        assert source.frame_size == (0, 0)

    def test_camera_fallback_attempts(self, monkeypatch):
        import cv2
        calls = []

        class MockCapture:
            def isOpened(self):
                return False
            def release(self):
                pass

        def mock_videocapture(idx, *args):
            calls.append((idx, args))
            return MockCapture()

        monkeypatch.setattr(cv2, "VideoCapture", mock_videocapture)
        source = FrameSource(0)
        with pytest.raises(FrameSourceError):
            source.open()
        assert len(calls) == 3

    def test_camera_negotiates_1080p_resolution(self, monkeypatch):
        import cv2
        set_calls = []

        class MockOpenedCapture:
            def isOpened(self):
                return True
            def set(self, prop, val):
                set_calls.append((prop, val))
                return True
            def read(self):
                import numpy as np
                return True, np.zeros((480, 640, 3), dtype=np.uint8)
            def release(self):
                pass

        monkeypatch.setattr(cv2, "VideoCapture", lambda *args, **kwargs: MockOpenedCapture())
        source = FrameSource(0)
        source.open()
        assert (cv2.CAP_PROP_FRAME_WIDTH, 1920) in set_calls
        assert (cv2.CAP_PROP_FRAME_HEIGHT, 1080) in set_calls
        source.release()
