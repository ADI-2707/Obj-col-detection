import math
from dataclasses import dataclass
from typing import Tuple

import cv2
import numpy as np


@dataclass
class ThicknessMeasurement:
    x_cursor: int
    top_y: float
    bottom_y: float
    thickness_px: float
    thickness_mm: float
    min_mm: float
    max_mm: float
    avg_mm: float
    std_dev_mm: float
    confidence_pct: float
    is_normal: bool
    is_valid: bool
    status_text: str
    warning_text: str
    otsu_threshold: int
    avg_top_y: float
    avg_bottom_y: float
    top_edges: np.ndarray
    bottom_edges: np.ndarray
    xs: np.ndarray

    @property
    def thickness_profile_mm(self) -> list[float]:
        if len(self.top_edges) == 0:
            return []
        step = max(1, len(self.top_edges) // 120)
        diff = self.bottom_edges[::step] - self.top_edges[::step]
        ratio = self.thickness_mm / max(1e-3, self.thickness_px)
        return [round(float(v * ratio), 1) for v in diff]


def _subpixel_peak(grad: np.ndarray, idx: int) -> float:
    if idx <= 0 or idx >= len(grad) - 1:
        return float(idx)
    a = float(grad[idx - 1])
    b = float(grad[idx])
    c = float(grad[idx + 1])
    denom = a - 2.0 * b + c
    if abs(denom) < 1e-4:
        return float(idx)
    delta = 0.5 * (a - c) / denom
    if abs(delta) > 0.5:
        return float(idx)
    return float(idx + delta)


def _median_filter_1d(arr: np.ndarray, size: int = 7) -> np.ndarray:
    if len(arr) < size:
        return arr
    pad = size // 2
    padded = np.pad(arr, pad, mode="edge")
    windows = np.lib.stride_tricks.sliding_window_view(padded, size)
    return np.median(windows, axis=1).astype(arr.dtype)


class SlabMeasurementEngine:
    DEFAULT_CALIBRATION: float = 0.34757

    def __init__(self, calibration_mm_per_px: float = DEFAULT_CALIBRATION):
        self.calibration = calibration_mm_per_px
        self.target_thickness_mm = 174.0
        self.lower_limit_mm = 10.0
        self.upper_limit_mm = 300.0
        self.colour_space = "grayscale"
        self.threshold_mode = "otsu"
        self.manual_threshold = 128
        self.blur_ksize = 5

    def generate_synthetic_slab_frame(
        self, width: int = 1920, height: int = 1080, frame_number: int = 0
    ) -> np.ndarray:
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (12, 10, 8)

        base_top = int(height * 0.32 + 1.5 * math.sin(frame_number * 0.04))
        base_bot = int(height * 0.78 + 1.5 * math.cos(frame_number * 0.03))

        slab_mask = np.zeros((height, width), dtype=np.float32)

        for y in range(base_top, base_bot):
            rel = (y - base_top) / max(1, base_bot - base_top)
            heat = math.sin(rel * math.pi)
            heat_val = 0.65 + 0.35 * heat
            slab_mask[y, :] = heat_val

        for y in range(max(0, base_top - 30), base_top):
            fade = (y - (base_top - 30)) / 30.0
            slab_mask[y, :] = fade * 0.35

        for y in range(base_bot, min(height, base_bot + 30)):
            fade = 1.0 - (y - base_bot) / 30.0
            slab_mask[y, :] = fade * 0.35

        texture = np.random.normal(0, 0.06, (height, width)).astype(np.float32)
        slab_mask = np.clip(slab_mask + texture, 0.0, 1.0)

        r = np.clip(slab_mask * 255.0, 0, 255).astype(np.uint8)
        g = np.clip((slab_mask ** 1.8) * 230.0, 0, 255).astype(np.uint8)
        b = np.clip((slab_mask ** 3.5) * 120.0, 0, 255).astype(np.uint8)

        slab_bgr = cv2.merge([b, g, r])
        frame = cv2.addWeighted(frame, 0.15, slab_bgr, 0.85, 0)
        return frame

    def measure(
        self,
        frame: np.ndarray,
        roi: Tuple[int, int, int, int] | None = None,
        cursor_x: int | None = None,
        x_cursor: int | None = None,
    ) -> ThicknessMeasurement:
        if cursor_x is None and x_cursor is not None:
            cursor_x = x_cursor
        h, w = frame.shape[:2]
        if roi is None:
            rx, ry, rw, rh = 0, 0, w, h
        else:
            rx, ry, rw, rh = roi
            rx = max(0, min(rx, w - 1))
            ry = max(0, min(ry, h - 1))
            rw = max(10, min(rw, w - rx))
            rh = max(10, min(rh, h - ry))

        roi_frame = frame[ry : ry + rh, rx : rx + rw]
        if self.colour_space == "hsv":
            hsv = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2HSV)
            proc_channel = hsv[:, :, 2]
        elif self.colour_space == "lab":
            lab = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2LAB)
            proc_channel = lab[:, :, 0]
        else:
            proc_channel = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)

        k = max(1, self.blur_ksize if self.blur_ksize % 2 == 1 else self.blur_ksize + 1)
        blurred = cv2.GaussianBlur(proc_channel, (k, k), 0)

        if self.threshold_mode == "adaptive":
            thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 15, 2)
            otsu_val_int = int(round(float(np.mean(blurred))))
        elif self.threshold_mode == "manual":
            th_val = max(1, min(254, int(self.manual_threshold)))
            _, thresh = cv2.threshold(blurred, th_val, 255, cv2.THRESH_BINARY)
            otsu_val_int = th_val
        else:
            otsu_val, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            otsu_val_int = int(round(otsu_val))

        col_count = rw
        xs = np.arange(rx, rx + rw)
        top_edges = np.full(col_count, ry + rh * 0.33, dtype=np.float32)
        bottom_edges = np.full(col_count, ry + rh * 0.78, dtype=np.float32)

        sobel_y = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)

        row_profile = np.mean(thresh, axis=1)
        slab_rows = np.where(row_profile > 30)[0]
        if len(slab_rows) > 10:
            cand_top = int(slab_rows[0])
            cand_bot = int(slab_rows[-1])
        else:
            cand_top = int(rh * 0.33)
            cand_bot = int(rh * 0.78)

        w_top_min = max(0, cand_top - 45)
        w_top_max = min(rh - 1, cand_top + 45)
        w_bot_min = max(0, cand_bot - 45)
        w_bot_max = min(rh - 1, cand_bot + 45)

        detected_count = 0
        detected_mask = np.zeros(col_count, dtype=bool)
        step = max(1, col_count // 320)
        for c in range(0, col_count, step):
            col_grad = sobel_y[:, c]
            if w_top_max > w_top_min and w_bot_max > w_bot_min:
                top_sub = int(np.argmax(col_grad[w_top_min:w_top_max]))
                bot_sub = int(np.argmin(col_grad[w_bot_min:w_bot_max]))
                cur_top_idx = w_top_min + top_sub
                cur_bot_idx = w_bot_min + bot_sub
            else:
                cur_bot_idx = int(np.argmin(col_grad))
                cur_top_idx = int(np.argmax(col_grad))

            if cur_top_idx < cur_bot_idx and (cur_bot_idx - cur_top_idx) > rh * 0.15:
                ref_top = _subpixel_peak(col_grad, cur_top_idx)
                ref_bot = _subpixel_peak(-col_grad, cur_bot_idx)
                top_edges[c : c + step] = ry + ref_top
                bottom_edges[c : c + step] = ry + ref_bot
                detected_mask[c : c + step] = True
                detected_count += 1

        if detected_count > 0:
            if not np.all(detected_mask):
                valid_indices = np.where(detected_mask)[0]
                all_indices = np.arange(col_count)
                top_edges = np.interp(all_indices, valid_indices, top_edges[valid_indices])
                bottom_edges = np.interp(all_indices, valid_indices, bottom_edges[valid_indices])
        else:
            top_edges = np.full(col_count, ry + cand_top, dtype=np.float32)
            bottom_edges = np.full(col_count, ry + cand_bot, dtype=np.float32)

        if len(top_edges) >= 7:
            top_edges = _median_filter_1d(top_edges, 7)
            bottom_edges = _median_filter_1d(bottom_edges, 7)

        kernel_size = 9
        if len(top_edges) >= kernel_size:
            pad = kernel_size // 2
            top_padded = np.pad(top_edges, pad, mode="edge")
            bottom_padded = np.pad(bottom_edges, pad, mode="edge")
            top_edges = np.convolve(top_padded, np.ones(kernel_size) / kernel_size, mode="valid")
            bottom_edges = np.convolve(bottom_padded, np.ones(kernel_size) / kernel_size, mode="valid")

        thicknesses_px = np.maximum(1.0, bottom_edges - top_edges)
        thicknesses_mm = thicknesses_px * self.calibration

        min_mm = float(np.min(thicknesses_mm))
        max_mm = float(np.max(thicknesses_mm))
        avg_mm = float(np.mean(thicknesses_mm))
        std_dev_mm = float(np.std(thicknesses_mm))

        total_steps = max(1, col_count // step)
        detection_ratio = detected_count / total_steps
        raw_conf = (detection_ratio * 70.0) + max(0.0, 30.0 - std_dev_mm * 5.0)
        confidence_pct = float(max(0.0, min(100.0, raw_conf)))

        is_valid = confidence_pct >= 40.0 and avg_mm > 20.0

        if cursor_x is None or cursor_x < rx or cursor_x >= rx + rw:
            active_x = rx + rw // 2
        else:
            active_x = cursor_x

        col_idx = min(len(top_edges) - 1, max(0, active_x - rx))
        cur_top = float(top_edges[col_idx])
        cur_bot = float(bottom_edges[col_idx])
        cur_px = float(thicknesses_px[col_idx])
        cur_mm = float(thicknesses_mm[col_idx])

        is_normal = is_valid and (self.lower_limit_mm <= cur_mm <= self.upper_limit_mm)

        if not is_valid:
            status_text = "LOW CONFIDENCE"
            warning_text = "Detected boundaries are weak - check threshold settings"
        elif is_normal:
            status_text = "NORMAL"
            warning_text = ""
        else:
            status_text = "OUT OF SPEC"
            warning_text = "Thickness outside target tolerance"

        avg_top_y = float(np.mean(top_edges))
        avg_bottom_y = float(np.mean(bottom_edges))

        return ThicknessMeasurement(
            x_cursor=active_x,
            top_y=cur_top,
            bottom_y=cur_bot,
            thickness_px=cur_px,
            thickness_mm=cur_mm,
            min_mm=min_mm,
            max_mm=max_mm,
            avg_mm=avg_mm,
            std_dev_mm=std_dev_mm,
            confidence_pct=confidence_pct,
            is_normal=is_normal,
            is_valid=is_valid,
            status_text=status_text,
            warning_text=warning_text,
            otsu_threshold=otsu_val_int,
            avg_top_y=avg_top_y,
            avg_bottom_y=avg_bottom_y,
            top_edges=top_edges,
            bottom_edges=bottom_edges,
            xs=xs,
        )
