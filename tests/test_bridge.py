import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from vision.bridge import BridgeAPI, WebviewApp, encode_frame_to_b64
from vision.config import Config
from vision.measurement import SlabMeasurementEngine, ThicknessMeasurement


@pytest.fixture
def mock_config(tmp_path):
    return Config(
        source="0",
        model_path="yolov8n.pt",
        output_dir=tmp_path / "logs",
        display=False,
    )


class TestEncodeFrameToB64:
    def test_encode_returns_valid_base64_string(self):
        frame = np.full((100, 200, 3), 128, dtype=np.uint8)
        encoded = encode_frame_to_b64(frame, quality=50)
        assert isinstance(encoded, str)
        assert len(encoded) > 0
        raw_bytes = base64.b64decode(encoded)
        arr = np.frombuffer(raw_bytes, dtype=np.uint8)
        decoded = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        assert decoded.shape == (100, 200, 3)

    def test_encode_handles_empty_or_zero_size(self):
        frame = np.zeros((0, 0, 3), dtype=np.uint8)
        encoded = encode_frame_to_b64(frame)
        assert encoded == ""


class TestBridgeAPI:
    def test_default_state(self):
        engine = SlabMeasurementEngine()
        api = BridgeAPI(engine)
        state = api.get_state()
        assert state["mode"] == "ORIGINAL"
        assert state["show_edges"] is True
        assert state["is_frozen"] is False
        assert state["cursor_x"] == 980
        assert state["cursor_y"] == 620

    def test_set_view_mode(self):
        api = BridgeAPI()
        res = api.set_view_mode("THERMAL")
        assert res["status"] == "ok"
        assert api.active_view_mode == "THERMAL"

    def test_toggle_edges(self):
        api = BridgeAPI()
        res = api.toggle_edges(False)
        assert res["show_edges"] is False
        assert api.show_edges is False

    def test_toggle_freeze(self):
        api = BridgeAPI()
        res = api.toggle_freeze(True)
        assert res["is_frozen"] is True
        assert api.is_frozen is True

    def test_set_cursor_clamps_coordinates(self):
        api = BridgeAPI()
        api.set_cursor(2500, -100)
        assert api.cursor_x == 1920
        assert api.cursor_y == 0
        api.set_cursor(500, 400)
        assert api.cursor_x == 500
        assert api.cursor_y == 400

    def test_toggle_fullscreen_delegates_to_window(self):
        api = BridgeAPI()
        mock_win = MagicMock()
        api._window = mock_win
        res = api.toggle_fullscreen()
        assert res["status"] == "ok"
        mock_win.toggle_fullscreen.assert_called_once()

    def test_close_window_delegates_to_window(self):
        api = BridgeAPI()
        mock_win = MagicMock()
        api._window = mock_win
        res = api.close_window()
        assert res["status"] == "ok"
        mock_win.destroy.assert_called_once()

    def test_operation_actions(self):
        api = BridgeAPI()
        assert api.start_measurement()["status"] == "ok"
        assert api.capture_image()["captured"] is True
        assert api.generate_report()["report_generated"] is True

    def test_connect_camera_with_ip_url(self):
        api = BridgeAPI()
        mock_app = MagicMock()
        api._app = mock_app
        res = api.connect_camera("rtsp://192.168.1.100:554/live")
        assert res["status"] == "ok"
        assert res["source"] == "rtsp://192.168.1.100:554/live"
        assert api.source_label == "IP: rtsp://192.168.1.100:554/live"
        mock_app.switch_source.assert_called_once_with("rtsp://192.168.1.100:554/live")

    def test_connect_camera_with_device_index(self):
        api = BridgeAPI()
        mock_app = MagicMock()
        api._app = mock_app
        res = api.connect_camera("0")
        assert res["status"] == "ok"
        mock_app.switch_source.assert_called_once_with(0)

    def test_set_limits(self):
        engine = SlabMeasurementEngine()
        api = BridgeAPI(engine)
        res = api.set_limits(180.0, 15.0, 250.0)
        assert res["status"] == "ok"
        assert engine.target_thickness_mm == 180.0
        assert engine.lower_limit_mm == 15.0
        assert engine.upper_limit_mm == 250.0

    def test_set_roi(self):
        api = BridgeAPI()
        res = api.set_roi(100, 50, 800, 600)
        assert res["status"] == "ok"
        assert api.roi == (100, 50, 800, 600)

    def test_open_video_dialog_selection(self):
        api = BridgeAPI()
        mock_win = MagicMock()
        mock_app = MagicMock()
        api._window = mock_win
        api._app = mock_app
        mock_win.create_file_dialog.return_value = ["/path/to/test_slab.mp4"]
        res = api.open_video_dialog()
        assert res["status"] == "ok"
        assert res["filename"] == "test_slab.mp4"
        mock_app.switch_source.assert_called_once_with("/path/to/test_slab.mp4")

    def test_open_video_dialog_cancelled(self):
        api = BridgeAPI()
        mock_win = MagicMock()
        api._window = mock_win
        mock_win.create_file_dialog.return_value = []
        res = api.open_video_dialog()
        assert res["status"] == "cancelled"

    def test_open_video_dialog_no_window(self):
        api = BridgeAPI()
        res = api.open_video_dialog()
        assert res["status"] == "error"

    def test_open_image_dialog_selection(self):
        api = BridgeAPI()
        mock_win = MagicMock()
        mock_app = MagicMock()
        api._window = mock_win
        api._app = mock_app
        mock_win.create_file_dialog.return_value = ["/path/to/slab_frame.jpg"]
        res = api.open_image_dialog()
        assert res["status"] == "ok"
        assert res["filename"] == "slab_frame.jpg"
        mock_app.switch_source.assert_called_once_with("/path/to/slab_frame.jpg")

    def test_open_image_dialog_cancelled(self):
        api = BridgeAPI()
        mock_win = MagicMock()
        api._window = mock_win
        mock_win.create_file_dialog.return_value = None
        res = api.open_image_dialog()
        assert res["status"] == "cancelled"

    def test_open_image_dialog_no_window(self):
        api = BridgeAPI()
        res = api.open_image_dialog()
        assert res["status"] == "error"

    def test_load_sample_video_and_image(self):
        api = BridgeAPI()
        mock_app = MagicMock()
        api._app = mock_app
        res_v = api.load_sample_video()
        assert res_v["status"] == "ok"
        assert "CAM01" in res_v["filename"]
        res_i = api.load_sample_image()
        assert res_i["status"] == "ok"
        assert "SLAB" in res_i["filename"]

    def test_colour_space_and_threshold_controls(self):
        api = BridgeAPI()
        res_c = api.set_colour_space("HSV")
        assert res_c["status"] == "ok"
        assert api.engine.colour_space == "hsv"

        res_t = api.set_threshold_mode("adaptive", 140)
        assert res_t["status"] == "ok"
        assert api.engine.threshold_mode == "adaptive"
        assert api.engine.manual_threshold == 140

        res_b = api.set_blur(7)
        assert res_b["status"] == "ok"
        assert api.engine.blur_ksize == 7

    def test_set_calibration(self):
        api = BridgeAPI()
        res = api.set_calibration(0.412)
        assert res["status"] == "ok"
        assert abs(api.engine.calibration - 0.412) < 1e-5
        res_err = api.set_calibration(-1.0)
        assert res_err["status"] == "error"

    def test_toggle_recording(self):
        api = BridgeAPI()
        res_on = api.toggle_recording()
        assert res_on["status"] == "ok"
        assert res_on["recording"] is True
        res_off = api.toggle_recording()
        assert res_off["status"] == "ok"
        assert res_off["recording"] is False


