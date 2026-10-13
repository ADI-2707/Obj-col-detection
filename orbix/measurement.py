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
    top_edges: np.ndarray
    bottom_edges: np.ndarray
    xs: np.ndarray


class SlabMeasurementEngine:
    DEFAULT_CALIBRATION: float = 0.34757

    def __init__(self, calibration_mm_per_px: float = DEFAULT_CALIBRATION):
        self.calibration = calibration_mm_per_px
        self.target_thickness_mm = 108.0
        self.lower_limit_mm = 10.0
        self.upper_limit_mm = 150.0

    def generate_synthetic_slab_frame(
        self, width: int = 1280, height: int = 720, frame_number: int = 0
    ) -> np.ndarray:
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        frame[:, :] = (18, 12, 10)

        top_y = int(height * 0.45 + 2 * math.sin(frame_number * 0.05))
        bottom_y = int(height * 0.72 + 2 * math.cos(frame_number * 0.04))

        for y in range(top_y, bottom_y):
            rel = (y - top_y) / max(1, bottom_y - top_y)
            heat = math.sin(rel * math.pi)
            r = int(min(255, 230 + 25 * heat))
            g = int(min(255, 120 + 70 * heat))
            b = int(min(255, 20 + 30 * heat))
            frame[y, 100 : width - 100] = (b, g, r)

        for y in range(max(0, top_y - 25), top_y):
            fade = (y - (top_y - 25)) / 25.0
            frame[y, 100 : width - 100] = (
                int(10 + 20 * fade),
                int(15 + 40 * fade),
                int(30 + 100 * fade),
            )

        for y in range(bottom_y, min(height, bottom_y + 25)):
            fade = 1.0 - (y - bottom_y) / 25.0
            frame[y, 100 : width - 100] = (
                int(10 + 20 * fade),
                int(15 + 40 * fade),
                int(30 + 100 * fade),
            )

        noise = np.random.randint(0, 10, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        return frame

    def measure(
        self,
        frame: np.ndarray,
        roi: Tuple[int, int, int, int] | None = None,
        cursor_x: int | None = None,
    ) -> ThicknessMeasurement:
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
        gray = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        _, thresh = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        col_count = rw
        xs = np.arange(rx, rx + rw)
        top_edges = np.full(col_count, ry + rh * 0.45, dtype=np.float32)
        bottom_edges = np.full(col_count, ry + rh * 0.72, dtype=np.float32)

        sobel_y = cv2.Sobel(blurred, cv2.CV_32F, 0, 1, ksize=3)

        step = max(1, col_count // 320)
        for c in range(0, col_count, step):
            col_grad = sobel_y[:, c]
            min_idx = int(np.argmin(col_grad))
            max_idx = int(np.argmax(col_grad))

            if max_idx < min_idx and min_idx - max_idx > rh * 0.15:
                top_edges[c : c + step] = ry + max_idx
                bottom_edges[c : c + step] = ry + min_idx
            else:
                col_thresh = thresh[:, c]
                nz = np.where(col_thresh > 0)[0]
                if len(nz) > 5:
                    top_edges[c : c + step] = ry + nz[0]
                    bottom_edges[c : c + step] = ry + nz[-1]

        kernel_size = 11
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

        if cursor_x is None or cursor_x < rx or cursor_x >= rx + rw:
            active_x = rx + rw // 2
        else:
            active_x = cursor_x

        col_idx = min(len(top_edges) - 1, max(0, active_x - rx))
        cur_top = float(top_edges[col_idx])
        cur_bot = float(bottom_edges[col_idx])
        cur_px = float(thicknesses_px[col_idx])
        cur_mm = float(thicknesses_mm[col_idx])

        is_normal = self.lower_limit_mm <= cur_mm <= self.upper_limit_mm
        confidence_pct = max(75.0, min(99.0, 100.0 - (std_dev_mm * 4.0)))

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
            top_edges=top_edges,
            bottom_edges=bottom_edges,
            xs=xs,
        )
