import math
import time

import cv2
import numpy as np

from mill_motion.motion import MotionState


class Visualizer:
    BOX_COLOR = (0, 255, 0)
    TRAIL_COLOR = (255, 200, 0)
    ARROW_COLOR = (0, 0, 255)
    TEXT_COLOR = (255, 255, 255)
    TEXT_BG_COLOR = (0, 0, 0)
    FONT = cv2.FONT_HERSHEY_SIMPLEX

    def __init__(self):
        self._prev_time = time.monotonic()
        self._fps = 0.0

    def annotate(
        self,
        frame: np.ndarray,
        tracker_ids: list[int],
        class_ids: list[int],
        confidences: list[float],
        bboxes: list[tuple[float, float, float, float]],
        motion_states: dict[int, MotionState],
        frame_number: int,
        class_names: dict[int, str] | None = None,
    ) -> np.ndarray:
        annotated = frame.copy()

        self._update_fps()

        for track_id, class_id, conf, bbox in zip(
            tracker_ids, class_ids, confidences, bboxes
        ):
            x1, y1, x2, y2 = int(bbox[0]), int(bbox[1]), int(bbox[2]), int(bbox[3])

            cv2.rectangle(annotated, (x1, y1), (x2, y2), self.BOX_COLOR, 2)

            name = ""
            if class_names and class_id in class_names:
                name = class_names[class_id]
            label = f"ID:{track_id} {name} {conf:.2f}"

            label_size, _ = cv2.getTextSize(label, self.FONT, 0.5, 1)
            cv2.rectangle(
                annotated,
                (x1, y1 - label_size[1] - 6),
                (x1 + label_size[0] + 4, y1),
                self.TEXT_BG_COLOR,
                cv2.FILLED,
            )
            cv2.putText(
                annotated, label, (x1 + 2, y1 - 4), self.FONT, 0.5, self.TEXT_COLOR, 1
            )

            motion = motion_states.get(track_id)
            if motion is None:
                continue

            self._draw_trail(annotated, motion.trail)
            self._draw_velocity_arrow(annotated, bbox, motion)

        self._draw_hud(annotated, frame_number)

        return annotated

    def _draw_trail(self, frame: np.ndarray, trail: list[tuple[float, float]]):
        if len(trail) < 2:
            return

        points = [(int(p[0]), int(p[1])) for p in trail]
        for i in range(1, len(points)):
            alpha = i / len(points)
            thickness = max(1, int(alpha * 3))
            color = (
                int(self.TRAIL_COLOR[0] * alpha),
                int(self.TRAIL_COLOR[1] * alpha),
                int(self.TRAIL_COLOR[2] * alpha),
            )
            cv2.line(frame, points[i - 1], points[i], color, thickness)

    def _draw_velocity_arrow(
        self,
        frame: np.ndarray,
        bbox: tuple[float, float, float, float],
        motion: MotionState,
    ):
        if motion.velocity_px < 1.0:
            return

        cx = int((bbox[0] + bbox[2]) / 2)
        cy = int((bbox[1] + bbox[3]) / 2)

        arrow_length = min(motion.velocity_px * 3, 80)
        rad = math.radians(motion.direction_deg)
        end_x = int(cx + arrow_length * math.cos(rad))
        end_y = int(cy + arrow_length * math.sin(rad))

        cv2.arrowedLine(frame, (cx, cy), (end_x, end_y), self.ARROW_COLOR, 2)

    def _draw_hud(self, frame: np.ndarray, frame_number: int):
        hud = f"Frame: {frame_number} | FPS: {self._fps:.1f}"
        cv2.putText(frame, hud, (10, 25), self.FONT, 0.6, self.TEXT_COLOR, 1)

    def _update_fps(self):
        now = time.monotonic()
        elapsed = now - self._prev_time
        if elapsed > 0:
            self._fps = 1.0 / elapsed
        self._prev_time = now
