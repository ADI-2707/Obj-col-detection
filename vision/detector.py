from pathlib import Path

import numpy as np
import supervision as sv
from ultralytics import YOLO

from vision.paths import get_resource_path


class DetectorError(Exception):
    pass


class Detector:
    def __init__(self, model_path: str = "yolov8n.pt", confidence: float = 0.25):
        resolved = Path(model_path)
        if not resolved.suffix:
            raise DetectorError(
                f"Invalid model path '{model_path}'. "
                f"Expected a .pt, .onnx, or similar model file."
            )

        if not resolved.exists():
            bundled = get_resource_path(model_path)
            if bundled.exists():
                resolved = bundled

        try:
            self._model = YOLO(str(resolved))
        except Exception as exc:
            raise DetectorError(
                f"Failed to load YOLO model from '{model_path}': {exc}"
            ) from exc

        self._confidence = confidence

    def detect(self, frame: np.ndarray) -> sv.Detections:
        results = self._model(
            frame,
            conf=self._confidence,
            device="cpu",
            verbose=False,
        )

        if not results:
            return sv.Detections.empty()

        return sv.Detections.from_ultralytics(results[0])
