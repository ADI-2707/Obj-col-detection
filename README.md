# Mill Motion Phase 1

Industrial computer-vision prototype for mill motion monitoring. Foundation for a future collision-risk monitoring system.

## What This Does

- Captures video frames from a webcam or video file
- Runs YOLOv8 object detection (COCO pretrained, CPU-only)
- Tracks detected objects across frames using ByteTrack
- Estimates image-plane velocity and direction per tracked object using exponential moving average smoothing
- Draws bounding boxes, track IDs, motion trails, and velocity arrows
- Logs per-frame tracking data to CSV

## What This Does NOT Do

- Physical speed measurement: all velocities are in image-plane pixels per frame, not meters per second
- Domain-specific detection: the pretrained COCO model does not reliably recognize steel coils, cranes, rollers, or other mill-specific equipment
- Collision-risk analysis: this is planned for a future phase
- GPU acceleration: this prototype is CPU-only by design

## Requirements

- Windows 10/11 or Linux/macOS
- Python 3.11 or later
- A webcam or video file for input
- Internet access on first launch to download dependencies

## Technology Stack and Dependencies

| Component | Purpose | Version Constraint |
|-----------|---------|-------------------|
| Python | Runtime execution environment | >= 3.11 |
| ultralytics | YOLO object detection (CPU mode) | >= 8.3, < 9 |
| supervision | ByteTrack multi-object tracking | >= 0.25, < 1 |
| opencv-python-headless | Video capture and visual overlay rendering | >= 4.10, < 5 |
| torch | Neural network tensor inference backend | Auto-resolved by ultralytics |
| pytest (dev) | Test runner for test suite execution | >= 8.0, < 9 |

## Quick Start on Windows

1. Extract the project folder or clone the repository.
2. Double-click run.bat in the root folder.
3. The application will set up everything automatically and open the camera window.

## Launcher Behavior by Scenario

The run.bat script handles common runtime environments automatically:

### 1. First-Time Launch
- Automatically verifies Python availability.
- Creates an isolated virtual environment (.venv) inside the project folder.
- Installs all dependencies from requirements.txt via pip.
- Starts the camera application and opens the Mill Motion display window.

### 2. Subsequent Launches
- Detects the existing virtual environment.
- Skips setup entirely and starts the application immediately.

### 3. Python Not Installed
- Uses Windows Package Manager (winget) to install Python 3.12 automatically.
- Once complete, prompts to close and reopen run.bat so the new system PATH takes effect.
- If winget is unavailable, opens https://www.python.org/downloads/ in the default browser and displays installation instructions.

### 4. Older Python Version Installed (below 3.11)
- Verifies that Python meets the minimum version requirement (sys.version_info >= 3.11).
- If the default Python is older (such as 3.8, 3.9, or 3.10), checks for a newer parallel installation via the Windows Python Launcher (py -3).
- If no compatible version exists, triggers the automatic Python 3.12 installation via winget.

### 5. Python Installed Without Add to PATH Checked
- Automatically falls back to the Windows Python Launcher (py -3), which is installed by default in C:\Windows\ and discovers Python via the Windows Registry.

### 6. Webcam Active and Functional
- Opens the live camera feed with an overlay display.
- Renders green bounding boxes with track IDs and confidence scores.
- Renders fading motion trails tracking recent centroid movement.
- Renders red velocity vectors indicating direction and speed in pixels per frame.
- Displays a real-time frame counter and FPS indicator.

### 7. Webcam Missing, Disconnected, or In Use
- Displays a clear error message indicating the camera device index could not be opened.
- Pauses the console window so the user can read the error message.
- Exits cleanly without crashing or hanging.

### 8. Webcam Lens Covered or In Dark Environment
- Reads frames normally without crashing.
- Reports zero detections when confidence thresholds are not met.
- Continues updating the HUD and logs empty frame records to CSV.

### 9. Webcam Disconnected During Execution
- Detects end of stream, terminates the processing loop cleanly, flushes the CSV log to disk, and closes all open windows.

### 10. Stopping the Application
- Press q inside the Mill Motion video window.
- Or press Ctrl+C in the terminal.
- The script flushes the log, displays the total processed frame count and CSV file path, and pauses before closing.

## Manual Terminal Usage

If preferred, the application can be run directly from any terminal or Command Prompt.

### Installation

```
pip install -r requirements.txt
```

For development and running the test suite:

```
pip install -e ".[dev]"
```

### Running the Application

Default webcam:

```
python -m mill_motion --source 0
```

Using a video file:

```
python -m mill_motion --source "path/to/video.mp4"
```

Headless mode (no display window, logs to CSV only):

```
python -m mill_motion --no-display
```

Custom confidence threshold:

```
python -m mill_motion --confidence 0.4
```

### CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--source` | `0` | Camera index (integer) or path to video file |
| `--model` | `yolov8n.pt` | Path to YOLO model weights |
| `--confidence` | `0.25` | Minimum detection confidence threshold |
| `--output-dir` | `data/logs` | Directory for CSV log output |
| `--no-display` | `false` | Disable visualization window |

## Running Tests

Execute the full automated test suite:

```
python -m pytest tests/ -v
```

## Project Structure

```
mill_motion/
    __init__.py        Package version
    __main__.py        CLI entry point
    config.py          Centralized configuration
    capture.py         Video frame source
    detector.py        YOLO detection wrapper
    tracker.py         ByteTrack tracking wrapper
    motion.py          Image-plane velocity estimation
    logger.py          CSV data logging
    visualizer.py      Frame annotation and overlay
    pipeline.py        Processing pipeline orchestration
tests/                 Unit and integration tests
data/logs/             CSV output directory
run.bat                Self-installing Windows launcher script
```

## Architecture

```
Camera/File -> FrameSource -> Detector -> ObjectTracker -> MotionEstimator -> CSVLogger
                                                                           -> Visualizer
```

Each module is independent and communicates through standard data structures. The Pipeline class orchestrates the flow.

## Limitations

- Frame rate dependent: velocity values change if camera FPS changes
- Single camera only: no multi-view support
- COCO classes only: 80 object categories, none specific to industrial equipment
- No calibration: pixel measurements have no physical scale
- CPU inference: expect 5-15 FPS depending on hardware and model size

## License

MIT
