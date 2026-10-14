import csv
from datetime import datetime, timezone
from pathlib import Path

from vision.motion import MotionState


class CSVLogger:
    FIELDNAMES = [
        "timestamp",
        "frame_number",
        "track_id",
        "class_id",
        "confidence",
        "x1",
        "y1",
        "x2",
        "y2",
        "velocity_px_per_frame",
        "direction_deg",
    ]

    def __init__(self, output_dir: Path):
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        self._filepath = output_dir / f"track_log_{timestamp}.csv"
        self._file = None
        self._writer = None

    def open(self):
        self._file = open(self._filepath, "w", newline="", encoding="utf-8")
        self._writer = csv.DictWriter(self._file, fieldnames=self.FIELDNAMES)
        self._writer.writeheader()

    def log_frame(
        self,
        frame_number: int,
        tracker_ids: list[int],
        class_ids: list[int],
        confidences: list[float],
        bboxes: list[tuple[float, float, float, float]],
        motion_states: dict[int, MotionState],
    ):
        if self._writer is None:
            return

        timestamp = datetime.now(timezone.utc).isoformat()

        for track_id, class_id, conf, bbox in zip(
            tracker_ids, class_ids, confidences, bboxes
        ):
            motion = motion_states.get(track_id)
            velocity = motion.velocity_px if motion else 0.0
            direction = motion.direction_deg if motion else 0.0

            self._writer.writerow({
                "timestamp": timestamp,
                "frame_number": frame_number,
                "track_id": track_id,
                "class_id": class_id,
                "confidence": f"{conf:.4f}",
                "x1": f"{bbox[0]:.1f}",
                "y1": f"{bbox[1]:.1f}",
                "x2": f"{bbox[2]:.1f}",
                "y2": f"{bbox[3]:.1f}",
                "velocity_px_per_frame": f"{velocity:.2f}",
                "direction_deg": f"{direction:.1f}",
            })

    def close(self):
        if self._file is not None:
            self._file.close()
            self._file = None
            self._writer = None

    @property
    def filepath(self) -> Path:
        return self._filepath

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False
