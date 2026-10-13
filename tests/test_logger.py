import csv
from pathlib import Path

import pytest

from orbix.logger import CSVLogger
from orbix.motion import MotionState


@pytest.fixture
def log_dir(tmp_path):
    return tmp_path / "test_logs"


class TestCSVLoggerCreation:
    def test_creates_output_directory(self, log_dir):
        logger = CSVLogger(output_dir=log_dir)
        logger.open()
        logger.close()
        assert log_dir.exists()

    def test_creates_csv_file(self, log_dir):
        logger = CSVLogger(output_dir=log_dir)
        logger.open()
        logger.close()
        assert logger.filepath.exists()


class TestCSVLoggerHeader:
    def test_header_row_matches_fieldnames(self, log_dir):
        with CSVLogger(output_dir=log_dir) as logger:
            pass
        with open(logger.filepath, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader)
        assert header == CSVLogger.FIELDNAMES


class TestCSVLoggerDataRow:
    def test_writes_track_data(self, log_dir):
        motion = {1: MotionState(velocity_px=5.5, direction_deg=45.0, trail=[])}
        with CSVLogger(output_dir=log_dir) as logger:
            logger.log_frame(
                frame_number=0,
                tracker_ids=[1],
                class_ids=[0],
                confidences=[0.85],
                bboxes=[(10.0, 20.0, 30.0, 40.0)],
                motion_states=motion,
            )

        with open(logger.filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 1
        assert rows[0]["track_id"] == "1"
        assert rows[0]["velocity_px_per_frame"] == "5.50"
        assert rows[0]["direction_deg"] == "45.0"

    def test_writes_multiple_tracks_per_frame(self, log_dir):
        motion = {
            1: MotionState(velocity_px=2.0, direction_deg=0.0, trail=[]),
            2: MotionState(velocity_px=3.0, direction_deg=90.0, trail=[]),
        }
        with CSVLogger(output_dir=log_dir) as logger:
            logger.log_frame(
                frame_number=0,
                tracker_ids=[1, 2],
                class_ids=[0, 1],
                confidences=[0.9, 0.8],
                bboxes=[(0, 0, 10, 10), (20, 20, 30, 30)],
                motion_states=motion,
            )

        with open(logger.filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2


class TestCSVLoggerContextManager:
    def test_context_manager_closes_file(self, log_dir):
        with CSVLogger(output_dir=log_dir) as logger:
            pass
        assert logger._file is None
