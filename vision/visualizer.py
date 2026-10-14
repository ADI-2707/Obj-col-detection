import datetime
import math
import time

import cv2
import numpy as np

from vision import __version__
from vision.measurement import SlabMeasurementEngine, ThicknessMeasurement
from vision.motion import MotionState
from vision.paths import get_resource_path


def _heading_to_compass(deg: float) -> str:
    val = deg % 360
    if 22.5 <= val < 67.5:
        return "NE"
    elif 67.5 <= val < 112.5:
        return "E"
    elif 112.5 <= val < 157.5:
        return "SE"
    elif 157.5 <= val < 202.5:
        return "S"
    elif 202.5 <= val < 247.5:
        return "SW"
    elif 247.5 <= val < 292.5:
        return "W"
    elif 292.5 <= val < 337.5:
        return "NW"
    return "N"


class Visualizer:
    COLOR_BG = (255, 255, 255)
    COLOR_PANEL_BG = (255, 255, 255)
    COLOR_HEADER_BG = (255, 255, 255)
    COLOR_SUBPANEL_BG = (252, 250, 248)
    COLOR_BORDER = (225, 215, 205)
    COLOR_BORDER_SUB = (235, 230, 222)

    COLOR_TEXT_MAIN = (0, 0, 0)
    COLOR_TEXT_MUTED = (120, 105, 95)
    COLOR_TEXT_WHITE = (255, 255, 255)

    COLOR_LOGO_BLUE = (120, 55, 16)
    COLOR_LOGO_GREEN = (25, 145, 45)
    COLOR_ALERT = (20, 20, 220)
    COLOR_CAUTION = (10, 130, 215)
    COLOR_SLAB_EDGE = (0, 215, 255)
    COLOR_CALIPER = (245, 210, 0)
    COLOR_ACTIVE_TAB = (245, 210, 0)

    BOX_COLOR = (25, 145, 45)
    TRAIL_COLOR = (240, 175, 0)
    ARROW_COLOR = (20, 20, 220)
    TEXT_COLOR = (255, 255, 255)
    TEXT_BG_COLOR = (120, 55, 16)
    FONT = cv2.FONT_HERSHEY_DUPLEX

    VIEW_MODES = ["ORIGINAL", "GRAY", "THRESHOLD", "DETECTION", "THERMAL", "MEASUREMENT"]

    def __init__(self):
        self._prev_time = time.monotonic()
        self._fps = 0.0
        self.active_view_mode = "ORIGINAL"
        self.show_edges = True
        self.is_frozen = False
        self.cursor_x = 977
        self.cursor_y = 622
        self.measurement_engine = SlabMeasurementEngine()
        self._systrol_logo = self._load_logo("assets/systrol_ico_logo.ico")
        logo = self._load_logo("assets/Vision_logo.ico")
        if logo is None:
            logo = self._load_logo("assets/orbix_ico_logo.ico")
        self._orbix_logo = logo
        self._vision_logo = logo

    def _load_logo(self, relative_path: str) -> np.ndarray | None:
        try:
            from PIL import Image

            path = get_resource_path(relative_path)
            if not path.exists():
                return None
            pil_img = Image.open(path).convert("RGBA")
            return np.array(pil_img)
        except Exception:
            return None

    def _overlay_icon(self, canvas: np.ndarray, icon: np.ndarray | None, x: int, y: int, size: int):
        if icon is None:
            return
        h, w = canvas.shape[:2]
        if x < 0 or y < 0 or x + size > w or y + size > h:
            return
        resized = cv2.resize(icon, (size, size), interpolation=cv2.INTER_AREA)
        if resized.shape[2] == 4:
            b, g, r, a = cv2.split(resized)
            overlay = cv2.merge([b, g, r])
            alpha = (a.astype(float) / 255.0)[:, :, np.newaxis]
            roi = canvas[y : y + size, x : x + size].astype(float)
            blended = (overlay.astype(float) * alpha) + (roi * (1.0 - alpha))
            canvas[y : y + size, x : x + size] = np.clip(blended, 0, 255).astype(np.uint8)
        else:
            canvas[y : y + size, x : x + size] = resized

    def handle_mouse_event(self, event: int, x: int, y: int) -> str | None:
        if 350 <= x <= 1570 and 96 <= y <= 861:
            rel_x = int((x - 350) / 1220 * 1920)
            rel_y = int((y - 96) / 765 * 1080)
            self.cursor_x = max(0, min(1920, rel_x))
            self.cursor_y = max(0, min(1080, rel_y))

        if event == cv2.EVENT_LBUTTONDOWN:
            if 56 <= y <= 88:
                cur_tx = 350
                for mode in self.VIEW_MODES:
                    sz, _ = cv2.getTextSize(mode, self.FONT, 0.38, 1)
                    tw = sz[0] + 20
                    if cur_tx <= x <= cur_tx + tw:
                        self.active_view_mode = mode
                        return f"view_mode_{mode}"
                    cur_tx += tw + 4

                util_x = 1570
                utils = [("FULLSCREEN", 90), ("FREEZE", 66), ("EDGES", 60)]
                for uname, uw in utils:
                    ux = util_x - uw
                    if ux <= x <= util_x:
                        if uname == "FULLSCREEN":
                            return "toggle_fullscreen"
                        elif uname == "FREEZE":
                            self.is_frozen = not self.is_frozen
                            return "toggle_freeze"
                        elif uname == "EDGES":
                            self.show_edges = not self.show_edges
                            return "toggle_edges"
                    util_x = ux - 6

        return None

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
            label_size, _ = cv2.getTextSize(label, self.FONT, 0.55, 1)
            cv2.rectangle(
                annotated,
                (x1, y1 - label_size[1] - 8),
                (x1 + label_size[0] + 6, y1),
                self.TEXT_BG_COLOR,
                cv2.FILLED,
            )
            cv2.putText(
                annotated,
                label,
                (x1 + 3, y1 - 4),
                self.FONT,
                0.55,
                self.TEXT_COLOR,
                1,
                cv2.LINE_AA,
            )
            motion = motion_states.get(track_id)
            if motion is not None:
                self._draw_trail(annotated, motion.trail)
                self._draw_velocity_arrow(annotated, bbox, motion)

        self._draw_hud(annotated, frame_number)
        return annotated

    def compose_dashboard(
        self,
        annotated_frame: np.ndarray,
        tracker_ids: list[int],
        class_ids: list[int],
        confidences: list[float],
        bboxes: list[tuple[float, float, float, float]],
        motion_states: dict[int, MotionState],
        frame_number: int,
        class_names: dict[int, str] | None = None,
        canvas_width: int = 1920,
        canvas_height: int = 1080,
    ) -> np.ndarray:
        canvas = np.full((canvas_height, canvas_width, 3), self.COLOR_BG, dtype=np.uint8)

        left_w = 286
        right_w = 310
        center_x1 = left_w + 12
        center_x2 = canvas_width - right_w - 12
        top_y = 54
        bottom_y = canvas_height - 28

        roi = (150, 39, 1549, 870)
        measurement = self.measurement_engine.measure(
            annotated_frame, roi=roi, cursor_x=self.cursor_x
        )

        self._draw_top_header(canvas, frame_number, canvas_width)
        self._draw_left_sidebar(canvas, 10, top_y, left_w, bottom_y - top_y)
        self._draw_right_sidebar(canvas, canvas_width - right_w - 10, top_y, right_w, bottom_y - top_y, measurement)
        self._draw_center_viewport(
            canvas=canvas,
            frame=annotated_frame,
            measurement=measurement,
            x1=center_x1,
            y1=top_y,
            x2=center_x2,
            y2=bottom_y,
            frame_number=frame_number,
        )
        self._draw_status_bar(canvas, frame_number, canvas_width, canvas_height)

        return canvas

    def _draw_top_header(self, canvas: np.ndarray, frame_number: int, width: int):
        cv2.rectangle(canvas, (0, 0), (width, 48), self.COLOR_HEADER_BG, cv2.FILLED)
        cv2.line(canvas, (0, 48), (width, 48), self.COLOR_BORDER, 1)

        self._overlay_icon(canvas, self._orbix_logo, 14, 12, 24)

        title = f"VISION \u2014 SMART MATERIAL MANAGEMENT SYSTEM  v{__version__}"
        cv2.putText(canvas, title, (44, 25), self.FONT, 0.52, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)

        subtitle = "Hot-metal edge detection \u00b7 Pixel-to-mm calibration \u00b7 Live thickness profile"
        cv2.putText(canvas, subtitle, (44, 40), self.FONT, 0.38, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        sub_size, _ = cv2.getTextSize(subtitle, self.FONT, 0.38, 1)
        p_x = 44 + sub_size[0] + 16
        cv2.putText(canvas, "powered by", (p_x, 40), self.FONT, 0.38, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
        self._overlay_icon(canvas, self._systrol_logo, p_x + 76, 29, 14)

        rx = width - 14
        gear_text = "\u2699"
        cv2.putText(canvas, gear_text, (rx - 16, 29), self.FONT, 0.60, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        now_str = datetime.datetime.now().strftime("%H:%M:%S  %a %d %b %Y").upper()
        now_size, _ = cv2.getTextSize(now_str, self.FONT, 0.40, 1)
        clock_x = rx - 30 - now_size[0]
        cv2.putText(canvas, now_str, (clock_x, 28), self.FONT, 0.40, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)

        badges_x = clock_x - 12
        badges = [
            ("RECORDING OFF", False, (140, 130, 120), (245, 245, 245)),
            ("\u2022 NORMAL", True, self.COLOR_LOGO_GREEN, (230, 248, 235)),
            ("\u2022 VIDEO PLAYING", True, self.COLOR_LOGO_BLUE, (228, 244, 255)),
        ]

        cur_x = badges_x
        for label, is_active, fg, bg in badges:
            sz, _ = cv2.getTextSize(label, self.FONT, 0.38, 1)
            bw = sz[0] + 16
            bx = cur_x - bw
            cv2.rectangle(canvas, (bx, 14), (cur_x, 34), bg, cv2.FILLED)
            cv2.rectangle(canvas, (bx, 14), (cur_x, 34), fg, 1)
            cv2.putText(canvas, label, (bx + 8, 28), self.FONT, 0.38, fg, 1, cv2.LINE_AA)
            cur_x = bx - 8

    def _draw_card(self, canvas: np.ndarray, x: int, y: int, w: int, h: int, title: str):
        cv2.rectangle(canvas, (x, y), (x + w, y + h), self.COLOR_PANEL_BG, cv2.FILLED)
        cv2.rectangle(canvas, (x, y), (x + w, y + h), self.COLOR_BORDER, 1)
        header_h = 28
        cv2.rectangle(canvas, (x, y), (x + w, y + header_h), self.COLOR_HEADER_BG, cv2.FILLED)
        cv2.line(canvas, (x, y + header_h), (x + w, y + header_h), self.COLOR_BORDER, 1)
        cv2.putText(canvas, title, (x + 10, y + 19), self.FONT, 0.46, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)

    def _draw_button(
        self,
        canvas: np.ndarray,
        x: int,
        y: int,
        w: int,
        h: int,
        text: str,
        btn_type: str = "primary",
    ):
        if btn_type == "primary":
            bg = self.COLOR_LOGO_BLUE
            fg = (255, 255, 255)
        elif btn_type == "success":
            bg = self.COLOR_LOGO_GREEN
            fg = (255, 255, 255)
        else:
            bg = (245, 243, 238)
            fg = self.COLOR_TEXT_MAIN

        cv2.rectangle(canvas, (x, y), (x + w, y + h), bg, cv2.FILLED)
        cv2.rectangle(canvas, (x, y), (x + w, y + h), self.COLOR_BORDER, 1)
        sz, _ = cv2.getTextSize(text, self.FONT, 0.38, 1)
        tx = x + max(4, (w - sz[0]) // 2)
        ty = y + max(14, (h + sz[1]) // 2)
        cv2.putText(canvas, text, (tx, ty), self.FONT, 0.38, fg, 1, cv2.LINE_AA)

    def _draw_left_sidebar(self, canvas: np.ndarray, x: int, y: int, w: int, h: int):
        card_gap = 10
        ch = (h - card_gap * 2) // 3

        cy = y
        self._draw_card(canvas, x, cy, w, ch, "IMAGE SOURCE")
        cv2.putText(canvas, "RTSP URL / CAMERA IP", (x + 10, cy + 46), self.FONT, 0.36, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
        cv2.rectangle(canvas, (x + 10, cy + 54), (x + w - 10, cy + 80), (250, 248, 245), cv2.FILLED)
        cv2.rectangle(canvas, (x + 10, cy + 54), (x + w - 10, cy + 80), self.COLOR_BORDER, 1)
        cv2.putText(canvas, "192.168.1.250", (x + 16, cy + 72), self.FONT, 0.42, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)

        self._draw_button(canvas, x + 10, cy + 88, w - 20, 28, "CONNECT CAMERA", "primary")
        bw = (w - 26) // 2
        self._draw_button(canvas, x + 10, cy + 124, bw, 24, "OPEN IMAGE", "secondary")
        self._draw_button(canvas, x + 16 + bw, cy + 124, bw, 24, "OPEN VIDEO", "secondary")
        self._draw_button(canvas, x + 10, cy + 154, bw, 24, "SAMPLE IMAGE", "secondary")
        self._draw_button(canvas, x + 16 + bw, cy + 154, bw, 24, "SAMPLE VIDEO", "secondary")

        cv2.putText(canvas, "\u2022 VIDEO PLAYING \u00b7 Playing", (x + 10, cy + 198), self.FONT, 0.36, self.COLOR_LOGO_GREEN, 1, cv2.LINE_AA)
        cv2.putText(canvas, "CAM01_2026-10-09_10-06-40.mp4", (x + 10, cy + 214), self.FONT, 0.34, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        cy += ch + card_gap
        self._draw_card(canvas, x, cy, w, ch, "REGION OF INTEREST")
        self._draw_button(canvas, x + 10, cy + 38, bw, 26, "SELECT ROI", "secondary")
        self._draw_button(canvas, x + 16 + bw, cy + 38, bw, 26, "CONFIRM ROI", "success")

        btn3_w = (w - 32) // 3
        self._draw_button(canvas, x + 10, cy + 70, btn3_w, 22, "+ ADD", "secondary")
        self._draw_button(canvas, x + 16 + btn3_w, cy + 70, btn3_w, 22, "DELETE", "secondary")
        self._draw_button(canvas, x + 22 + btn3_w * 2, cy + 70, btn3_w, 22, "FULL", "secondary")

        cv2.rectangle(canvas, (x + 10, cy + 98), (x + w - 10, cy + 124), (242, 238, 230), cv2.FILLED)
        cv2.rectangle(canvas, (x + 10, cy + 98), (x + w - 10, cy + 124), self.COLOR_LOGO_BLUE, 1)
        cv2.putText(canvas, "ROI 1 : 1549 x 870 @ (150, 39)", (x + 16, cy + 115), self.FONT, 0.38, self.COLOR_LOGO_BLUE, 1, cv2.LINE_AA)

        col_w = (w - 20) // 2
        labels = [
            ("X", "150 px", x + 10, cy + 144),
            ("Y", "39 px", x + 10 + col_w, cy + 144),
            ("WIDTH", "1549 px", x + 10, cy + 180),
            ("HEIGHT", "870 px", x + 10 + col_w, cy + 180),
        ]
        for lbl, val, lx, ly in labels:
            cv2.putText(canvas, lbl, (lx, ly), self.FONT, 0.34, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
            cv2.putText(canvas, val, (lx, ly + 16), self.FONT, 0.42, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)

        cv2.putText(canvas, "AREA  1,347,630 px\u00b2", (x + 10, cy + 220), self.FONT, 0.38, self.COLOR_LOGO_BLUE, 1, cv2.LINE_AA)

        cy += ch + card_gap
        self._draw_card(canvas, x, cy, w, ch, "THRESHOLD & DETECTION")
        controls = [
            ("COLOUR SPACE", "Grayscale intensity", cy + 40),
            ("THRESHOLD MODE", "Otsu (automatic)", cy + 95),
            ("BLUR / KERNEL", "Gaussian Blur  |  k=5", cy + 150),
        ]
        for lbl, val, ly in controls:
            cv2.putText(canvas, lbl, (x + 10, ly), self.FONT, 0.34, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
            cv2.rectangle(canvas, (x + 10, ly + 6), (x + w - 10, ly + 32), (250, 248, 245), cv2.FILLED)
            cv2.rectangle(canvas, (x + 10, ly + 6), (x + w - 10, ly + 32), self.COLOR_BORDER, 1)
            cv2.putText(canvas, val, (x + 16, ly + 25), self.FONT, 0.40, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)

    def _draw_center_viewport(
        self,
        canvas: np.ndarray,
        frame: np.ndarray,
        measurement: ThicknessMeasurement,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        frame_number: int,
    ):
        tab_h = 32
        cur_tx = x1
        for mode in self.VIEW_MODES:
            is_active = mode == self.active_view_mode
            sz, _ = cv2.getTextSize(mode, self.FONT, 0.38, 1)
            tw = sz[0] + 20
            bg = self.COLOR_ACTIVE_TAB if is_active else self.COLOR_SUBPANEL_BG
            fg = (255, 255, 255) if is_active else self.COLOR_TEXT_MUTED
            cv2.rectangle(canvas, (cur_tx, y1), (cur_tx + tw, y1 + tab_h), bg, cv2.FILLED)
            cv2.rectangle(canvas, (cur_tx, y1), (cur_tx + tw, y1 + tab_h), self.COLOR_BORDER, 1)
            cv2.putText(canvas, mode, (cur_tx + 10, y1 + 21), self.FONT, 0.38, fg, 1, cv2.LINE_AA)
            cur_tx += tw + 4

        util_x = x2
        utils = [
            ("FULLSCREEN", 90, False),
            ("FREEZE", 66, self.is_frozen),
            ("EDGES", 60, self.show_edges),
        ]
        for uname, uw, is_act in utils:
            ux = util_x - uw
            bg = self.COLOR_ACTIVE_TAB if is_act else (250, 248, 245)
            fg = (255, 255, 255) if is_act else self.COLOR_TEXT_MUTED
            cv2.rectangle(canvas, (ux, y1), (util_x, y1 + tab_h), bg, cv2.FILLED)
            cv2.rectangle(canvas, (ux, y1), (util_x, y1 + tab_h), self.COLOR_BORDER, 1)
            cv2.putText(canvas, uname, (ux + 8, y1 + 21), self.FONT, 0.36, fg, 1, cv2.LINE_AA)
            util_x = ux - 6

        prof_h = 175
        video_y1 = y1 + tab_h + 8
        video_y2 = y2 - prof_h - 10
        video_w = x2 - x1
        video_h = video_y2 - video_y1

        cv2.rectangle(canvas, (x1, video_y1), (x2, video_y2), (18, 12, 10), cv2.FILLED)
        cv2.rectangle(canvas, (x1, video_y1), (x2, video_y2), self.COLOR_BORDER, 2)

        view_frame = self._render_view_mode(frame, self.active_view_mode)
        resized_view = cv2.resize(view_frame, (video_w, video_h))
        canvas[video_y1:video_y2, x1:x2] = resized_view

        self._draw_overlay_graphics(canvas, x1, video_y1, video_w, video_h, frame.shape[1], frame.shape[0], measurement)
        self._draw_thickness_profile(canvas, x1, video_y2 + 8, video_w, prof_h, measurement)

    def _render_view_mode(self, frame: np.ndarray, mode: str) -> np.ndarray:
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
        return frame

    def _draw_overlay_graphics(
        self,
        canvas: np.ndarray,
        vx: int,
        vy: int,
        vw: int,
        vh: int,
        orig_w: int,
        orig_h: int,
        measurement: ThicknessMeasurement,
    ):
        scale_x = vw / max(1, orig_w)
        scale_y = vh / max(1, orig_h)

        roi_x = int(150 * scale_x)
        roi_y = int(39 * scale_y)
        roi_w = int(1549 * scale_x)
        roi_h = int(870 * scale_y)
        cv2.rectangle(canvas, (vx + roi_x, vy + roi_y), (vx + roi_x + roi_w, vy + roi_y + roi_h), self.COLOR_CALIPER, 2)

        if self.show_edges and len(measurement.top_edges) > 1:
            step = max(1, len(measurement.xs) // 160)
            for i in range(0, len(measurement.xs) - step, step):
                px1 = vx + int(measurement.xs[i] * scale_x)
                px2 = vx + int(measurement.xs[i + step] * scale_x)
                py_top1 = vy + int(measurement.top_edges[i] * scale_y)
                py_top2 = vy + int(measurement.top_edges[i + step] * scale_y)
                py_bot1 = vy + int(measurement.bottom_edges[i] * scale_y)
                py_bot2 = vy + int(measurement.bottom_edges[i + step] * scale_y)
                cv2.line(canvas, (px1, py_top1), (px2, py_top2), self.COLOR_SLAB_EDGE, 2, cv2.LINE_AA)
                cv2.line(canvas, (px1, py_bot1), (px2, py_bot2), self.COLOR_SLAB_EDGE, 2, cv2.LINE_AA)

        cx = vx + int(measurement.x_cursor * scale_x)
        top_y = vy + int(measurement.top_y * scale_y)
        bot_y = vy + int(measurement.bottom_y * scale_y)

        for seg_y in range(vy + roi_y, vy + roi_y + roi_h, 8):
            cv2.line(canvas, (cx, seg_y), (cx, min(vy + roi_y + roi_h, seg_y + 4)), (180, 180, 180), 1)

        cv2.line(canvas, (cx, top_y), (cx, bot_y), self.COLOR_CALIPER, 2, cv2.LINE_AA)
        cv2.circle(canvas, (cx, top_y), 4, self.COLOR_SLAB_EDGE, cv2.FILLED)
        cv2.circle(canvas, (cx, bot_y), 4, self.COLOR_SLAB_EDGE, cv2.FILLED)

        tt_w, tt_h = 220, 68
        tt_x = min(vx + vw - tt_w - 10, max(vx + 10, cx + 14))
        tt_y = min(vy + vh - tt_h - 10, max(vy + 10, (top_y + bot_y) // 2 - 34))

        cv2.rectangle(canvas, (tt_x, tt_y), (tt_x + tt_w, tt_y + tt_h), (25, 20, 16), cv2.FILLED)
        cv2.rectangle(canvas, (tt_x, tt_y), (tt_x + tt_w, tt_y + tt_h), self.COLOR_CALIPER, 1)

        cv2.putText(canvas, f"X: {measurement.x_cursor} px   Y: {int(measurement.top_y + measurement.thickness_px/2)} px", (tt_x + 8, tt_y + 16), self.FONT, 0.35, (220, 220, 220), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"Top: {measurement.top_y:.1f} px   Bottom: {measurement.bottom_y:.1f} px", (tt_x + 8, tt_y + 32), self.FONT, 0.35, (180, 180, 180), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"Thickness: {measurement.thickness_px:.1f} px", (tt_x + 8, tt_y + 48), self.FONT, 0.38, (255, 255, 255), 1, cv2.LINE_AA)
        cv2.putText(canvas, f"Thickness: {measurement.thickness_mm:.1f} mm", (tt_x + 8, tt_y + 63), self.FONT, 0.44, self.COLOR_CALIPER, 1, cv2.LINE_AA)

        cv2.putText(canvas, "Vision", (vx + 28, vy + vh - 24), self.FONT, 0.70, (200, 200, 200), 1, cv2.LINE_AA)

    def _draw_thickness_profile(
        self,
        canvas: np.ndarray,
        x: int,
        y: int,
        w: int,
        h: int,
        measurement: ThicknessMeasurement,
    ):
        cv2.rectangle(canvas, (x, y), (x + w, y + h), self.COLOR_PANEL_BG, cv2.FILLED)
        cv2.rectangle(canvas, (x, y), (x + w, y + h), self.COLOR_BORDER, 1)

        header_h = 24
        cv2.rectangle(canvas, (x, y), (x + w, y + header_h), self.COLOR_HEADER_BG, cv2.FILLED)
        cv2.line(canvas, (x, y + header_h), (x + w, y + header_h), self.COLOR_BORDER, 1)

        cv2.putText(canvas, "THICKNESS PROFILE", (x + 8, y + 17), self.FONT, 0.40, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)
        cv2.putText(canvas, "MEASUREMENT POINTS", (x + 140, y + 17), self.FONT, 0.40, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        stats_str = f"MIN: {measurement.min_mm:.1f}  MAX: {measurement.max_mm:.1f}  AVG: {measurement.avg_mm:.1f}  \u03c3: {measurement.std_dev_mm:.2f}  CUR: {measurement.thickness_mm:.1f} mm"
        cv2.putText(canvas, stats_str, (x + 310, y + 17), self.FONT, 0.38, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)

        legend_str = "\u2014 Thickness   \u2014 Target   --- Limits   \u2022 Points"
        leg_sz, _ = cv2.getTextSize(legend_str, self.FONT, 0.34, 1)
        cv2.putText(canvas, legend_str, (x + w - leg_sz[0] - 12, y + 17), self.FONT, 0.34, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        plot_x1 = x + 44
        plot_x2 = x + w - 16
        plot_y1 = y + header_h + 8
        plot_y2 = y + h - 22

        cv2.line(canvas, (plot_x1, plot_y1), (plot_x1, plot_y2), self.COLOR_BORDER, 1)
        cv2.line(canvas, (plot_x1, plot_y2), (plot_x2, plot_y2), self.COLOR_BORDER, 1)

        for val, y_pct in [(300, 0.05), (200, 0.35), (100, 0.65), (0, 0.95)]:
            py = int(plot_y1 + (plot_y2 - plot_y1) * y_pct)
            cv2.line(canvas, (plot_x1 - 3, py), (plot_x2, py), self.COLOR_BORDER_SUB, 1)
            cv2.putText(canvas, str(val), (x + 10, py + 4), self.FONT, 0.30, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        target_y = int(plot_y2 - (plot_y2 - plot_y1) * (108.0 / 300.0))
        cv2.line(canvas, (plot_x1, target_y), (plot_x2, target_y), (140, 130, 120), 1)

        low_y = int(plot_y2 - (plot_y2 - plot_y1) * (70.0 / 300.0))
        high_y = int(plot_y2 - (plot_y2 - plot_y1) * (145.0 / 300.0))
        for dash_x in range(plot_x1, plot_x2, 8):
            cv2.line(canvas, (dash_x, low_y), (min(plot_x2, dash_x + 4), low_y), self.COLOR_ALERT, 1)
            cv2.line(canvas, (dash_x, high_y), (min(plot_x2, dash_x + 4), high_y), self.COLOR_ALERT, 1)

        if len(measurement.top_edges) > 1:
            pw = plot_x2 - plot_x1
            pts = []
            for i, thick_mm in enumerate((measurement.bottom_edges - measurement.top_edges) * self.measurement_engine.calibration):
                px = plot_x1 + int(i / max(1, len(measurement.top_edges) - 1) * pw)
                py = int(plot_y2 - (plot_y2 - plot_y1) * max(0.0, min(1.0, thick_mm / 300.0)))
                pts.append((px, py))

            for i in range(len(pts) - 1):
                cv2.line(canvas, pts[i], pts[i + 1], self.COLOR_LOGO_BLUE, 2, cv2.LINE_AA)

            cur_ratio = (measurement.x_cursor - measurement.xs[0]) / max(1, measurement.xs[-1] - measurement.xs[0])
            cur_px = plot_x1 + int(max(0.0, min(1.0, cur_ratio)) * pw)
            cur_py = int(plot_y2 - (plot_y2 - plot_y1) * max(0.0, min(1.0, measurement.thickness_mm / 300.0)))
            cv2.circle(canvas, (cur_px, cur_py), 5, (255, 255, 255), cv2.FILLED)
            cv2.circle(canvas, (cur_px, cur_py), 5, self.COLOR_LOGO_BLUE, 2)

        cv2.putText(canvas, "Position across slab (mm)", (plot_x1 + pw // 2 - 60, y + h - 6), self.FONT, 0.32, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

    def _draw_right_sidebar(
        self,
        canvas: np.ndarray,
        x: int,
        y: int,
        w: int,
        h: int,
        measurement: ThicknessMeasurement,
    ):
        card1_h = int(h * 0.44)
        card2_h = int(h * 0.22)
        card3_h = h - card1_h - card2_h - 20

        cy = y
        self._draw_card(canvas, x, cy, w, card1_h, "THICKNESS")
        cv2.putText(canvas, f"CURSOR X: {measurement.x_cursor} px", (x + w - 110, cy + 18), self.FONT, 0.32, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        cv2.putText(canvas, f"{measurement.thickness_mm:.1f}", (x + 12, cy + 62), self.FONT, 1.25, self.COLOR_TEXT_MAIN, 2, cv2.LINE_AA)
        cv2.putText(canvas, "mm", (x + 160, cy + 62), self.FONT, 0.65, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
        cv2.putText(canvas, f"{measurement.thickness_px:.1f} px", (x + 14, cy + 82), self.FONT, 0.40, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        metrics = [
            ("MINIMUM", f"{measurement.min_mm:.1f} mm", cy + 104),
            ("MAXIMUM", f"{measurement.max_mm:.1f} mm", cy + 124),
            ("AVERAGE", f"{measurement.avg_mm:.1f} mm", cy + 144),
            ("STD DEV", f"{measurement.std_dev_mm:.2f} mm", cy + 164),
        ]
        for lbl, val, ly in metrics:
            cv2.putText(canvas, lbl, (x + 14, ly), self.FONT, 0.36, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
            cv2.putText(canvas, val, (x + w - 74, ly), self.FONT, 0.38, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)

        badge_bg = (230, 248, 235) if measurement.is_normal else (235, 235, 255)
        badge_fg = self.COLOR_LOGO_GREEN if measurement.is_normal else self.COLOR_ALERT
        badge_text = "\u2022 NORMAL" if measurement.is_normal else "\u2022 OUT OF SPEC"
        cv2.rectangle(canvas, (x + 12, cy + 176), (x + w - 12, cy + 198), badge_bg, cv2.FILLED)
        cv2.rectangle(canvas, (x + 12, cy + 176), (x + w - 12, cy + 198), badge_fg, 1)
        cv2.putText(canvas, badge_text, (x + w // 2 - 34, cy + 192), self.FONT, 0.40, badge_fg, 1, cv2.LINE_AA)

        cv2.putText(canvas, f"DETECTION CONFIDENCE  {int(measurement.confidence_pct)}%  GOOD", (x + 14, cy + 215), self.FONT, 0.33, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
        total_segments = 24
        lit_segments = int(total_segments * (measurement.confidence_pct / 100.0))
        seg_w = (w - 28 - (total_segments - 1) * 2) // total_segments
        for i in range(total_segments):
            sx = x + 14 + i * (seg_w + 2)
            s_color = self.COLOR_LOGO_GREEN if i < lit_segments else (230, 225, 220)
            cv2.rectangle(canvas, (sx, cy + 222), (sx + seg_w, cy + 234), s_color, cv2.FILLED)

        cy += card1_h + 10
        self._draw_card(canvas, x, cy, w, card2_h, "CALIBRATION")
        cv2.putText(canvas, f"{self.measurement_engine.calibration:.5f} mm/px", (x + 14, cy + 48), self.FONT, 0.58, self.COLOR_TEXT_MAIN, 1, cv2.LINE_AA)
        cv2.putText(canvas, "= 2.87712 px/mm (derived)", (x + 14, cy + 66), self.FONT, 0.36, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
        cv2.putText(canvas, "Known object (2-point)  10-10-2026 10:23:55", (x + 14, cy + 84), self.FONT, 0.32, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)
        self._draw_button(canvas, x + 14, cy + 96, w - 28, 28, "CALIBRATE", "primary")

        cy += card2_h + 10
        self._draw_card(canvas, x, cy, w, card3_h, "OPERATION")
        self._draw_button(canvas, x + 14, cy + 36, w - 28, 30, "\u25b6 START MEASUREMENT", "success")
        self._draw_button(canvas, x + 14, cy + 74, w - 28, 30, "\U0001F4F7 CAPTURE IMAGE", "primary")
        self._draw_button(canvas, x + 14, cy + 112, w - 28, 28, "\U0001F4C4 GENERATE REPORT", "secondary")

    def _draw_status_bar(self, canvas: np.ndarray, frame_number: int, width: int, height: int):
        cv2.rectangle(canvas, (0, height - 24), (width, height), self.COLOR_HEADER_BG, cv2.FILLED)
        cv2.line(canvas, (0, height - 24), (width, height - 24), self.COLOR_BORDER, 1)

        status_left = f"FPS {self._fps:.1f} / 3.9   RESOLUTION 1920x1080   PROCESSING 168 ms   THRESHOLD OTSU 119   CALIBRATION {self.measurement_engine.calibration:.5f} mm/px"
        cv2.putText(canvas, status_left, (14, height - 7), self.FONT, 0.34, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

        status_right = "Playing CAM01_2026-10-09_10-06-40.mp4"
        sz, _ = cv2.getTextSize(status_right, self.FONT, 0.34, 1)
        cv2.putText(canvas, status_right, (width - sz[0] - 14, height - 7), self.FONT, 0.34, self.COLOR_TEXT_MUTED, 1, cv2.LINE_AA)

    def _draw_trail(self, frame: np.ndarray, trail: list[tuple[float, float]]):
        if len(trail) < 2:
            return
        for i in range(len(trail) - 1):
            pt1 = (int(trail[i][0]), int(trail[i][1]))
            pt2 = (int(trail[i + 1][0]), int(trail[i + 1][1]))
            cv2.line(frame, pt1, pt2, self.TRAIL_COLOR, 2, cv2.LINE_AA)

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
        hud_size, _ = cv2.getTextSize(hud, self.FONT, 0.62, 1)
        cv2.rectangle(
            frame,
            (8, 8),
            (14 + hud_size[0], 14 + hud_size[1] + 6),
            (20, 20, 20),
            cv2.FILLED,
        )
        cv2.putText(
            frame,
            hud,
            (12, 12 + hud_size[1]),
            self.FONT,
            0.62,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        h, w = frame.shape[:2]
        cv2.putText(
            frame,
            "powered by",
            (w - 145, h - 12),
            self.FONT,
            0.42,
            (220, 220, 220),
            1,
            cv2.LINE_AA,
        )
        self._overlay_icon(frame, self._systrol_logo, w - 44, h - 26, 20)

    def _update_fps(self):
        now = time.monotonic()
        elapsed = now - self._prev_time
        if elapsed > 0:
            self._fps = 1.0 / elapsed
        self._prev_time = now
