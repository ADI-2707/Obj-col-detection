from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
import supervision as sv

from mill_motion.config import Config
from mill_motion.pipeline import Pipeline


@pytest.fixture
def headless_config(tmp_path):
    return Config(
        source="fake.mp4",
        model_path="yolov8n.pt",
        output_dir=tmp_path / "logs",
        display=False,
    )


class TestPipelineConstruction:
    @patch("mill_motion.pipeline.Detector")
    def test_constructs_all_components(self, mock_detector_cls, headless_config):
        mock_detector_cls.return_value = MagicMock()
        pipeline = Pipeline(headless_config)
        assert pipeline._frame_source is not None
        assert pipeline._tracker is not None
        assert pipeline._motion is not None
        assert pipeline._logger is not None
        assert pipeline._visualizer is None


class TestPipelineProcessFrame:
    @patch("mill_motion.pipeline.Detector")
    def test_process_frame_empty_detections(self, mock_detector_cls, headless_config):
        mock_detector = MagicMock()
        mock_detector.detect.return_value = sv.Detections.empty()
        mock_detector_cls.return_value = mock_detector

        pipeline = Pipeline(headless_config)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        tracker_ids, class_ids, confs, bboxes = pipeline._process_frame(frame)

        assert tracker_ids == []
        assert class_ids == []
        assert confs == []
        assert bboxes == []

    @patch("mill_motion.pipeline.Detector")
    def test_process_frame_with_detections(self, mock_detector_cls, headless_config):
        detections = sv.Detections(
            xyxy=np.array([[10, 20, 50, 60]], dtype=np.float32),
            confidence=np.array([0.9], dtype=np.float32),
            class_id=np.array([0], dtype=int),
        )

        mock_detector = MagicMock()
        mock_detector.detect.return_value = detections
        mock_detector._model.names = {0: "person"}
        mock_detector_cls.return_value = mock_detector

        pipeline = Pipeline(headless_config)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        tracker_ids, class_ids, confs, bboxes = pipeline._process_frame(frame)

        assert len(tracker_ids) == 1
        assert len(bboxes) == 1


class TestPipelineSourceError:
    @patch("mill_motion.pipeline.Detector")
    def test_run_with_invalid_source_prints_error(
        self, mock_detector_cls, headless_config, capsys
    ):
        mock_detector_cls.return_value = MagicMock()
        pipeline = Pipeline(headless_config)
        pipeline.run()
        captured = capsys.readouterr()
        assert "ERROR" in captured.err or "Failed" in captured.err


class TestCLIParsing:
    def test_default_args(self):
        from mill_motion.__main__ import parse_args

        args = parse_args([])
        assert args.source == "0"
        assert args.model == "yolov8n.pt"
        assert args.confidence == 0.25
        assert args.no_display is False
        assert args.windowed is False

    def test_custom_args(self):
        from mill_motion.__main__ import parse_args

        args = parse_args([
            "--source", "video.mp4",
            "--model", "custom.pt",
            "--confidence", "0.5",
            "--no-display",
            "--windowed",
        ])
        assert args.source == "video.mp4"
        assert args.model == "custom.pt"
        assert args.confidence == 0.5
        assert args.no_display is True
        assert args.windowed is True

    def test_source_parsing_integer(self):
        from mill_motion.__main__ import _parse_source

        assert _parse_source("0") == 0
        assert _parse_source("2") == 2

    def test_source_parsing_string(self):
        from mill_motion.__main__ import _parse_source

        assert _parse_source("video.mp4") == "video.mp4"
