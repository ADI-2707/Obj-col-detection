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

from vision import __version__
from vision.capture import FrameSource
from vision.config import Config
from vision.logger import CSVLogger
from vision.measurement import SlabMeasurementEngine, ThicknessMeasurement
from vision.paths import get_resource_path


def encode_frame_to_b64(frame: np.ndarray, quality: int = 75) -> str:
    if frame is None or frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
        return ""
    success, buffer = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), quality])
    if not success:
        return ""
    return base64.b64encode(buffer).decode("ascii")


def letterbox_frame(frame: np.ndarray, target_w: int = 1920, target_h: int = 1080) -> np.ndarray:
    if frame is None or frame.size == 0:
        return frame
    h, w = frame.shape[:2]
    if (w, h) == (target_w, target_h):
        return frame
    scale = min(target_w / w, target_h / h)
    nw = max(1, int(round(w * scale)))
    nh = max(1, int(round(h * scale)))
    resized = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_LINEAR)
    if frame.ndim == 3:
        canvas = np.zeros((target_h, target_w, frame.shape[2]), dtype=frame.dtype)
    else:
        canvas = np.zeros((target_h, target_w), dtype=frame.dtype)
    pad_x = (target_w - nw) // 2
    pad_y = (target_h - nh) // 2
    canvas[pad_y : pad_y + nh, pad_x : pad_x + nw] = resized
    return canvas


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
        if hasattr(target, "_config") and hasattr(target._config, "source"):
            src = target._config.source
            if isinstance(src, int):
                self.source_label = f"Camera {src}"
            elif src:
                self.source_label = Path(str(src)).name
            else:
                self.source_label = "CAM01_2026-10-09_10-06-01.mp4"
        else:
            self.source_label = "CAM01_2026-10-09_10-06-01.mp4"
        self.is_recording = False
        self.current_recording_path = None

    def get_state(self) -> dict:
        return {
            "version": __version__,
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

    def toggle_recording(self) -> dict:
        if self._app is not None:
            return self._app.toggle_recording()
        self.is_recording = not self.is_recording
        return {"status": "ok", "recording": self.is_recording}

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
        if self._app is not None and hasattr(self._app, "_engine") and self._app._engine is not None:
            self._app._engine.target_thickness_mm = float(target)
            self._app._engine.lower_limit_mm = float(lower)
            self._app._engine.upper_limit_mm = float(upper)
        return {"status": "ok", "target": target, "lower": lower, "upper": upper}

    def set_roi(self, x: int, y: int, w: int, h: int) -> dict:
        self.roi = (int(x), int(y), int(w), int(h))
        return {"status": "ok", "roi": self.roi}

    def set_colour_space(self, space: str) -> dict:
        self.engine.colour_space = str(space).lower()
        return {"status": "ok", "colour_space": self.engine.colour_space}

    def set_threshold_mode(self, mode: str, manual_val: int = 128) -> dict:
        self.engine.threshold_mode = str(mode).lower()
        self.engine.manual_threshold = int(manual_val)
        return {"status": "ok", "threshold_mode": self.engine.threshold_mode}

    def set_blur(self, ksize: int) -> dict:
        self.engine.blur_ksize = max(1, int(ksize))
        return {"status": "ok", "blur": self.engine.blur_ksize}

    def set_calibration(self, mm_per_px: float) -> dict:
        val = float(mm_per_px)
        if val > 0:
            self.engine.calibration = val
            if self._app is not None and hasattr(self._app, "_engine") and self._app._engine is not None:
                self._app._engine.calibration = val
            return {"status": "ok", "calibration": self.engine.calibration}
        return {"status": "error", "message": "Invalid scale"}

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
        if self.engine is not None and hasattr(self.engine, "reset_state"):
            self.engine.reset_state()
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

    def open_pdf_manual(self) -> dict:
        try:
            from vision.manual import open_pdf_manual as _open_pdf
            path = _open_pdf()
            return {"status": "ok", "path": str(path)}
        except Exception as e:
            return {"status": "error", "message": str(e)}


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
        self._video_writer = None
        self._recording_lock = threading.Lock()
        self._recording_path = None

    def toggle_recording(self) -> dict:
        with self._recording_lock:
            if self.api.is_recording:
                self.api.is_recording = False
                if self._video_writer is not None:
                    try:
                        self._video_writer.release()
                    except Exception:
                        pass
                    self._video_writer = None
                p = self._recording_path
                self._recording_path = None
                self.api.current_recording_path = None
                return {"status": "ok", "recording": False, "path": p}
            else:
                rec_dir = Path("data/recordings")
                rec_dir.mkdir(parents=True, exist_ok=True)
                ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                self._recording_path = str(rec_dir / f"dvr_recording_{ts}.avi")
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")
                self._video_writer = cv2.VideoWriter(self._recording_path, fourcc, 20.0, (1920, 1080))
                self.api.is_recording = True
                self.api.current_recording_path = self._recording_path
                return {"status": "ok", "recording": True, "path": self._recording_path}

    def switch_source(self, new_source):
        with self._source_lock:
            self._new_source = new_source
            if self._engine is not None and hasattr(self._engine, "reset_state"):
                self._engine.reset_state()

    def run(self):
        import logging
        import webview
        logging.getLogger("pywebview").setLevel(logging.CRITICAL)

        index_path = get_resource_path("vision/web/index.html")
        if not index_path.exists():
            index_path = get_resource_path("orbix/web/index.html")
        if not index_path.exists():
            index_path = Path(__file__).parent / "web" / "index.html"

        if sys.platform == "win32":
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(f"Systrol.Vision.MaterialManagement.{__version__}")
            except Exception:
                pass

        self._window = webview.create_window(
            title="Vision — Smart Material Management System",
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
        icon_path = str(get_resource_path("assets/Vision_logo.ico")) if get_resource_path("assets/Vision_logo.ico").exists() else str(get_resource_path("assets/orbix_ico_logo.ico"))
        if not Path(icon_path).exists():
            return

        def _set_icon_for_hwnd(hwnd):
            try:
                import ctypes
                cx_sm = ctypes.windll.user32.GetSystemMetrics(49) or 16
                cy_sm = ctypes.windll.user32.GetSystemMetrics(50) or 16
                cx_lg = ctypes.windll.user32.GetSystemMetrics(11) or 32
                cy_lg = ctypes.windll.user32.GetSystemMetrics(12) or 32
                hicon_sm = ctypes.windll.user32.LoadImageW(None, icon_path, 1, cx_sm, cy_sm, 0x00000010)
                hicon_lg = ctypes.windll.user32.LoadImageW(None, icon_path, 1, cx_lg, cy_lg, 0x00000010)
                if hicon_sm:
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 0, hicon_sm)
                if hicon_lg:
                    ctypes.windll.user32.SendMessageW(hwnd, 0x0080, 1, hicon_lg)
            except Exception:
                pass

        try:
            import ctypes
            hwnd = ctypes.windll.user32.FindWindowW(None, "Vision — Smart Material Management System")
            if hwnd:
                _set_icon_for_hwnd(hwnd)
                return
        except Exception:
            pass

        def _poll_and_apply():
            try:
                import ctypes
                import time
                for _ in range(15):
                    hwnd = ctypes.windll.user32.FindWindowW(None, "Vision — Smart Material Management System")
                    if hwnd:
                        _set_icon_for_hwnd(hwnd)
                        return
                    time.sleep(0.1)
            except Exception:
                pass

        threading.Thread(target=_poll_and_apply, daemon=True).start()

    def _on_closing(self, *args):
        self._stop_event.set()
        self._window = None
        if self.api is not None:
            self.api._window = None
        with self._recording_lock:
            if self._video_writer is not None:
                try:
                    self._video_writer.release()
                except Exception:
                    pass
                self._video_writer = None

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
            elif frame.shape[:2] != (1080, 1920):
                frame = letterbox_frame(frame, 1920, 1080)

            measurement = self._engine.measure(
                frame,
                roi=self.api.roi,
                cursor_x=self.api.cursor_x,
            )
            self.last_measurement = measurement

            proc_ms = (time.monotonic() - start_t) * 1000.0

            rendered_frame = self._apply_view_mode(frame, self.api.active_view_mode, measurement)
            self.last_rendered_frame = rendered_frame
            with self._recording_lock:
                if self.api.is_recording and self._video_writer is not None:
                    try:
                        if rendered_frame.shape[:2] != (1080, 1920):
                            rec_frame = cv2.resize(rendered_frame, (1920, 1080))
                        else:
                            rec_frame = rendered_frame
                        self._video_writer.write(rec_frame)
                    except Exception:
                        pass
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
                "target_mm": getattr(self._engine, "target_thickness_mm", 78.0),
                "lower_limit_mm": getattr(self._engine, "lower_limit_mm", 10.0),
                "upper_limit_mm": getattr(self._engine, "upper_limit_mm", 300.0),
                "cursor_x": self.api.cursor_x,
                "cursor_y": self.api.cursor_y,
                "source_name": self.api.source_label,
                "roi": list(self.api.roi),
                "colour_space": getattr(self._engine, "colour_space", "grayscale"),
                "threshold_mode": getattr(self._engine, "threshold_mode", "otsu"),
                "is_recording": self.api.is_recording,
                "show_edges": self.api.show_edges,
                "version": __version__,
            }

            if self._stop_event.is_set():
                break

            if self._window is not None and not self._stop_event.is_set():
                try:
                    js_code = f"if (window.updateTelemetry) {{ window.updateTelemetry({json.dumps(payload)}); }}"
                    self._window.evaluate_js(js_code)
                except Exception:
                    pass

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
            if getattr(self._engine, "colour_space", "grayscale") == "hsv":
                chan = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)[:, :, 2]
            elif getattr(self._engine, "colour_space", "grayscale") == "lab":
                chan = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)[:, :, 0]
            else:
                chan = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            k = max(1, self._engine.blur_ksize if self._engine.blur_ksize % 2 == 1 else self._engine.blur_ksize + 1)
            blurred = cv2.GaussianBlur(chan, (k, k), 0)
            if getattr(self._engine, "threshold_mode", "otsu") == "adaptive":
                th = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 2)
            elif getattr(self._engine, "threshold_mode", "otsu") == "manual":
                _, th = cv2.threshold(blurred, int(self._engine.manual_threshold), 255, cv2.THRESH_BINARY)
            else:
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
