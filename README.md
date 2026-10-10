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

- Python 3.11 or later
- A webcam or video file for input

## Installation

```
git clone <repository-url>
cd Obj-col-detection
pip install -r requirements.txt
```

For development (includes pytest):

```
pip install -e ".[dev]"
```

## Usage

Run from terminal:

```
python -m mill_motion --source 0
```

### CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--source` | `0` | Camera index (integer) or path to video file |
| `--model` | `yolov8n.pt` | Path to YOLO model weights |
| `--confidence` | `0.25` | Minimum detection confidence threshold |
| `--output-dir` | `data/logs` | Directory for CSV log output |
| `--no-display` | `false` | Disable visualization window |

Press `q` in the display window to stop, or use `Ctrl+C` in the terminal.

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
