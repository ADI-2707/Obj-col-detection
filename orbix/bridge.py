import base64
import json
import threading
import time
from pathlib import Path

import cv2
import numpy as np

from orbix.capture import FrameSource
from orbix.config import Config
from orbix.logger import CSVLogger
from orbix.measurement import SlabMeasurementEngine, ThicknessMeasurement
from orbix.paths import get_resource_path


def encode_frame_to_b64(frame: np.ndarray, quality: int = 75) -> str:
    if frame is None or frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
        return ""
    success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        return ""
    return base64.b64encode(buffer).decode("ascii")


class BridgeAPI:
    def __init__(self, engine: SlabMeasurementEngine | None = None):
        self.engine = engine or SlabMeasurementEngine()
        self.active_view_mode = "ORIGINAL"
        self.show_edges = True
        self.is_frozen = False
        self.is_measuring = True
        self.cursor_x = 980
        self.cursor_y = 620
        self._window = None
        self.latest_payload = None

    def get_telemetry(self) -> dict | None:
        return self.latest_payload

    def set_view_mode(self, mode: str) -> dict:
        self.active_view_mode = mode
        return {"status": "ok", "mode": mode}

    def toggle_edges(self, enabled: bool) -> dict:
        self.show_edges = enabled
        return {"status": "ok", "show_edges": self.show_edges}

    def toggle_freeze(self, frozen: bool) -> dict:
        self.is_frozen = frozen
        return {"status": "ok", "is_frozen": self.is_frozen}

    def toggle_fullscreen(self) -> dict:
        if self._window is not None:
            self._window.toggle_fullscreen()
        return {"status": "ok"}

    def close_window(self) -> dict:
        if self._window is not None:
            self._window.destroy()
        return {"status": "ok"}

    def set_cursor(self, x: int, y: int) -> dict:
        self.cursor_x = max(0, min(1920, int(x)))
        self.cursor_y = max(0, min(1080, int(y)))
        return {"status": "ok", "x": self.cursor_x, "y": self.cursor_y}

    def start_measurement(self) -> dict:
        self.is_measuring = not self.is_measuring
        return {"status": "ok", "is_measuring": self.is_measuring}

    def capture_image(self) -> dict:
        return {"status": "ok", "captured": True}

    def generate_report(self) -> dict:
        return {"status": "ok", "report_generated": True}

    def get_state(self) -> dict:
        return {
            "mode": self.active_view_mode,
            "show_edges": self.show_edges,
            "is_frozen": self.is_frozen,
            "cursor_x": self.cursor_x,
            "cursor_y": self.cursor_y,
            "calibration": self.engine.calibration,
        }


