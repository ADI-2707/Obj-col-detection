import base64
from pathlib import Path
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest

from orbix.bridge import BridgeAPI, WebviewApp, encode_frame_to_b64
from orbix.config import Config
from orbix.measurement import SlabMeasurementEngine, ThicknessMeasurement


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

    def test_apply_window_icon_does_not_crash(self, mock_config):
        app = WebviewApp(mock_config)
        app._apply_window_icon()

    def test_on_closing_sets_stop_event(self, mock_config):
        app = WebviewApp(mock_config)
        assert not app._stop_event.is_set()
        app._on_closing()
        assert app._stop_event.is_set()


class TestWebAssets:
    def test_html_contains_critical_elements(self):
        html_path = Path("orbix/web/index.html")
        assert html_path.exists()
        content = html_path.read_text(encoding="utf-8")
        assert "ORBIX" in content
        assert "systrol_logo.png" in content
        assert "caliper-overlay" in content
        assert "profile-chart" in content
        assert "readout-mm" in content

    def test_css_contains_white_theme(self):
        css_path = Path("orbix/web/style.css")
        assert css_path.exists()
        content = css_path.read_text(encoding="utf-8")
        assert "--bg-main: #ffffff;" in content
        assert "--blue-primary:" in content

    def test_js_defines_telemetry_handler(self):
        js_path = Path("orbix/web/app.js")
        assert js_path.exists()
        content = js_path.read_text(encoding="utf-8")
        assert "window.updateTelemetry" in content
        assert "renderProfileChart" in content
