import math
from collections import deque
from dataclasses import dataclass, field


@dataclass
class MotionState:
    velocity_px: float = 0.0
    direction_deg: float = 0.0
    trail: list[tuple[float, float]] = field(default_factory=list)


class _TrackState:
    def __init__(self, centroid: tuple[float, float], trail_length: int):
        self.prev_centroid = centroid
        self.smoothed_vx = 0.0
        self.smoothed_vy = 0.0
        self.trail: deque[tuple[float, float]] = deque(maxlen=trail_length)
        self.trail.append(centroid)
        self.frames_since_seen = 0


class MotionEstimator:
    def __init__(
        self,
        ema_alpha: float = 0.4,
        trail_length: int = 30,
        stale_track_frames: int = 60,
    ):
        self._alpha = ema_alpha
        self._trail_length = trail_length
        self._stale_threshold = stale_track_frames
        self._tracks: dict[int, _TrackState] = {}

    def update(
        self,
        tracker_ids: list[int],
        bboxes: list[tuple[float, float, float, float]],
    ) -> dict[int, MotionState]:
        seen_ids = set()
        results: dict[int, MotionState] = {}

        for track_id, bbox in zip(tracker_ids, bboxes):
            seen_ids.add(track_id)
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0
            centroid = (cx, cy)

            if track_id not in self._tracks:
                self._tracks[track_id] = _TrackState(centroid, self._trail_length)
                results[track_id] = MotionState(
                    velocity_px=0.0,
                    direction_deg=0.0,
                    trail=[centroid],
                )
                continue

            state = self._tracks[track_id]
            state.frames_since_seen = 0

            dx = cx - state.prev_centroid[0]
            dy = cy - state.prev_centroid[1]

            state.smoothed_vx = (
                self._alpha * dx + (1.0 - self._alpha) * state.smoothed_vx
            )
            state.smoothed_vy = (
                self._alpha * dy + (1.0 - self._alpha) * state.smoothed_vy
            )

            velocity = math.hypot(state.smoothed_vx, state.smoothed_vy)
            direction = math.degrees(
                math.atan2(state.smoothed_vy, state.smoothed_vx)
            )

            state.prev_centroid = centroid
            state.trail.append(centroid)

            results[track_id] = MotionState(
                velocity_px=velocity,
                direction_deg=direction,
                trail=list(state.trail),
            )

        self._prune_stale(seen_ids)

        return results

    def _prune_stale(self, seen_ids: set[int]):
        stale = []
        for track_id, state in self._tracks.items():
            if track_id not in seen_ids:
                state.frames_since_seen += 1
                if state.frames_since_seen > self._stale_threshold:
                    stale.append(track_id)

        for track_id in stale:
            del self._tracks[track_id]

    def reset(self):
        self._tracks.clear()
