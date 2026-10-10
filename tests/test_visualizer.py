import numpy as np

from mill_motion.motion import MotionState
from mill_motion.visualizer import Visualizer


def _blank_frame(width=640, height=480):
    return np.zeros((height, width, 3), dtype=np.uint8)


class TestVisualizerAnnotate:
    def test_returns_frame_with_same_shape(self):
        vis = Visualizer()
        frame = _blank_frame()
        result = vis.annotate(
            frame=frame,
            tracker_ids=[1],
            class_ids=[0],
            confidences=[0.9],
            bboxes=[(10.0, 20.0, 100.0, 200.0)],
            motion_states={1: MotionState(5.0, 45.0, [(55.0, 110.0)])},
            frame_number=0,
        )
        assert result.shape == frame.shape

    def test_does_not_modify_original_frame(self):
        vis = Visualizer()
        frame = _blank_frame()
        original = frame.copy()
        vis.annotate(
            frame=frame,
            tracker_ids=[1],
            class_ids=[0],
            confidences=[0.9],
            bboxes=[(10.0, 20.0, 100.0, 200.0)],
            motion_states={1: MotionState(5.0, 45.0, [(55.0, 110.0)])},
            frame_number=0,
        )
        assert np.array_equal(frame, original)

    def test_empty_detections_returns_valid_frame(self):
        vis = Visualizer()
        frame = _blank_frame()
        result = vis.annotate(
            frame=frame,
            tracker_ids=[],
            class_ids=[],
            confidences=[],
            bboxes=[],
            motion_states={},
            frame_number=0,
        )
        assert result.shape == frame.shape

    def test_annotated_frame_differs_from_blank(self):
        vis = Visualizer()
        frame = _blank_frame()
        result = vis.annotate(
            frame=frame,
            tracker_ids=[1],
            class_ids=[0],
            confidences=[0.9],
            bboxes=[(10.0, 20.0, 100.0, 200.0)],
            motion_states={1: MotionState(5.0, 45.0, [(55.0, 110.0)])},
            frame_number=0,
        )
        assert not np.array_equal(result, np.zeros_like(result))


class TestVisualizerTrail:
    def test_trail_with_multiple_points_renders(self):
        vis = Visualizer()
        frame = _blank_frame()
        trail = [(50.0, 100.0), (60.0, 100.0), (70.0, 100.0)]
        result = vis.annotate(
            frame=frame,
            tracker_ids=[1],
            class_ids=[0],
            confidences=[0.9],
            bboxes=[(40.0, 90.0, 80.0, 110.0)],
            motion_states={1: MotionState(10.0, 0.0, trail)},
            frame_number=5,
        )
        assert result.shape == frame.shape
