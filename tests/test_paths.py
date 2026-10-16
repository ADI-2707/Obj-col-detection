import sys
from pathlib import Path
from unittest.mock import patch

from vision.paths import (
    get_default_capture_dir,
    get_default_log_dir,
    get_default_model_path,
    get_default_recording_dir,
    get_default_report_dir,
    get_resource_path,
    get_user_data_dir,
    is_frozen,
)


def test_is_frozen_default_is_false():
    assert is_frozen() is False


def test_is_frozen_when_attributes_present(monkeypatch):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", "/fake/meipass", raising=False)
    assert is_frozen() is True


def test_get_resource_path_in_development():
    res_path = get_resource_path()
    assert res_path.exists()
    assert (res_path / "pyproject.toml").exists()


def test_get_resource_path_with_relative_file():
    model_path = get_resource_path("yolov8n.pt")
    assert model_path.name == "yolov8n.pt"


def test_get_resource_path_frozen_mock(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    target = get_resource_path("weights.pt")
    assert target == tmp_path / "weights.pt"


def test_get_user_data_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    user_dir = get_user_data_dir("VisionTest")
    assert user_dir.exists()
    assert user_dir == tmp_path / "VisionTest"


def test_get_user_data_dir_windows_branch(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "win32")
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    user_dir = get_user_data_dir("VisionWin")
    assert user_dir == tmp_path / "VisionWin"


def test_get_user_data_dir_linux_branch(tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    user_dir = get_user_data_dir("VisionLinux")
    assert user_dir == tmp_path / "VisionLinux"


def test_get_default_log_dir_in_development():
    log_dir = get_default_log_dir()
    assert log_dir == Path("data/logs")


def test_get_default_log_dir_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    log_dir = get_default_log_dir()
    assert log_dir.parent == tmp_path / "Vision"
    assert log_dir.name == "logs"


def test_get_default_model_path():
    path = get_default_model_path()
    assert path.name == "yolov8n.pt"


def test_get_default_output_dirs_in_development():
    assert get_default_report_dir() == Path("data/reports")
    assert get_default_capture_dir() == Path("data/captures")
    assert get_default_recording_dir() == Path("data/recordings")


def test_get_default_output_dirs_when_frozen(monkeypatch, tmp_path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert get_default_report_dir() == tmp_path / "Vision" / "reports"
    assert get_default_capture_dir() == tmp_path / "Vision" / "captures"
    assert get_default_recording_dir() == tmp_path / "Vision" / "recordings"

