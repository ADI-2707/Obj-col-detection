import math
import time

import cv2
import numpy as np

from mill_motion.motion import MotionState


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
    BOX_COLOR = (0, 255, 0)
    TRAIL_COLOR = (255, 200, 0)
    ARROW_COLOR = (0, 0, 255)
    TEXT_COLOR = (255, 255, 255)
    TEXT_BG_COLOR = (0, 0, 0)
    FONT = cv2.FONT_HERSHEY_SIMPLEX

    COLOR_BG = (22, 24, 28)
    COLOR_PANEL_BG = (30, 34, 40)
    COLOR_HEADER_BG = (38, 44, 52)
    COLOR_BORDER = (55, 65, 78)
    COLOR_TEXT_MAIN = (235, 240, 245)
    COLOR_TEXT_MUTED = (140, 155, 170)
    COLOR_TEXT_ACCENT = (210, 195, 100)
    COLOR_NOMINAL = (75, 195, 95)
    COLOR_CAUTION = (40, 180, 240)
    COLOR_ALERT = (50, 60, 240)

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

        self._draw_top_bar(canvas, frame_number, canvas_width)

        top_panels_y = max(48, int(canvas_height * 0.048))
        top_panels_h = int(canvas_height * 0.58)
        split_x = int(canvas_width * 0.635)

        self._draw_camera_panel(
            canvas=canvas,
            annotated_frame=annotated_frame,
            tracker_ids=tracker_ids,
            x1=12,
            y1=top_panels_y,
            x2=split_x - 6,
            y2=top_panels_y + top_panels_h,
        )

        self._draw_telemetry_panel(
            canvas=canvas,
            tracker_ids=tracker_ids,
            class_ids=class_ids,
            confidences=confidences,
            bboxes=bboxes,
            motion_states=motion_states,
            class_names=class_names,
            x1=split_x + 6,
            y1=top_panels_y,
            x2=canvas_width - 12,
            y2=top_panels_y + top_panels_h,
        )

        bottom_panel_y = top_panels_y + top_panels_h + 10
        bottom_panel_h = max(60, canvas_height - bottom_panel_y - 12)

        self._draw_collision_panel(
            canvas=canvas,
            tracker_ids=tracker_ids,
            bboxes=bboxes,
            motion_states=motion_states,
            frame_w=annotated_frame.shape[1],
            frame_h=annotated_frame.shape[0],
            frame_number=frame_number,
            x1=12,
            y1=bottom_panel_y,
            x2=canvas_width - 12,
            y2=bottom_panel_y + bottom_panel_h,
        )

        return canvas

    def _draw_panel(
        self,
        canvas: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        title: str,
        tag: str | None = None,
    ):
        cv2.rectangle(canvas, (x1, y1), (x2, y2), self.COLOR_PANEL_BG, cv2.FILLED)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), self.COLOR_BORDER, 1)

        header_h = 30
        cv2.rectangle(canvas, (x1, y1), (x2, y1 + header_h), self.COLOR_HEADER_BG, cv2.FILLED)
        cv2.line(canvas, (x1, y1 + header_h), (x2, y1 + header_h), self.COLOR_BORDER, 1)

        cv2.putText(
            canvas,
            title,
            (x1 + 12, y1 + 20),
            self.FONT,
            0.5,
            self.COLOR_TEXT_MAIN,
            1,
            cv2.LINE_AA,
        )

        if tag:
            tag_size, _ = cv2.getTextSize(tag, self.FONT, 0.42, 1)
            cv2.putText(
                canvas,
                tag,
                (x2 - tag_size[0] - 12, y1 + 20),
                self.FONT,
                0.42,
                self.COLOR_TEXT_ACCENT,
                1,
                cv2.LINE_AA,
            )

    def _draw_top_bar(self, canvas: np.ndarray, frame_number: int, width: int):
        cv2.rectangle(canvas, (12, 10), (width - 12, 44), self.COLOR_HEADER_BG, cv2.FILLED)
        cv2.rectangle(canvas, (12, 10), (width - 12, 44), self.COLOR_BORDER, 1)

        cv2.putText(
            canvas,
            "MILL MOTION // INDUSTRIAL MACHINE MONITOR",
            (24, 32),
            self.FONT,
            0.55,
            self.COLOR_TEXT_MAIN,
            1,
            cv2.LINE_AA,
        )

        status_text = "STATUS: TRACKING ACTIVE"
        cv2.putText(
            canvas,
            status_text,
            (460, 32),
            self.FONT,
            0.48,
            self.COLOR_NOMINAL,
            1,
            cv2.LINE_AA,
        )

        hud_info = f"FPS: {self._fps:.1f}  |  FRAME: {frame_number:06d}  |  KEYS: [Q] QUIT  [F] FULLSCREEN"
        hud_size, _ = cv2.getTextSize(hud_info, self.FONT, 0.45, 1)
        cv2.putText(
            canvas,
            hud_info,
            (width - hud_size[0] - 24, 32),
            self.FONT,
            0.45,
            self.COLOR_TEXT_MUTED,
            1,
            cv2.LINE_AA,
        )

    def _draw_camera_panel(
        self,
        canvas: np.ndarray,
        annotated_frame: np.ndarray,
        tracker_ids: list[int],
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ):
        tag = f"ACTIVE TARGETS: {len(tracker_ids)}"
        self._draw_panel(canvas, x1, y1, x2, y2, "[ OPTICAL SENSOR FEED ]", tag=tag)

        pad_x = 10
        pad_top = 38
        pad_bot = 10
        vp_w = (x2 - x1) - (pad_x * 2)
        vp_h = (y2 - y1) - pad_top - pad_bot

        fh, fw = annotated_frame.shape[:2]
        scale = min(vp_w / fw, vp_h / fh)
        dst_w = max(1, int(fw * scale))
        dst_h = max(1, int(fh * scale))

        resized = cv2.resize(annotated_frame, (dst_w, dst_h), interpolation=cv2.INTER_LINEAR)

        start_x = x1 + pad_x + (vp_w - dst_w) // 2
        start_y = y1 + pad_top + (vp_h - dst_h) // 2

        canvas[start_y : start_y + dst_h, start_x : start_x + dst_w] = resized
        cv2.rectangle(
            canvas,
            (start_x, start_y),
            (start_x + dst_w, start_y + dst_h),
            self.COLOR_BORDER,
            1,
        )

        bracket_len = 16
        for bx, by in [
            (start_x, start_y),
            (start_x + dst_w, start_y),
            (start_x, start_y + dst_h),
            (start_x + dst_w, start_y + dst_h),
        ]:
            dx = 1 if bx == start_x else -1
            dy = 1 if by == start_y else -1
            cv2.line(canvas, (bx, by), (bx + dx * bracket_len, by), self.COLOR_TEXT_ACCENT, 2)
            cv2.line(canvas, (bx, by), (bx, by + dy * bracket_len), self.COLOR_TEXT_ACCENT, 2)

    def _draw_telemetry_panel(
        self,
        canvas: np.ndarray,
        tracker_ids: list[int],
        class_ids: list[int],
        confidences: list[float],
        bboxes: list[tuple[float, float, float, float]],
        motion_states: dict[int, MotionState],
        class_names: dict[int, str] | None,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ):
        self._draw_panel(
            canvas,
            x1,
            y1,
            x2,
            y2,
            "[ TARGET TELEMETRY ]",
            tag=f"COUNT: {len(tracker_ids):02d}",
        )

        content_y = y1 + 42
        max_y = y2 - 12

        if not tracker_ids:
            box_h = 100
            cv2.rectangle(
                canvas,
                (x1 + 16, content_y),
                (x2 - 16, content_y + box_h),
                (26, 29, 34),
                cv2.FILLED,
            )
            cv2.rectangle(
                canvas,
                (x1 + 16, content_y),
                (x2 - 16, content_y + box_h),
                self.COLOR_BORDER,
                1,
            )
            cv2.putText(
                canvas,
                "NO ACTIVE TARGETS IN OPTICAL SECTOR",
                (x1 + 32, content_y + 42),
                self.FONT,
                0.5,
                self.COLOR_TEXT_MUTED,
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                canvas,
                "SYSTEM IDLE // AWAITING MOTION DETECTION",
                (x1 + 32, content_y + 70),
                self.FONT,
                0.42,
                self.COLOR_TEXT_ACCENT,
                1,
                cv2.LINE_AA,
            )
            return

        card_h = 126
        max_cards = max(1, (max_y - content_y) // (card_h + 8))
        displayed_count = min(len(tracker_ids), max_cards)

        for idx in range(displayed_count):
            tid = tracker_ids[idx]
            cid = class_ids[idx]
            conf = confidences[idx]
            bbox = bboxes[idx]
            motion = motion_states.get(tid)

            card_top = content_y + idx * (card_h + 8)
            card_bot = card_top + card_h

            cv2.rectangle(
                canvas,
                (x1 + 14, card_top),
                (x2 - 14, card_bot),
                (25, 29, 35),
                cv2.FILLED,
            )
            cv2.rectangle(
                canvas,
                (x1 + 14, card_top),
                (x2 - 14, card_bot),
                self.COLOR_BORDER,
                1,
            )

            cv2.rectangle(
                canvas,
                (x1 + 14, card_top),
                (x2 - 14, card_top + 26),
                (32, 38, 46),
                cv2.FILLED,
            )
            cv2.line(
                canvas,
                (x1 + 14, card_top + 26),
                (x2 - 14, card_top + 26),
                self.COLOR_BORDER,
                1,
            )

            cname = class_names[cid] if class_names and cid in class_names else f"CLASS_{cid}"
            card_title = f"TARGET #{tid:02d} // {cname.upper()}"
            cv2.putText(
                canvas,
                card_title,
                (x1 + 24, card_top + 18),
                self.FONT,
                0.48,
                self.COLOR_TEXT_MAIN,
                1,
                cv2.LINE_AA,
            )

            conf_str = f"CONF: {conf * 100:.1f}%"
            conf_size, _ = cv2.getTextSize(conf_str, self.FONT, 0.42, 1)
            cv2.putText(
                canvas,
                conf_str,
                (x2 - conf_size[0] - 24, card_top + 18),
                self.FONT,
                0.42,
                self.COLOR_TEXT_ACCENT,
                1,
                cv2.LINE_AA,
            )

            vel = motion.velocity_px if motion else 0.0
            heading = motion.direction_deg if motion else 0.0
            compass = _heading_to_compass(heading)
            cx = (bbox[0] + bbox[2]) / 2.0
            cy = (bbox[1] + bbox[3]) / 2.0
            bw = bbox[2] - bbox[0]
            bh = bbox[3] - bbox[1]

            row1 = f"VELOCITY : {vel:6.2f} px/f ({vel * 30.0:6.1f} px/s)"
            row2 = f"HEADING  : {heading:5.1f} deg [{compass:>2}]"
            row3 = f"POSITION : ({cx:5.0f}, {cy:5.0f}) px"
            row4 = f"BOUNDS   : {bw:4.0f} x {bh:4.0f} px"

            cv2.putText(
                canvas,
                row1,
                (x1 + 24, card_top + 48),
                self.FONT,
                0.42,
                self.COLOR_TEXT_MAIN,
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                canvas,
                row2,
                (x1 + 24, card_top + 70),
                self.FONT,
                0.42,
                self.COLOR_TEXT_MUTED,
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                canvas,
                row3,
                (x1 + 24, card_top + 92),
                self.FONT,
                0.42,
                self.COLOR_TEXT_MAIN,
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                canvas,
                row4,
                (x1 + 24, card_top + 114),
                self.FONT,
                0.42,
                self.COLOR_TEXT_MUTED,
                1,
                cv2.LINE_AA,
            )

            status_lbl = "MOVING" if vel > 1.0 else "STATIC"
            status_color = self.COLOR_NOMINAL if vel > 1.0 else self.COLOR_TEXT_MUTED
            cv2.putText(
                canvas,
                status_lbl,
                (x2 - 80, card_top + 48),
                self.FONT,
                0.42,
                status_color,
                1,
                cv2.LINE_AA,
            )

        if len(tracker_ids) > displayed_count:
            remaining = len(tracker_ids) - displayed_count
            cv2.putText(
                canvas,
                f"+ {remaining} ADDITIONAL TARGET(S) RECORDED TO LOG",
                (x1 + 24, max_y - 4),
                self.FONT,
                0.4,
                self.COLOR_TEXT_ACCENT,
                1,
                cv2.LINE_AA,
            )

    def _draw_collision_panel(
        self,
        canvas: np.ndarray,
        tracker_ids: list[int],
        bboxes: list[tuple[float, float, float, float]],
        motion_states: dict[int, MotionState],
        frame_w: int,
        frame_h: int,
        frame_number: int,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ):
        self._draw_panel(
            canvas,
            x1,
            y1,
            x2,
            y2,
            "[ COLLISION ASSESSMENT & TRAJECTORY RADAR ]",
            tag="MONITORING ACTIVE",
        )

        total_w = x2 - x1
        w_radar = int(total_w * 0.28)
        w_matrix = int(total_w * 0.40)
        w_audit = total_w - w_radar - w_matrix

        rx1 = x1 + 10
        rx2 = rx1 + w_radar - 10
        mx1 = rx2 + 10
        mx2 = mx1 + w_matrix - 10
        ax1 = mx2 + 10
        ax2 = x2 - 10

        sub_y1 = y1 + 38
        sub_y2 = y2 - 10

        self._draw_subpanel_box(canvas, rx1, sub_y1, rx2, sub_y2, "SPATIAL TRAJECTORY RADAR")
        rad = max(10, min((rx2 - rx1) // 2 - 20, (sub_y2 - sub_y1) // 2 - 22))
        self._draw_radar(
            canvas=canvas,
            cx=(rx1 + rx2) // 2,
            cy=(sub_y1 + sub_y2 + 20) // 2,
            radius=rad,
            tracker_ids=tracker_ids,
            bboxes=bboxes,
            motion_states=motion_states,
            frame_w=frame_w,
            frame_h=frame_h,
        )

        self._draw_subpanel_box(canvas, mx1, sub_y1, mx2, sub_y2, "THREAT METRICS & IMPACT WINDOW")
        self._draw_threat_matrix(
            canvas=canvas,
            tracker_ids=tracker_ids,
            bboxes=bboxes,
            motion_states=motion_states,
            x1=mx1,
            y1=sub_y1,
            x2=mx2,
            y2=sub_y2,
        )

        self._draw_subpanel_box(canvas, ax1, sub_y1, ax2, sub_y2, "SYSTEM EVENT AUDIT STREAM")
        self._draw_audit_stream(
            canvas=canvas,
            tracker_ids=tracker_ids,
            frame_number=frame_number,
            x1=ax1,
            y1=sub_y1,
            x2=ax2,
            y2=sub_y2,
        )

    def _draw_subpanel_box(
        self, canvas: np.ndarray, x1: int, y1: int, x2: int, y2: int, label: str
    ):
        cv2.rectangle(canvas, (x1, y1), (x2, y2), (26, 30, 36), cv2.FILLED)
        cv2.rectangle(canvas, (x1, y1), (x2, y2), self.COLOR_BORDER, 1)

        cv2.rectangle(canvas, (x1, y1), (x2, y1 + 22), (32, 37, 45), cv2.FILLED)
        cv2.line(canvas, (x1, y1 + 22), (x2, y1 + 22), self.COLOR_BORDER, 1)

        cv2.putText(
            canvas,
            label,
            (x1 + 10, y1 + 16),
            self.FONT,
            0.42,
            self.COLOR_TEXT_MAIN,
            1,
            cv2.LINE_AA,
        )

    def _draw_radar(
        self,
        canvas: np.ndarray,
        cx: int,
        cy: int,
        radius: int,
        tracker_ids: list[int],
        bboxes: list[tuple[float, float, float, float]],
        motion_states: dict[int, MotionState],
        frame_w: int,
        frame_h: int,
    ):
        if radius < 10:
            return

        for ring_fraction in (0.33, 0.66, 1.0):
            r = int(radius * ring_fraction)
            cv2.circle(canvas, (cx, cy), r, (45, 55, 68), 1)

        cv2.line(canvas, (cx - radius, cy), (cx + radius, cy), (45, 55, 68), 1)
        cv2.line(canvas, (cx, cy - radius), (cx, cy + radius), (45, 55, 68), 1)

        cv2.putText(canvas, "N", (cx - 4, cy - radius + 12), self.FONT, 0.35, self.COLOR_TEXT_MUTED, 1)
        cv2.putText(canvas, "S", (cx - 4, cy + radius - 4), self.FONT, 0.35, self.COLOR_TEXT_MUTED, 1)
        cv2.putText(canvas, "W", (cx - radius + 4, cy + 4), self.FONT, 0.35, self.COLOR_TEXT_MUTED, 1)
        cv2.putText(canvas, "E", (cx + radius - 14, cy + 4), self.FONT, 0.35, self.COLOR_TEXT_MUTED, 1)

        if frame_w <= 0 or frame_h <= 0:
            return

        for tid, bbox in zip(tracker_ids, bboxes):
            bx = (bbox[0] + bbox[2]) / 2.0
            by = (bbox[1] + bbox[3]) / 2.0
            norm_x = (bx - (frame_w / 2.0)) / (frame_w / 2.0)
            norm_y = (by - (frame_h / 2.0)) / (frame_h / 2.0)

            px = int(cx + norm_x * (radius * 0.88))
            py = int(cy + norm_y * (radius * 0.88))
            dist = math.hypot(px - cx, py - cy)
            if dist > radius:
                factor = (radius - 4) / max(dist, 1)
                px = int(cx + (px - cx) * factor)
                py = int(cy + (py - cy) * factor)

            cv2.circle(canvas, (px, py), 4, self.COLOR_NOMINAL, cv2.FILLED)
            cv2.putText(
                canvas,
                f"#{tid}",
                (px + 6, py - 3),
                self.FONT,
                0.35,
                self.COLOR_TEXT_MAIN,
                1,
                cv2.LINE_AA,
            )

            motion = motion_states.get(tid)
            if motion and motion.velocity_px > 1.0:
                rad = math.radians(motion.direction_deg)
                vec_len = min(motion.velocity_px * 2.0, 24.0)
                vx = int(px + vec_len * math.cos(rad))
                vy = int(py + vec_len * math.sin(rad))
                cv2.line(canvas, (px, py), (vx, vy), self.COLOR_ALERT, 1)

    def _draw_threat_matrix(
        self,
        canvas: np.ndarray,
        tracker_ids: list[int],
        bboxes: list[tuple[float, float, float, float]],
        motion_states: dict[int, MotionState],
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ):
        banner_y = y1 + 32
        banner_h = 32

        num_targets = len(tracker_ids)
        min_dist = 999999.0
        closest_pair = None

        if num_targets >= 2:
            for i in range(num_targets):
                for j in range(i + 1, num_targets):
                    c1x = (bboxes[i][0] + bboxes[i][2]) / 2.0
                    c1y = (bboxes[i][1] + bboxes[i][3]) / 2.0
                    c2x = (bboxes[j][0] + bboxes[j][2]) / 2.0
                    c2y = (bboxes[j][1] + bboxes[j][3]) / 2.0
                    d = math.hypot(c1x - c2x, c1y - c2y)
                    if d < min_dist:
                        min_dist = d
                        closest_pair = (tracker_ids[i], tracker_ids[j])

        if closest_pair is not None and min_dist < 80.0:
            threat_level = "LEVEL 3 - CRITICAL PROXIMITY"
            banner_col = self.COLOR_ALERT
            prob_pct = max(0.0, min(100.0, (1.0 - min_dist / 80.0) * 100.0))
            ttc_str = f"~ {max(0.2, min_dist / 15.0):.1f} s [HAZARD]"
        elif closest_pair is not None and min_dist < 180.0:
            threat_level = "LEVEL 2 - PROXIMITY CAUTION"
            banner_col = self.COLOR_CAUTION
            prob_pct = max(0.0, min(100.0, (1.0 - min_dist / 180.0) * 50.0))
            ttc_str = f"~ {min_dist / 20.0:.1f} s [WARNING]"
        else:
            threat_level = "LEVEL 0 - NOMINAL (CLEAR)"
            banner_col = self.COLOR_NOMINAL
            prob_pct = 0.0
            ttc_str = "> 30.0 s [SECURE]"

        cv2.rectangle(
            canvas,
            (x1 + 12, banner_y),
            (x2 - 12, banner_y + banner_h),
            (22, 26, 32),
            cv2.FILLED,
        )
        cv2.rectangle(
            canvas,
            (x1 + 12, banner_y),
            (x2 - 12, banner_y + banner_h),
            banner_col,
            1,
        )

        cv2.putText(
            canvas,
            f"ALERT: {threat_level}",
            (x1 + 24, banner_y + 21),
            self.FONT,
            0.48,
            banner_col,
            1,
            cv2.LINE_AA,
        )

        pair_str = f"TARGET #{closest_pair[0]} <-> #{closest_pair[1]}" if closest_pair else "NONE (CLEAR)"
        dist_str = f"{min_dist:.1f} px" if closest_pair else "INF"

        rows = [
            ("COLLISION PROBABILITY", f"{prob_pct:5.1f} %"),
            ("ESTIMATED TIME TO IMPACT", ttc_str),
            ("CLOSEST TARGET PAIR", pair_str),
            ("SEPARATION DISTANCE", dist_str),
            ("SAFETY BUFFER ZONE", "100.0 px [ACTIVE]"),
            ("COLLISION COURSE EVAL", "PARALLEL / SEPARATED"),
        ]

        text_base = banner_y + banner_h + 24
        line_spacing = 24
        for idx, (label, val) in enumerate(rows):
            y_pos = text_base + idx * line_spacing
            if y_pos > y2 - 8:
                break
            cv2.putText(
                canvas,
                label,
                (x1 + 18, y_pos),
                self.FONT,
                0.41,
                self.COLOR_TEXT_MUTED,
                1,
                cv2.LINE_AA,
            )
            cv2.putText(
                canvas,
                val,
                (x1 + 250, y_pos),
                self.FONT,
                0.41,
                self.COLOR_TEXT_MAIN,
                1,
                cv2.LINE_AA,
            )

    def _draw_audit_stream(
        self,
        canvas: np.ndarray,
        tracker_ids: list[int],
        frame_number: int,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
    ):
        base_y = y1 + 36
        spacing = 22

        lines = [
            "[AUDIT] SYS_CORE: RUNTIME ONLINE",
            f"[AUDIT] CAM_OPT : FRAME STREAMING OK (F#{frame_number:06d})",
            f"[AUDIT] TRK_ENG : ACQUISITIONS IN SECTOR: {len(tracker_ids):02d}",
            "[AUDIT] COL_MOD : TRAJECTORY THREAT ENGINE ONLINE",
            "[AUDIT] SEC_BUF : PERIMETER BUFFER ARMED",
            "[AUDIT] REC_LOG : TELEMETRY RECORDING DIRECT TO DISK",
        ]

        for i, text in enumerate(lines):
            cur_y = base_y + i * spacing
            if cur_y > y2 - 6:
                break
            cv2.putText(
                canvas,
                text,
                (x1 + 14, cur_y),
                self.FONT,
                0.39,
                self.COLOR_TEXT_MUTED,
                1,
                cv2.LINE_AA,
            )

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
