# Vision - Smart Material Management System

Industrial computer-vision platform for hot-metal slab thickness measurement, edge detection, and real-time mill material telemetry.

## System Overview

Vision is a modern industrial computer-vision system developed by Systrol Vision for manufacturing and metal-processing mills. It provides high-precision edge detection, pixel-to-millimeter dimensional calibration, real-time cross-sectional thickness profiling, video recording, and automated reporting.

The application features a modern desktop SCADA interface powered by an embedded WebView runtime, paired with a high-performance computer-vision backend and an OpenCV fallback visualizer.

## Core Capabilities

- Hot-Metal Edge Detection: Accurately identifies top and bottom slab contours using Otsu, adaptive, and manual intensity thresholding.
- Dimensional Calibration: Calibrates pixels to millimeters for precise real-world physical thickness measurements.
- Real-Time Thickness Profiling: Computes continuous cross-sectional profile arrays and calculates instantaneous, minimum, maximum, mean, and standard deviation thickness metrics.
- Multiple Visualization Modes:
  - ORIGINAL: Clean camera or video input stream.
  - GRAY: Monochromatic luminance view.
  - THRESHOLD: Binary segmented slab profile across Grayscale, HSV, or LAB color spaces.
  - DETECTION: Edge gradient view highlighting material boundaries.
  - THERMAL: Inferno pseudo-color mapping for thermal contrast inspection.
  - MEASUREMENT: Caliper overlays showing tracked edges, measurement cursor, and tolerance zones.
- Interactive Caliper & ROI Selection: Allows operators to drag bounding regions of interest (ROI) and position caliper measurement cursors anywhere on the live stream.
- DVR Video Recording: Captures live operational footage with telemetry directly into high-compression AVI files.
- Telemetry Logging: Records per-frame measurement statistics, calibration data, and system metrics to CSV files.
- PDF Manual Generator: Built-in automated generator creates a multi-page, formatted PDF operations and features manual.
- Modern SCADA Dashboard: High-contrast dark and light themes, responsive layout, digital clock, real-time FPS counter, and status indicators.

## System Requirements

- Operating System: Windows 10/11 (64-bit) or Linux/macOS
- Python: Version 3.11 or later
- Hardware: Standard USB webcam, industrial camera, or video file source
- Internet Access: Required only during initial setup for package resolution

## Technology Stack

| Component | Purpose | Version Constraint |
|---|---|---|
| Python | Execution runtime | >= 3.11 |
| pywebview | Modern SCADA web-based desktop application framework | >= 5.0 |
| opencv-python | Video decoding, computer vision transforms, and edge detection | >= 4.10, < 5 |
| ultralytics | YOLOv8 object detection inference engine | >= 8.3, < 9 |
| supervision | ByteTrack multi-object tracking and visual annotations | >= 0.25, < 1 |
| reportlab | Automated PDF operation manual generator | >= 4.0 |
| pytest (dev) | Test framework for unit and regression testing | >= 8.0, < 9 |
| PyInstaller | Standalone Windows executable bundle compiler | >= 6.5 |
| Inno Setup | Windows installer package compiler | 6.x |

## Quick Start on Windows

The easiest way to start Vision is using the self-installing launcher:

1. Clone or download the repository.
2. Double-click `run.bat` in the project root.
3. The launcher automatically:
   - Verifies the Python environment (installs Python 3.12 via winget if missing).
   - Initializes an isolated virtual environment (`.venv`).
   - Installs dependencies from `requirements.txt`.
   - Starts the Vision desktop application.

To close the application, close the window or press Ctrl+C in the console.

## Manual Terminal Setup

For development or command-line deployment:

### 1. Create and Activate Virtual Environment

Windows:
```powershell
python -m venv .venv
.venv\Scripts\activate
```

Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

Standard dependencies:
```bash
pip install -r requirements.txt
```

Development dependencies (including pytest):
```bash
pip install -e ".[dev]"
```

### 3. Running the Application

Launch with default webcam (index 0):
```bash
python -m vision --source 0
```

Launch with a recorded video file:
```bash
python -m vision --source "path/to/video.mp4"
```

Launch in windowed mode:
```bash
python -m vision --windowed
```

Launch in headless mode (no display, CSV telemetry only):
```bash
python -m vision --no-display
```

Custom confidence threshold:
```bash
python -m vision --confidence 0.4
```

### 4. CLI Arguments Reference

| Argument | Default | Description |
|---|---|---|
| `--source` | `0` | Camera index (integer) or file path to video stream |
| `--model` | `yolov8n.pt` | Path to YOLO detection model weights |
| `--confidence` | `0.25` | Minimum detection confidence threshold |
| `--output-dir` | `data/logs` | Destination directory for telemetry CSV files |
| `--no-display` | `false` | Run headlessly without opening the user interface |
| `--windowed` | `false` | Launch in windowed mode instead of fullscreen |

## Project Structure

```
vision/
    __init__.py        Package version declaration
    __main__.py        CLI entry point and argument parsing
    bridge.py          Webview API bridge, telemetry worker, and window management
    capture.py         Video frame source reader and validation
    config.py          Centralized system configuration schema
    detector.py        YOLOv8 inference wrapper
    logger.py          Telemetry and measurement CSV logger
    manual.py          ReportLab printable PDF manual builder
    measurement.py     Slab edge detection, calibration, and thickness profiling
    motion.py          Centroid velocity smoothing and heading calculation
    paths.py           Cross-platform resource and user data path resolution
    pipeline.py        Core vision loop and OpenCV fallback window
    tracker.py         ByteTrack tracking wrapper
    visualizer.py      OpenCV fallback HUD rendering and drawing routines
    web/
        index.html     SCADA interface structure and modals
        style.css      SCADA styling (dark/light themes, layout, gauges)
        app.js         Frontend telemetry handling, charts, caliper, and controls
        vision_mark.png High-resolution aperture mark icon
        Vision_logo.png Brand header and watermark logo
tests/                 Automated test suites (200 test cases)
assets/                Icons, favicon, and brand assets
installer/             Inno Setup installer scripts (VisionSetup.iss)
packaging/             PyInstaller specifications (vision.spec) and app manifest
scripts/               Build, packaging, and version bumping scripts
run.bat                Self-healing Windows launcher
package.bat            Automated distribution archive creator
```

## Running the Test Suite

Execute the full automated pytest suite:

```bash
pytest -v
```

All 200 unit, regression, UI contract, and distribution tests will execute.

## Building Executables and Installers

### 1. Standalone Executable
Compile a portable, standalone executable directory inside `dist/Vision/`:

```cmd
scripts\build_exe.bat
```

### 2. Windows Setup Installer
Compile a complete Windows setup installer inside `dist/`:

```cmd
scripts\build_installer.bat
```

### 3. Source Distribution Archive
Generate a clean, redistributable zip package (`Vision.zip`):

```cmd
package.bat
```

## Automated CI/CD and Versioning

- Continuous Integration (`.github/workflows/ci.yml`): Runs on every push and pull request across Ubuntu and Windows runners on Python 3.11 and 3.12.
- Automated Version Bumping (`.github/workflows/bump_version.yml`): Bumps version numbers across `vision/__init__.py`, `pyproject.toml`, `VisionSetup.iss`, `app_manifest.xml`, `index.html`, and `app.js` based on pull request labels (major, minor, patch).
- Automated Release Builder (`.github/workflows/release_installer.yml`): Builds and attaches Windows installers to GitHub Releases on version tags.

## License

MIT License. Copyright (c) 2026 Systrol Vision.
