import sys

import cv2
import numpy as np

from mill_motion.capture import FrameSource, FrameSourceError
from mill_motion.config import Config
from mill_motion.detector import Detector
from mill_motion.logger import CSVLogger
from mill_motion.motion import MotionEstimator
from mill_motion.tracker import ObjectTracker
from mill_motion.visualizer import Visualizer


class Pipeline:
    WINDOW_NAME = "Mill Motion"

    def __init__(self, config: Config):
        self._config = config
        self._frame_source = FrameSource(config.source)
        self._detector = Detector(
            model_path=config.model_path,
            confidence=config.confidence_threshold,
        )
        self._tracker = ObjectTracker(
            track_buffer_length=config.track_buffer_length,
        )
        self._motion = MotionEstimator(
            ema_alpha=config.ema_alpha,
            trail_length=config.trail_length,
            stale_track_frames=config.stale_track_frames,
        )
        self._logger = CSVLogger(output_dir=config.output_dir)
        self._visualizer = Visualizer() if config.display else None
        self._class_names: dict[int, str] = {}
        self._is_fullscreen = config.fullscreen

    def run(self):
        try:
            self._frame_source.open()
        except FrameSourceError as exc:
            print(f"[ERROR] {exc}", file=sys.stderr)
            return

        self._logger.open()

        print(f"[INFO] Source opened: {self._config.source}")
        print(f"[INFO] Frame size: {self._frame_source.frame_size}")
        print(f"[INFO] CSV log: {self._logger.filepath}")
        print("[INFO] Press 'q' or 'ESC' to quit, 'f' to toggle fullscreen")

        if self._visualizer is not None:
            cv2.namedWindow(self.WINDOW_NAME, cv2.WINDOW_NORMAL)
            if self._is_fullscreen:
                cv2.setWindowProperty(
                    self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN
                )

        frame_number = 0

        try:
            for frame in self._frame_source:
                tracker_ids, class_ids, confidences, bboxes = self._process_frame(
                    frame
                )

                motion_states = self._motion.update(
                    tracker_ids=tracker_ids,
                    bboxes=bboxes,
                )

                self._logger.log_frame(
                    frame_number=frame_number,
                    tracker_ids=tracker_ids,
                    class_ids=class_ids,
                    confidences=confidences,
                    bboxes=bboxes,
                    motion_states=motion_states,
                )

                if self._visualizer is not None:
                    annotated = self._visualizer.annotate(
                        frame=frame,
                        tracker_ids=tracker_ids,
                        class_ids=class_ids,
                        confidences=confidences,
                        bboxes=bboxes,
                        motion_states=motion_states,
                        frame_number=frame_number,
                        class_names=self._class_names,
                    )
                    dashboard = self._visualizer.compose_dashboard(
                        annotated_frame=annotated,
                        tracker_ids=tracker_ids,
                        class_ids=class_ids,
                        confidences=confidences,
                        bboxes=bboxes,
                        motion_states=motion_states,
                        frame_number=frame_number,
                        class_names=self._class_names,
                    )
                    cv2.imshow(self.WINDOW_NAME, dashboard)
                    key = cv2.waitKey(1) & 0xFF
                    if key in (ord("q"), 27):
                        break
                    elif key == ord("f"):
                        self._toggle_fullscreen()

                frame_number += 1

        except KeyboardInterrupt:
            print("\n[INFO] Interrupted by user")
        finally:
            self._cleanup()
            print(f"[INFO] Processed {frame_number} frames")
            print(f"[INFO] Log saved to {self._logger.filepath}")

    def _toggle_fullscreen(self):
        self._is_fullscreen = not self._is_fullscreen
        prop = (
            cv2.WINDOW_FULLSCREEN
            if self._is_fullscreen
            else cv2.WINDOW_NORMAL
        )
        cv2.setWindowProperty(self.WINDOW_NAME, cv2.WND_PROP_FULLSCREEN, prop)

    def _process_frame(
        self, frame: np.ndarray
    ) -> tuple[list[int], list[int], list[float], list[tuple[float, float, float, float]]]:
        detections = self._detector.detect(frame)
        tracked = self._tracker.update(detections)

        if len(tracked) == 0:
            return [], [], [], []

        if self._detector._model.names and not self._class_names:
            self._class_names = self._detector._model.names

        tracker_ids = tracked.tracker_id.tolist() if tracked.tracker_id is not None else []
        class_ids = tracked.class_id.tolist() if tracked.class_id is not None else []
        confidences = tracked.confidence.tolist() if tracked.confidence is not None else []
        bboxes = [tuple(row) for row in tracked.xyxy.tolist()]

        return tracker_ids, class_ids, confidences, bboxes

    def _cleanup(self):
        self._frame_source.release()
        self._logger.close()
        if self._visualizer is not None:
            cv2.destroyAllWindows()
