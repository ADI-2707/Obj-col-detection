import pytest

from mill_motion.capture import FrameSource, FrameSourceError


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
