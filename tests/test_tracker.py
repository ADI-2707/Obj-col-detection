import numpy as np
import supervision as sv

from vision.tracker import ObjectTracker


class TestObjectTrackerInit:
    def test_default_construction(self):
        tracker = ObjectTracker()
        assert tracker._tracker is not None

    def test_custom_buffer_length(self):
        tracker = ObjectTracker(track_buffer_length=60)
        assert tracker._tracker is not None


class TestObjectTrackerUpdate:
    def test_empty_detections_passthrough(self):
        tracker = ObjectTracker()
        empty = sv.Detections.empty()
        result = tracker.update(empty)
        assert len(result) == 0

    def test_detections_get_tracker_ids(self):
        tracker = ObjectTracker()
        detections = sv.Detections(
            xyxy=np.array([[10, 20, 50, 60]], dtype=np.float32),
            confidence=np.array([0.9], dtype=np.float32),
            class_id=np.array([0], dtype=int),
        )
        result = tracker.update(detections)
        assert result.tracker_id is not None
        assert len(result.tracker_id) == 1


class TestObjectTrackerReset:
    def test_reset_does_not_raise(self):
        tracker = ObjectTracker()
        tracker.reset()