class TestWebviewApp:
    def test_initialization(self, mock_config):
        app = WebviewApp(mock_config)
        assert app.api is not None
        assert app._engine is not None

    def test_apply_view_modes(self, mock_config):
        app = WebviewApp(mock_config)
        frame = np.full((100, 100, 3), 150, dtype=np.uint8)
        meas = app._engine.measure(frame, cursor_x=50)
        for mode in ["ORIGINAL", "GRAY", "THRESHOLD", "DETECTION", "THERMAL", "MEASUREMENT"]:
            out = app._apply_view_mode(frame, mode, meas)
            assert out.shape == (100, 100, 3)

    def test_apply_view_modes_with_custom_spaces(self, mock_config):
        app = WebviewApp(mock_config)
        frame = np.full((100, 100, 3), 150, dtype=np.uint8)
        meas = app._engine.measure(frame, cursor_x=50)

        app.api.set_colour_space("hsv")
        app.api.set_threshold_mode("adaptive")
        out_hsv = app._apply_view_mode(frame, "THRESHOLD", meas)
        assert out_hsv.shape == (100, 100, 3)

        app.api.set_colour_space("lab")
        app.api.set_threshold_mode("manual", 120)
        out_lab = app._apply_view_mode(frame, "THRESHOLD", meas)
        assert out_lab.shape == (100, 100, 3)

    def test_apply_window_icon_does_not_crash(self, mock_config):
        app = WebviewApp(mock_config)
        app._apply_window_icon()

    def test_on_closing_sets_stop_event(self, mock_config):
        app = WebviewApp(mock_config)
        assert not app._stop_event.is_set()
        app._on_closing()
        assert app._stop_event.is_set()

    def test_toggle_recording_service(self, mock_config):
        app = WebviewApp(mock_config)
        res_on = app.toggle_recording()
        assert res_on["status"] == "ok"
        assert res_on["recording"] is True
        assert app.api.is_recording is True
        assert app._video_writer is not None
        assert Path(res_on["path"]).exists()

        res_off = app.toggle_recording()
        assert res_off["status"] == "ok"
        assert res_off["recording"] is False
        assert app.api.is_recording is False
        assert app._video_writer is None