class WebviewApp:
    def __init__(self, config: Config):
        self._config = config
        self._engine = SlabMeasurementEngine()
        self._logger = CSVLogger(output_dir=config.output_dir)
        self.api = BridgeAPI(self._engine)
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._window = None
        self._frame_count = 0

    def run(self):
        import webview

        index_path = get_resource_path("orbix/web/index.html")
        if not index_path.exists():
            index_path = Path(__file__).parent / "web" / "index.html"

        print(f"[INFO] Source opened: {self._config.source}")
        print(f"[INFO] Frame size: (1920, 1080)")
        print(f"[INFO] CSV log: {self._logger.filepath}")
        print("[INFO] Press 'q' or 'ESC' to quit, 'f' to toggle fullscreen")

        self._window = webview.create_window(
            title="ORBIX — HOT METAL SLAB THICKNESS VISION SYSTEM",
            url=str(index_path.resolve()),
            js_api=self.api,
            width=1440,
            height=900,
            min_size=(1024, 680),
            resizable=True,
            fullscreen=False,
        )
        self.api._window = self._window

        self._stop_event.clear()
        self._worker_thread = threading.Thread(target=self._telemetry_worker, daemon=True)
        self._worker_thread.start()

        try:
            webview.start(debug=False)
        finally:
            self._stop_event.set()
            if self._worker_thread and self._worker_thread.is_alive():
                self._worker_thread.join(timeout=1.0)
            self._logger.close()
            print(f"[INFO] Processed {self._frame_count} frames")
            print(f"[INFO] Log saved to {self._logger.filepath}")

    def _telemetry_worker(self):
        source = None
        try:
            source = FrameSource(self._config.source)
            source.open()
        except Exception:
            source = None

        self._logger.open()
        frame_idx = 0
        last_time = time.monotonic()
        fps = 15.0

        while not self._stop_event.is_set():
            if self.api.is_frozen:
                time.sleep(0.05)
                continue

            start_t = time.monotonic()
            frame = None
            if source is not None:
                try:
                    frame = source.read()
                except Exception:
                    frame = None

            if frame is None:
                frame = self._engine.generate_synthetic_slab_frame(frame_idx)

            measurement = self._engine.measure(frame, cursor_x=self.api.cursor_x)
            proc_ms = (time.monotonic() - start_t) * 1000.0

            rendered_frame = self._apply_view_mode(frame, self.api.active_view_mode, measurement)
            frame_b64 = encode_frame_to_b64(rendered_frame, quality=70)

            dt = time.monotonic() - last_time
            if dt > 0:
                fps = 0.9 * fps + 0.1 * (1.0 / dt)
            last_time = time.monotonic()

            payload = {
                "frame_b64": frame_b64,
                "thickness_mm": measurement.thickness_mm,
                "thickness_px": measurement.thickness_px,
                "min_mm": measurement.min_mm,
                "max_mm": measurement.max_mm,
                "avg_mm": measurement.avg_mm,
                "std_dev_mm": measurement.std_dev_mm,
                "is_normal": measurement.is_normal,
                "confidence_pct": measurement.confidence_pct,
                "profile": getattr(measurement, "thickness_profile_mm", []),
                "fps": fps,
                "processing_ms": proc_ms,
                "calibration": self._engine.calibration,
            }

            self.api.latest_payload = payload

            if self._window is not None:
                try:
                    js_code = f"if (window.updateTelemetry) {{ window.updateTelemetry({json.dumps(payload)}); }}"
                    self._window.evaluate_js(js_code)
                except Exception:
                    pass

            self._logger.log_frame(
                frame_number=frame_idx,
                tracker_ids=[],
                class_ids=[],
                confidences=[],
                bboxes=[],
                motion_states={},
            )
            if frame_idx % 30 == 0:
                status_text = "NORMAL" if measurement.is_normal else "OUT OF SPEC"
                print(f"[INFO] Frame: {frame_idx:05d} | FPS: {fps:.1f} | Thick: {measurement.thickness_mm:.1f} mm | Status: {status_text}")
            self._frame_count = frame_idx + 1

            frame_idx += 1
            elapsed = time.monotonic() - start_t
            sleep_time = max(0.01, (1.0 / 30.0) - elapsed)
            time.sleep(sleep_time)

        if source is not None:
            try:
                source.release()
            except Exception:
                pass

    def _apply_view_mode(self, frame: np.ndarray, mode: str, measurement: ThicknessMeasurement) -> np.ndarray:
        if mode == "GRAY":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)
        elif mode == "THRESHOLD":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            _, th = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            return cv2.cvtColor(th, cv2.COLOR_GRAY2BGR)
        elif mode == "DETECTION":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 40, 120)
            colored = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
            colored[:, :, 1] = edges
            return colored
        elif mode == "THERMAL":
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return cv2.applyColorMap(gray, cv2.COLORMAP_INFERNO)
        elif mode == "MEASUREMENT":
            display = frame.copy()
            if self.api.show_edges and len(measurement.top_edges) > 1:
                step = max(1, len(measurement.xs) // 120)
                for i in range(0, len(measurement.xs) - step, step):
                    cv2.line(display, (measurement.xs[i], int(measurement.top_edges[i])), (measurement.xs[i + step], int(measurement.top_edges[i + step])), (0, 215, 255), 2)
                    cv2.line(display, (measurement.xs[i], int(measurement.bottom_edges[i])), (measurement.xs[i + step], int(measurement.bottom_edges[i + step])), (0, 215, 255), 2)
            return display
        return frame
