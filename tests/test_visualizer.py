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


class TestVisualizerComposeDashboard:
    def test_default_canvas_dimensions(self):
        vis = Visualizer()
        frame = _blank_frame()
        dash = vis.compose_dashboard(
            annotated_frame=frame,
            tracker_ids=[],
            class_ids=[],
            confidences=[],
            bboxes=[],
            motion_states={},
            frame_number=0,
        )
        assert dash.shape == (1080, 1920, 3)

    def test_custom_canvas_dimensions(self):
        vis = Visualizer()
        frame = _blank_frame()
        dash = vis.compose_dashboard(
            annotated_frame=frame,
            tracker_ids=[],
            class_ids=[],
            confidences=[],
            bboxes=[],
            motion_states={},
            frame_number=0,
            canvas_width=1280,
            canvas_height=720,
        )
        assert dash.shape == (720, 1280, 3)

    def test_dashboard_with_single_target(self):
        vis = Visualizer()
        frame = _blank_frame()
        dash = vis.compose_dashboard(
            annotated_frame=frame,
            tracker_ids=[1],
            class_ids=[0],
            confidences=[0.95],
            bboxes=[(50.0, 50.0, 150.0, 200.0)],
            motion_states={1: MotionState(12.0, 90.0, [(100.0, 125.0)])},
            frame_number=42,
            class_names={0: "person"},
        )
        assert dash.shape == (1080, 1920, 3)
        assert not np.array_equal(dash, np.zeros_like(dash))

    def test_dashboard_with_multiple_targets(self):
        vis = Visualizer()
        frame = _blank_frame()
        dash = vis.compose_dashboard(
            annotated_frame=frame,
            tracker_ids=[1, 2],
            class_ids=[0, 1],
            confidences=[0.92, 0.88],
            bboxes=[(50.0, 50.0, 100.0, 100.0), (120.0, 120.0, 180.0, 180.0)],
            motion_states={
                1: MotionState(8.0, 45.0, [(75.0, 75.0)]),
                2: MotionState(5.0, 225.0, [(150.0, 150.0)]),
            },
            frame_number=100,
            class_names={0: "person", 1: "cart"},
        )
        assert dash.shape == (1080, 1920, 3)


class TestVisualizerTheme:
    def test_theme_color_palette(self):
        vis = Visualizer()
        assert vis.COLOR_BG == (255, 255, 255)
        assert vis.COLOR_PANEL_BG == (255, 255, 255)
        assert vis.COLOR_TEXT_MAIN == (15, 20, 28)
        assert vis.COLOR_LOGO_BLUE == (120, 55, 16)
        assert vis.COLOR_LOGO_GREEN == (30, 165, 55)
        assert vis.COLOR_ALERT == (20, 20, 225)

    def test_dashboard_renders_white_background(self):
        vis = Visualizer()
        frame = _blank_frame()
        dash = vis.compose_dashboard(
            annotated_frame=frame,
            tracker_ids=[],
            class_ids=[],
            confidences=[],
            bboxes=[],
            motion_states={},
            frame_number=0,
        )
        assert tuple(dash[0, 0].tolist()) == (255, 255, 255)
