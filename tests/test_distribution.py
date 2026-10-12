import re
import subprocess
import zipfile
from pathlib import Path

import pytest


def test_requirements_contains_gui_opencv():
    req_file = Path(__file__).resolve().parent.parent / "requirements.txt"
    content = req_file.read_text(encoding="utf-8")
    assert "opencv-python>=" in content
    assert "opencv-python-headless" not in content


def test_pyproject_contains_gui_opencv():
    pyproject_file = Path(__file__).resolve().parent.parent / "pyproject.toml"
    content = pyproject_file.read_text(encoding="utf-8")
    assert "opencv-python>=" in content
    assert "opencv-python-headless" not in content


def test_requirements_and_pyproject_dependencies_match():
    root = Path(__file__).resolve().parent.parent
    req_lines = [
        line.strip()
        for line in (root / "requirements.txt").read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    pyproject_text = (root / "pyproject.toml").read_text(encoding="utf-8")

    for req in req_lines:
        assert req in pyproject_text


def test_package_bat_exists_and_contains_exclusions():
    package_bat = Path(__file__).resolve().parent.parent / "package.bat"
    assert package_bat.exists()
    content = package_bat.read_text(encoding="utf-8")
    assert ".venv" in content
    assert ".git" in content
    assert "__pycache__" in content
    assert "Obj-col-detection.zip" in content


def test_run_bat_exists_and_contains_self_healing_check():
    run_bat = Path(__file__).resolve().parent.parent / "run.bat"
    assert run_bat.exists()
    content = run_bat.read_text(encoding="utf-8")
    assert '.venv\\Scripts\\python.exe" -c "import sys"' in content
    assert "rmdir /s /q .venv" in content
    assert "winget install Python.Python.3.12" in content


def test_package_bat_execution_generates_valid_archive(tmp_path):
    root = Path(__file__).resolve().parent.parent
    zip_path = root / "Obj-col-detection.zip"
    if zip_path.exists():
        zip_path.unlink()

    proc = subprocess.run(
        ["cmd", "/c", "package.bat"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    assert zip_path.exists()

    try:
        archive_size_mb = zip_path.stat().st_size / (1024 * 1024)
        assert archive_size_mb < 20.0

        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert any(name.endswith("requirements.txt") for name in namelist)
            assert any(name.endswith("run.bat") for name in namelist)
            assert any(name.endswith("package.bat") for name in namelist)
            assert any(name.endswith("mill_motion/__main__.py") or name.endswith("mill_motion\\__main__.py") for name in namelist)
            assert not any(".venv" in name for name in namelist)
            assert not any(".git/" in name or ".git\\" in name for name in namelist)
            assert not any("__pycache__" in name for name in namelist)
    finally:
        if zip_path.exists():
            zip_path.unlink()