class TestWebAssets:
    def test_html_contains_critical_elements(self):
        html_path = Path("vision/web/index.html")
        assert html_path.exists()
        content = html_path.read_text(encoding="utf-8")
        assert "Vision" in content or "VISION" in content
        assert "systrol_logo.png" in content
        assert "caliper-overlay" in content
        assert "profile-chart" in content
        assert "readout-mm" in content

    def test_html_contains_settings_and_theme_toggle(self):
        html_path = Path("vision/web/index.html")
        content = html_path.read_text(encoding="utf-8")
        assert "btn-settings" in content
        assert "settings-dropdown" in content
        assert "theme-toggle-chk" in content

    def test_html_contains_bottom_right_branding(self):
        html_path = Path("vision/web/index.html")
        content = html_path.read_text(encoding="utf-8")
        assert "bottom-right-branding" in content
        assert "systrol_ico_logo.png" in content

    def test_css_contains_black_scada_theme(self):
        css_path = Path("vision/web/style.css")
        assert css_path.exists()
        content = css_path.read_text(encoding="utf-8")
        assert "--bg-main: #000000;" in content
        assert "--cyan-accent:" in content

    def test_css_contains_responsive_media_queries(self):
        css_path = Path("vision/web/style.css")
        content = css_path.read_text(encoding="utf-8")
        assert "@media (min-width: 2200px)" in content
        assert "@media (min-width: 3200px)" in content

    def test_js_defines_telemetry_handler(self):
        js_path = Path("vision/web/app.js")
        assert js_path.exists()
        content = js_path.read_text(encoding="utf-8")
        assert "window.updateTelemetry" in content
        assert "renderProfileChart" in content

    def test_js_contains_dynamic_canvas_resolution(self):
        js_path = Path("vision/web/app.js")
        content = js_path.read_text(encoding="utf-8")
        assert "canvas.clientWidth" in content
        assert "canvas.clientHeight" in content

    def test_html_contains_detection_selectors(self):
        html_path = Path("vision/web/index.html")
        content = html_path.read_text(encoding="utf-8")
        assert "select-colour-space" in content
        assert "select-thresh-mode" in content

    def test_html_contains_measurement_points_table(self):
        html_path = Path("vision/web/index.html")
        content = html_path.read_text(encoding="utf-8")
        assert "points-table-wrapper" in content
        assert "points-table" in content

    def test_js_contains_points_table_renderer(self):
        js_path = Path("vision/web/app.js")
        content = js_path.read_text(encoding="utf-8")
        assert "renderPointsTable" in content
        assert "points-table-body" in content

    def test_html_contains_modal_dialog(self):
        html_path = Path("vision/web/index.html")
        content = html_path.read_text(encoding="utf-8")
        assert "scada-modal-backdrop" in content
        assert "scada-modal-window" in content
        assert "scada-modal-title" in content

    def test_js_contains_modal_system(self):
        js_path = Path("vision/web/app.js")
        content = js_path.read_text(encoding="utf-8")
        assert "showScadaModal" in content
        assert "showHelpModal" in content
        assert "showAboutModal" in content

    def test_html_and_js_recording_integration(self):
        html_path = Path("vision/web/index.html")
        content_html = html_path.read_text(encoding="utf-8")
        assert "badge-rec" in content_html

        js_path = Path("vision/web/app.js")
        content_js = js_path.read_text(encoding="utf-8")
        assert "toggle_recording" in content_js
        assert "recording-active" in content_js

    def test_js_contains_show_edges_toggle_behavior(self):
        js_path = Path("vision/web/app.js")
        content_js = js_path.read_text(encoding="utf-8")
        assert "btn-toggle-edges" in content_js
        assert "edgeGraphic" in content_js

    def test_html_contains_roi_toggle_button(self):
        html_path = Path("vision/web/index.html")
        content_html = html_path.read_text(encoding="utf-8")
        assert "btn-toggle-roi-box" in content_html

    def test_js_contains_roi_toggle_and_label(self):
        js_path = Path("vision/web/app.js")
        content_js = js_path.read_text(encoding="utf-8")
        assert "btn-toggle-roi-box" in content_js
        assert "ROI: SEARCH REGION" in content_js

    def test_html_contains_modal_watermark_and_pdf_button(self):
        html_path = Path("vision/web/index.html")
        content_html = html_path.read_text(encoding="utf-8")
        assert "modal-sticky-watermark" in content_html
        assert "btn-modal-open-pdf" in content_html

    def test_js_contains_features_manual_and_pdf_launcher(self):
        js_path = Path("vision/web/app.js")
        content_js = js_path.read_text(encoding="utf-8")
        assert "btn-modal-open-pdf" in content_js
        assert "open_pdf_manual" in content_js
        assert "TOPBAR AREA" in content_js
        assert "LEFT PANEL" in content_js

    def test_bridge_api_open_pdf_manual(self, monkeypatch, tmp_path):
        import vision.manual
        pdf_path = tmp_path / "test_manual.pdf"
        monkeypatch.setattr(vision.manual, "open_pdf_manual", lambda: pdf_path)
        api = BridgeAPI()
        res = api.open_pdf_manual()
        assert res["status"] == "ok"
        assert res["path"] == str(pdf_path)


