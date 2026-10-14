import os
import sys
from pathlib import Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))


def get_resource_path(relative_path: str | Path = "") -> Path:
    if is_frozen():
        base_path = Path(getattr(sys, "_MEIPASS"))
    else:
        base_path = Path(__file__).resolve().parent.parent
    if relative_path:
        return base_path / relative_path
    return base_path


def get_user_data_dir(app_name: str = "Vision") -> Path:
    if sys.platform == "win32":
        local_app_data = os.environ.get("LOCALAPPDATA")
        if local_app_data:
            base_dir = Path(local_app_data)
        else:
            base_dir = Path.home() / "AppData" / "Local"
    else:
        xdg_data = os.environ.get("XDG_DATA_HOME")
        if xdg_data:
            base_dir = Path(xdg_data)
        else:
            base_dir = Path.home() / ".local" / "share"

    data_dir = base_dir / app_name
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


def get_default_model_path() -> Path:
    return get_resource_path("yolov8n.pt")


def get_default_log_dir() -> Path:
    if is_frozen():
        log_dir = get_user_data_dir() / "logs"
    else:
        log_dir = Path("data/logs")
    return log_dir
