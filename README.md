# Mill Motion Phase 1

Industrial computer-vision prototype for mill motion monitoring. Foundation for a future collision-risk monitoring system.

## What This Does

- Captures video frames from a webcam or video file
- Runs YOLOv8 object detection (COCO pretrained, CPU-only)
- Tracks detected objects across frames using ByteTrack
- Estimates image-plane velocity and direction per tracked object using exponential moving average smoothing
- Draws bounding boxes, track IDs, motion trails, and velocity arrows
- Renders a multi-panel industrial fullscreen dashboard with optical feed, telemetry, and collision radar
- Logs per-frame tracking data to CSV

## What This Does NOT Do

- Physical speed measurement: all velocities are in image-plane pixels per frame, not meters per second
- Domain-specific detection: the pretrained COCO model does not reliably recognize steel coils, cranes, rollers, or other mill-specific equipment
- Production collision-avoidance intervention: collision detection algorithms are currently in UI preview stage
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

## Industrial Fullscreen Dashboard Layout

The monitoring window automatically launches in borderless full-screen mode, styled with a high-clarity industrial white background, crisp black typography, branded corporate logo blue and green accents (from favicon), and basic red alert indicators:

```
+--------------------------------------------------------------------------------------------------+
| MILL MOTION // INDUSTRIAL MACHINE MONITOR   STATUS: TRACKING ACTIVE   FPS: 24.2  FRAME: 000805   |
+-----------------------------------------------------------------+--------------------------------+
| [ OPTICAL SENSOR FEED ]                                         | [ TARGET TELEMETRY ]           |
|                                                                 |                                |
|  - Camera Feed (Scaled aspect-ratio)                            |  - Target #01 // PERSON (91%)  |
|  - Bounding Box & Persistent Track ID                           |    Velocity: 14.2 px/f (SE)    |
|  - Centroid Reticles & Motion Trails                            |    Position: (340, 218) px     |
|  - Directional Velocity Arrows                                  |    Bounds: 210 x 380 px        |
|                                                                 |                                |
+-----------------------------------------------------------------+--------------------------------+
| [ COLLISION ASSESSMENT & TRAJECTORY RADAR ]                                                      |
|                                                                                                  |
|  [ 2D TRAJECTORY RADAR ]     [ THREAT METRICS & IMPACT ]          [ SYSTEM EVENT AUDIT STREAM ]  |
|   - Polar Scope (N/S/E/W)     - Alert Level: NOMINAL / HAZARD      - [AUDIT] Core Runtime Online |
|   - Target Blips & Headings   - Collision Probability (%)          - [AUDIT] Tracking Sector OK  |
|   - Spatial Separation Range  - Estimated Time-to-Impact (TTC)     - [AUDIT] Threat Matrix Armed |
|                               - Separation Distance & Buffer       - [AUDIT] Logging to Disk     |
+--------------------------------------------------------------------------------------------------+
```

### 1. Panel Breakdown
- **Top System Bar**: Displays system identification, tracking operational status, real-time FPS, sequential frame counter, and key controls.
- **Top-Left (Optical Sensor Feed)**: Houses the live camera stream scaled with aspect-ratio preservation. Overlays high-contrast bounding boxes, persistent track IDs, motion trails, and directional velocity arrows.
- **Top-Right (Target Telemetry Panel)**: Provides dedicated metric cards for each tracked object including class name, detection confidence percentage, instantaneous velocity (px/frame and px/s), compass heading, coordinate center, and dimensions.
- **Bottom (Collision Assessment & Trajectory Radar)**:
  - **Spatial Trajectory Radar**: 2D polar radar scope plotting active targets and their heading vectors relative to image-plane coordinates.
  - **Threat Metrics & Impact Window**: Real-time collision probability gauge, proximity threat level indicator (NOMINAL, CAUTION, CRITICAL), estimated time-to-collision (TTC), closest target pair distance, and safety buffer zone status.
  - **System Event Audit Stream**: Monospace audit log stream verifying sensor pipeline, tracking engine, and disk I/O health.

### 2. Runtime Keyboard Controls
- **`Q`** or **`ESC`**: Terminate tracking and flush CSV logs to disk.
- **`F`**: Toggle dynamically between Fullscreen and Windowed mode.

### 1. Velocity and Direction Calculation
- Centroid Tracking: On each frame, the center point (cx, cy) of each tracked object is computed from its bounding box.
- Displacement: Frame-to-frame pixel displacements (dx, dy) are calculated relative to the previous centroid position.
- Exponential Moving Average (EMA) Smoothing: To eliminate detector jitter, velocity components are filtered using an exponential moving average (default alpha = 0.4):
  smoothed_v = alpha * current_displacement + (1 - alpha) * previous_smoothed_v
- Speed Metric: Speed is calculated as the Euclidean magnitude:
  speed = sqrt(vx^2 + vy^2)
  This represents the image-plane speed in pixels per frame.
- Direction Angle: The movement vector angle is calculated using atan2(vy, vx) and converted to degrees (-180 to +180 relative to the image coordinate plane).

### 2. On-Screen Visual Indicators
- Bounding Boxes and Labels (Green): Outlines each tracked object with a green rectangle. Above each box, a label shows the persistent track identifier, detected class name, and confidence score (for example, ID:1 person 0.88).
- Motion Trails (Yellow Gradient): A fading polyline tracing up to the last 30 positions of the object centroid. Recent positions appear brighter and thicker, while older positions fade to indicate movement trajectory.
- Velocity Vectors (Red Arrow): A directional arrow drawn from the object centroid pointing along its current trajectory. The arrow length scales proportionally with speed (up to a maximum of 80 pixels). Arrows are hidden for stationary objects or noise below 1.0 pixel per frame.
- Heads-Up Display (White): Displays current frame number and real-time processing framerate (FPS) in the top-left corner.

### 3. Telemetry and CSV Logging
Every active track per frame is written to a timestamped CSV log file with the following columns:
- timestamp: UTC ISO-8601 recording timestamp
- frame_number: Sequential video frame index
- track_id: Persistent identifier assigned by ByteTrack
- class_id: Detection class index
- confidence: Detection confidence score (0.00 to 1.00)
- x1, y1, x2, y2: Bounding box corner coordinates in image pixels
- velocity_px_per_frame: Smoothed image-plane speed in pixels per frame
- direction_deg: Direction of movement in degrees

## Quick Start on Windows

1. Extract the project folder or clone the repository.
2. Double-click run.bat in the root folder.
3. The application will set up everything automatically and open the camera window.
4. Press q inside the video window (or Ctrl+C in terminal) to close and stop tracking.
5. The tracking data is automatically saved as a CSV file in data/logs/.

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
| `--windowed` | `false` | Launch in windowed mode instead of fullscreen |

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
