import re
import subprocess
import sys
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
    assert "Vision.zip" in content


def test_run_bat_exists_and_contains_self_healing_check():
    run_bat = Path(__file__).resolve().parent.parent / "run.bat"
    assert run_bat.exists()
    content = run_bat.read_text(encoding="utf-8")
    assert '.venv\\Scripts\\python.exe" -c "import sys"' in content
    assert "rmdir /s /q .venv" in content
    assert "winget install Python.Python.3.12" in content


def test_package_bat_execution_generates_valid_archive(tmp_path):
    if sys.platform != "win32":
        pytest.skip("Windows batch script execution requires win32")

    root = Path(__file__).resolve().parent.parent
    zip_path = root / "Vision.zip"
    if zip_path.exists():
        zip_path.unlink()

    proc = subprocess.run(
        ["cmd", "/c", "package.bat"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0
    if not zip_path.exists():
        zip_path = root / "Vision.zip"
    assert zip_path.exists()

    try:
        archive_size_mb = zip_path.stat().st_size / (1024 * 1024)
        assert archive_size_mb < 20.0

        with zipfile.ZipFile(zip_path, "r") as zf:
            namelist = zf.namelist()
            assert any(name.endswith("requirements.txt") for name in namelist)
            assert any(name.endswith("run.bat") for name in namelist)
            assert any(name.endswith("package.bat") for name in namelist)
            assert any(name.endswith("vision/__main__.py") or name.endswith("vision\\__main__.py") for name in namelist)
            assert not any(".venv" in name for name in namelist)
            assert not any(".git/" in name or ".git\\" in name for name in namelist)
            assert not any("__pycache__" in name for name in namelist)
    finally:
        if zip_path.exists():
            zip_path.unlink()


def test_installer_iss_version_matches_vision_version():
    root = Path(__file__).resolve().parent.parent
    iss_file = root / "installer" / "VisionSetup.iss"
    assert iss_file.exists()
    content = iss_file.read_text(encoding="utf-8")
    import vision
    match = re.search(r'#define\s+MyAppVersion\s+"([^"]+)"', content)
    assert match is not None
    assert match.group(1) == vision.__version__


def test_packaging_spec_configuration():
    root = Path(__file__).resolve().parent.parent
    spec_file = root / "packaging" / "vision.spec"
    assert spec_file.exists()
    content = spec_file.read_text(encoding="utf-8")
    assert "yolov8n.pt" in content
    assert "vision.ico" in content
    assert "app_manifest.xml" in content
    assert "ultralytics" in content


def test_app_manifest_is_valid_xml_with_dpi_awareness():
    import xml.etree.ElementTree as ET
    root = Path(__file__).resolve().parent.parent
    manifest_file = root / "packaging" / "app_manifest.xml"
    assert manifest_file.exists()
    tree = ET.parse(manifest_file)
    assert "assembly" in tree.getroot().tag
    content = manifest_file.read_text(encoding="utf-8")
    assert "PerMonitorV2" in content


def test_build_scripts_exist_and_contain_error_checks():
    root = Path(__file__).resolve().parent.parent
    build_exe = root / "scripts" / "build_exe.bat"
    build_installer = root / "scripts" / "build_installer.bat"
    assert build_exe.exists()
    assert build_installer.exists()
    assert "exit /b 1" in build_exe.read_text(encoding="utf-8")
    assert "exit /b 1" in build_installer.read_text(encoding="utf-8")