class TestLetterboxFrame:
    def test_letterbox_same_size_returns_same(self):
        from vision.bridge import letterbox_frame
        frame = np.ones((1080, 1920, 3), dtype=np.uint8) * 128
        out = letterbox_frame(frame, 1920, 1080)
        assert out.shape == (1080, 1920, 3)
        assert np.array_equal(out, frame)

    def test_letterbox_4_to_3_preserves_aspect_ratio(self):
        from vision.bridge import letterbox_frame
        frame = np.ones((480, 640, 3), dtype=np.uint8) * 200
        out = letterbox_frame(frame, 1920, 1080)
        assert out.shape == (1080, 1920, 3)
        assert np.all(out[:, :240] == 0)
        assert np.all(out[:, 1680:] == 0)
        assert np.all(out[:, 240:1680] == 200)

    def test_letterbox_grayscale(self):
        from vision.bridge import letterbox_frame
        frame = np.ones((480, 640), dtype=np.uint8) * 255
        out = letterbox_frame(frame, 1920, 1080)
        assert out.shape == (1080, 1920)
        assert np.all(out[:, :240] == 0)
        assert np.all(out[:, 240:1680] == 255)

    def test_letterbox_none_or_empty(self):
        from vision.bridge import letterbox_frame
        assert letterbox_frame(None) is None
        empty = np.array([])
        assert letterbox_frame(empty).size == 0

    def test_letterbox_ultrawide_21_to_9_letterboxes_top_bottom(self):
        from vision.bridge import letterbox_frame
        frame = np.ones((1080, 2560, 3), dtype=np.uint8) * 180
        out = letterbox_frame(frame, 1920, 1080)
        assert out.shape == (1080, 1920, 3)
        assert np.all(out[:135, :] == 0)
        assert np.all(out[945:, :] == 0)
        assert np.all(out[135:945, :] == 180)

    def test_letterbox_portrait_9_to_16_pillarboxes_left_right(self):
        from vision.bridge import letterbox_frame
        frame = np.ones((1920, 1080, 3), dtype=np.uint8) * 220
        out = letterbox_frame(frame, 1920, 1080)
        assert out.shape == (1080, 1920, 3)
        assert np.all(out[:, :656] == 0)
        assert np.all(out[:, 1264:] == 0)
        assert np.all(out[:, 656:1264] == 220)


class TestBridgeShutdownAndRecording:
    def test_on_closing_clears_window_and_sets_stop_event(self, mock_config):
        app = WebviewApp(mock_config)
        app._window = object()
        app.api._window = app._window
        app._on_closing()
        assert app._stop_event.is_set() is True
        assert app._window is None
        assert app.api._window is None

    def test_toggle_recording_lifecycle(self, mock_config):
        app = WebviewApp(mock_config)
        res_start = app.toggle_recording()
        assert res_start["status"] == "ok"
        assert res_start["recording"] is True
        assert app.api.is_recording is True
        assert app._video_writer is not None
        rec_path = Path(res_start["path"])
        assert rec_path.parent.name == "recordings"

        res_stop = app.toggle_recording()
        assert res_stop["status"] == "ok"
        assert res_stop["recording"] is False
        assert app.api.is_recording is False
        assert app._video_writer is None
        if rec_path.exists():
            rec_path.unlink()


class TestUIElementsContract:
    def test_html_contains_hud_toolbar_and_symmetrical_watermarks(self):
        html_path = Path("vision/web/index.html")
        content = html_path.read_text(encoding="utf-8")
        assert "video-hud-overlay" in content
        assert "hud-status-text" in content
        assert "hud-fps-text" in content
        assert "hud-mode-text" in content
        assert "hud-thick-text" in content
        assert "watermark-brand" in content
        assert "watermark-brand-logo" in content
        assert "watermark-brand-text" in content
        assert "watermark-powered" in content
        assert "watermark-logo" in content
        assert "Vision_logo.png" in content
        assert "systrol_logo.png" in content




