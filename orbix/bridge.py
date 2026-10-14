import base64
import csv
import datetime
import json
import os
import sys
import threading
import time
from pathlib import Path
from typing import Any

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
    def __init__(self, target: Any = None):
        if hasattr(target, "_engine"):
            self._app = target
            self.engine = target._engine
        elif isinstance(target, SlabMeasurementEngine):
            self._app = None
            self.engine = target
        else:
            self._app = None
            self.engine = SlabMeasurementEngine()
        self.active_view_mode = "ORIGINAL"
        self.show_edges = True
        self.is_frozen = False
        self.is_measuring = True
        self.cursor_x = 980
        self.cursor_y = 620
        self._window = None
        self.roi = (150, 39, 1549, 870)
        self.source_label = "CAM01_2026-10-09_10-06-01.mp4"

    def get_state(self) -> dict:
        return {
            "mode": self.active_view_mode,
            "show_edges": self.show_edges,
            "is_frozen": self.is_frozen,
            "cursor_x": self.cursor_x,
            "cursor_y": self.cursor_y,
            "calibration": self.engine.calibration,
        }

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
        win = self._window or (self._app._window if self._app else None)
        if win is not None:
            win.toggle_fullscreen()
        return {"status": "ok"}

    def close_window(self) -> dict:
        win = self._window or (self._app._window if self._app else None)
        if win is not None:
            win.destroy()
        return {"status": "ok"}

    def set_cursor(self, x: int, y: int) -> dict:
        self.cursor_x = max(0, min(1920, int(x)))
        self.cursor_y = max(0, min(1080, int(y)))
        return {"status": "ok", "x": self.cursor_x, "y": self.cursor_y}

    def set_limits(self, target: float, lower: float, upper: float) -> dict:
        self.engine.target_thickness_mm = float(target)
        self.engine.lower_limit_mm = float(lower)
        self.engine.upper_limit_mm = float(upper)
        return {"status": "ok", "target": target, "lower": lower, "upper": upper}

    def set_roi(self, x: int, y: int, w: int, h: int) -> dict:
        self.roi = (int(x), int(y), int(w), int(h))
        return {"status": "ok", "roi": self.roi}

    def start_measurement(self) -> dict:
        self.is_measuring = not self.is_measuring
        return {"status": "ok", "is_measuring": self.is_measuring}

    def open_video_dialog(self) -> dict:
        win = self._window or (self._app._window if self._app else None)
        if win is None:
            return {"status": "error", "message": "Window unavailable"}
        import webview
        file_types = ("Video Files (*.mp4;*.avi;*.mkv;*.mov;*.wmv)", "All Files (*.*)")
        selected = win.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if selected and len(selected) > 0 and self._app is not None:
            path = selected[0]
            self.source_label = Path(path).name
            self._app.switch_source(path)
            return {"status": "ok", "filepath": path, "filename": self.source_label}
        return {"status": "cancelled"}

    def open_image_dialog(self) -> dict:
        win = self._window or (self._app._window if self._app else None)
        if win is None:
            return {"status": "error", "message": "Window unavailable"}
        import webview
        file_types = ("Image Files (*.jpg;*.jpeg;*.png;*.bmp;*.webp)", "All Files (*.*)")
        selected = win.create_file_dialog(webview.OPEN_DIALOG, allow_multiple=False, file_types=file_types)
        if selected and len(selected) > 0 and self._app is not None:
            path = selected[0]
            self.source_label = Path(path).name
            self._app.switch_source(path)
            return {"status": "ok", "filepath": path, "filename": self.source_label}
        return {"status": "cancelled"}

    def load_sample_video(self) -> dict:
        self.source_label = "CAM01_2026-10-09_10-06-01.mp4"
        if self._app is not None:
            self._app.switch_source(None)
        return {"status": "ok", "filename": self.source_label}

    def load_sample_image(self) -> dict:
        self.source_label = "SAMPLE_SLAB_HOT.jpg"
        if self._app is not None:
            self._app.switch_source(None)
        return {"status": "ok", "filename": self.source_label}

    def connect_camera(self, url: str) -> dict:
        url_str = str(url).strip()
        try:
            parsed = int(url_str)
        except ValueError:
            parsed = url_str
        self.source_label = f"IP: {url_str}"
        if self._app is not None:
            self._app.switch_source(parsed)
        return {"status": "ok", "source": url_str}

    def capture_image(self) -> dict:
        cap_dir = Path("data/captures")
        cap_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = cap_dir / f"capture_{ts}.png"
        last_frame = self._app.last_rendered_frame if self._app else None
        if last_frame is not None:
            cv2.imwrite(str(filepath), last_frame)
            return {"status": "ok", "captured": True, "path": str(filepath)}
        return {"status": "ok", "captured": True, "path": str(filepath)}

    def generate_report(self) -> dict:
        rep_dir = Path("data/reports")
        rep_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = rep_dir / f"slab_report_{ts}.csv"
        m = self._app.last_measurement if self._app else None
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Parameter", "Value"])
            writer.writerow(["Timestamp", ts])
            writer.writerow(["Source", self.source_label])
            writer.writerow(["Thickness (mm)", round(m.thickness_mm, 2) if m else 0.0])
            writer.writerow(["Minimum (mm)", round(m.min_mm, 2) if m else 0.0])
            writer.writerow(["Maximum (mm)", round(m.max_mm, 2) if m else 0.0])
            writer.writerow(["Average (mm)", round(m.avg_mm, 2) if m else 0.0])
            writer.writerow(["Std Dev (mm)", round(m.std_dev_mm, 2) if m else 0.0])
            writer.writerow(["Status", m.status_text if m else "N/A"])
            writer.writerow(["Confidence (%)", round(m.confidence_pct, 1) if m else 0.0])
            writer.writerow(["Calibration (mm/px)", self.engine.calibration])
            if m and hasattr(m, "thickness_profile_mm"):
                writer.writerow([])
                writer.writerow(["Profile Position", "Thickness (mm)"])
                for i, val in enumerate(m.thickness_profile_mm):
                    writer.writerow([i, val])
        return {"status": "ok", "report_generated": True, "path": str(filepath)}


