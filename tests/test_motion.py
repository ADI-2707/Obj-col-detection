import math

from orbix.motion import MotionEstimator, MotionState


class TestMotionEstimatorStationary:
    def test_first_frame_zero_velocity(self):
        estimator = MotionEstimator()
        result = estimator.update(
            tracker_ids=[1],
            bboxes=[(10.0, 20.0, 30.0, 40.0)],
        )
        assert result[1].velocity_px == 0.0

    def test_same_position_converges_to_zero(self):
        estimator = MotionEstimator(ema_alpha=0.5)
        bbox = (10.0, 20.0, 30.0, 40.0)
        for _ in range(20):
            result = estimator.update(tracker_ids=[1], bboxes=[bbox])
        assert result[1].velocity_px < 0.01


class TestMotionEstimatorMoving:
    def test_rightward_motion_positive_velocity(self):
        estimator = MotionEstimator(ema_alpha=1.0)
        estimator.update(tracker_ids=[1], bboxes=[(0, 0, 10, 10)])
        result = estimator.update(tracker_ids=[1], bboxes=[(10, 0, 20, 10)])
        assert result[1].velocity_px > 0

    def test_rightward_direction_near_zero_degrees(self):
        estimator = MotionEstimator(ema_alpha=1.0)
        estimator.update(tracker_ids=[1], bboxes=[(0, 0, 10, 10)])
        result = estimator.update(tracker_ids=[1], bboxes=[(10, 0, 20, 10)])
        assert abs(result[1].direction_deg) < 1.0

    def test_downward_direction_near_ninety_degrees(self):
        estimator = MotionEstimator(ema_alpha=1.0)
        estimator.update(tracker_ids=[1], bboxes=[(0, 0, 10, 10)])
        result = estimator.update(tracker_ids=[1], bboxes=[(0, 10, 10, 20)])
        assert abs(result[1].direction_deg - 90.0) < 1.0


class TestMotionEstimatorTrail:
    def test_trail_grows_with_frames(self):
        estimator = MotionEstimator()
        estimator.update(tracker_ids=[1], bboxes=[(0, 0, 10, 10)])
        estimator.update(tracker_ids=[1], bboxes=[(5, 0, 15, 10)])
        result = estimator.update(tracker_ids=[1], bboxes=[(10, 0, 20, 10)])
        assert len(result[1].trail) == 3

    def test_trail_capped_at_trail_length(self):
        estimator = MotionEstimator(trail_length=3)
        for i in range(10):
            result = estimator.update(
                tracker_ids=[1],
                bboxes=[(i * 5, 0, i * 5 + 10, 10)],
            )
        assert len(result[1].trail) == 3


class TestMotionEstimatorPruning:
    def test_stale_track_pruned(self):
        estimator = MotionEstimator(stale_track_frames=2)
        estimator.update(tracker_ids=[1], bboxes=[(0, 0, 10, 10)])
        estimator.update(tracker_ids=[], bboxes=[])
        estimator.update(tracker_ids=[], bboxes=[])
        estimator.update(tracker_ids=[], bboxes=[])
        assert 1 not in estimator._tracks

    def test_active_track_not_pruned(self):
        estimator = MotionEstimator(stale_track_frames=5)
        for _ in range(10):
            estimator.update(tracker_ids=[1], bboxes=[(0, 0, 10, 10)])
        assert 1 in estimator._tracks


class TestMotionEstimatorReset:
    def test_reset_clears_all_tracks(self):
        estimator = MotionEstimator()
        estimator.update(tracker_ids=[1, 2], bboxes=[(0, 0, 10, 10), (20, 20, 30, 30)])
        estimator.reset()
        assert len(estimator._tracks) == 0


class TestMotionEstimatorMultipleTracks:
    def test_independent_track_velocities(self):
        estimator = MotionEstimator(ema_alpha=1.0)
        estimator.update(
            tracker_ids=[1, 2],
            bboxes=[(0, 0, 10, 10), (100, 100, 110, 110)],
        )
        result = estimator.update(
            tracker_ids=[1, 2],
            bboxes=[(10, 0, 20, 10), (100, 100, 110, 110)],
        )
        assert result[1].velocity_px > 0
        assert result[2].velocity_px == 0.0