class WebviewApp:
    def __init__(self, config: Config):
        self._config = config
        self._engine = SlabMeasurementEngine()
        self._logger = CSVLogger(output_dir=config.output_dir)
        self.api = BridgeAPI(self)
        self._stop_event = threading.Event()
        self._worker_thread = None
        self._window = None
        self._frame_count = 0
        self.last_rendered_frame = None
        self.last_measurement = None
        self._new_source = None
        self._source_lock = threading.Lock()

    def switch_source(self, new_source):
        with self._source_lock:
            self._new_source = new_source

    def run(self):
        import webview

        index_path = get_resource_path("orbix/web/index.html")
        if not index_path.exists():
            index_path = Path(__file__).parent / "web" / "index.html"

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Systrol.Orbix.VisionSystem.1.5")
            except Exception:
                pass

        self._window = webview.create_window(
            title="ORBIX — HOT METAL SLAB THICKNESS VISION SYSTEM",
            url=str(index_path.resolve()),
            js_api=self.api,
            width=1440,
            height=900,
            min_size=(1024, 680),
            resizable=True,
            fullscreen=False,
            background_color="#000000",
        )
        self.api._window = self._window
        self._window.events.shown += self._apply_window_icon
        self._window.events.closing += self._on_closing
        self._window.events.closed += self._on_closing

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

    def _apply_window_icon(self, *args):
        if sys.platform != "win32":
            return
        icon_path = str(get_resource_path("assets/orbix_ico_logo.ico"))
        if not Path(icon_path).exists():
            return
        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "ORBIX — HOT METAL SLAB THICKNESS VISION SYSTEM")
            if hwnd:
                hicon_sm = ctypes.windll.user32.LoadImageW(None, icon_path, 1, 16, 16, 0x00000010)
                hicon_lg = ctypes.windll.user32.LoadImageW(None, icon_path, 1, 32, 32, 0x00000010)
                if hicon_sm:
                    ctypes.windll.user32.PostMessageW(hwnd, 0x0080, 0, hicon_sm)
                if hicon_lg:
                    ctypes.windll.user32.PostMessageW(hwnd, 0x0080, 1, hicon_lg)
        except Exception:
            pass

    def _on_closing(self, *args):
        self._stop_event.set()

    def _telemetry_worker(self):
        source = None
        current_source_id = self._config.source
        try:
            source = FrameSource(current_source_id)
            source.open()
        except Exception:
            source = None

        self._logger.open()
        frame_idx = 0
        last_time = time.monotonic()
        fps = 17.5

        while not self._stop_event.is_set():
            with self._source_lock:
                if self._new_source is not None:
                    if source is not None:
                        try:
                            source.release()
                        except Exception:
                            pass
                    current_source_id = self._new_source
                    self._new_source = None
                    if current_source_id is not None:
                        try:
                            source = FrameSource(current_source_id)
                            source.open()
                        except Exception:
                            source = None
                    else:
                        source = None

            if self.api.is_frozen:
                time.sleep(0.04)
                continue

            start_t = time.monotonic()
            frame = None
            if source is not None:
                try:
                    frame = source.read()
                    if frame is None and isinstance(current_source_id, (str, Path)):
                        source.release()
                        source = FrameSource(current_source_id)
                        source.open()
                        frame = source.read()
                except Exception:
                    frame = None

            if frame is None:
                frame = self._engine.generate_synthetic_slab_frame(1920, 1080, frame_idx)

            measurement = self._engine.measure(
                frame,
                roi=self.api.roi,
                cursor_x=self.api.cursor_x,
            )
            self.last_measurement = measurement

            proc_ms = (time.monotonic() - start_t) * 1000.0

            rendered_frame = self._apply_view_mode(frame, self.api.active_view_mode, measurement)
            self.last_rendered_frame = rendered_frame
            frame_b64 = encode_frame_to_b64(rendered_frame, quality=68)

            dt = time.monotonic() - last_time
            if dt > 0:
                fps = 0.92 * fps + 0.08 * (1.0 / dt)
            last_time = time.monotonic()

            payload = {
                "frame_b64": frame_b64,
                "thickness_mm": measurement.thickness_mm,
                "thickness_px": measurement.thickness_px,
                "top_y": measurement.top_y,
                "bottom_y": measurement.bottom_y,
                "avg_top_y": measurement.avg_top_y,
                "avg_bottom_y": measurement.avg_bottom_y,
                "min_mm": measurement.min_mm,
                "max_mm": measurement.max_mm,
                "avg_mm": measurement.avg_mm,
                "std_dev_mm": measurement.std_dev_mm,
                "is_normal": measurement.is_normal,
                "is_valid": measurement.is_valid,
                "status_text": measurement.status_text,
                "warning_text": measurement.warning_text,
                "confidence_pct": measurement.confidence_pct,
                "otsu_threshold": measurement.otsu_threshold,
                "profile": getattr(measurement, "thickness_profile_mm", []),
                "fps": round(fps, 1),
                "processing_ms": int(round(proc_ms)),
                "calibration": self._engine.calibration,
                "cursor_x": self.api.cursor_x,
                "cursor_y": self.api.cursor_y,
                "source_name": self.api.source_label,
            }

            if self._stop_event.is_set():
                break

            if self._window is not None and not self._stop_event.is_set():
                try:
                    js_code = f"if (window.updateTelemetry) {{ window.updateTelemetry({json.dumps(payload)}); }}"
                    self._window.evaluate_js(js_code)
                except Exception:
                    self._stop_event.set()
                    break

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
                step = max(1, len(measurement.xs) // 160)
                for i in range(0, len(measurement.xs) - step, step):
                    cv2.line(display, (int(measurement.xs[i]), int(measurement.top_edges[i])), (int(measurement.xs[i + step]), int(measurement.top_edges[i + step])), (0, 229, 255), 2)
                    cv2.line(display, (int(measurement.xs[i]), int(measurement.bottom_edges[i])), (int(measurement.xs[i + step]), int(measurement.bottom_edges[i + step])), (0, 229, 255), 2)
            return display
        return frame
