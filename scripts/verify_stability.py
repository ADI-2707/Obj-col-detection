import os
import sys
from pathlib import Path
import cv2
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from vision.measurement import SlabMeasurementEngine


def run_benchmark():
    video_path = r"C:\Users\hp\Downloads\WhatsApp Video 2026-10-15 at 19.12.12.mp4"
    engine = SlabMeasurementEngine(calibration_mm_per_px=0.34757)
    roi = (150, 39, 1549, 870)
    cursor_x = 1067

    thicknesses = []

    if os.path.exists(video_path):
        cap = cv2.VideoCapture(video_path)
        cap.set(cv2.CAP_PROP_POS_FRAMES, 100)
        for _ in range(300):
            ret, frame = cap.read()
            if not ret:
                break
            m = engine.measure(frame, roi=roi, cursor_x=cursor_x)
            thicknesses.append(m.thickness_mm)
        cap.release()
    else:
        for f in range(300):
            frame = engine.generate_synthetic_slab_frame(width=1920, height=1080, frame_number=f)
            m = engine.measure(frame, roi=roi, cursor_x=cursor_x)
            thicknesses.append(m.thickness_mm)

    arr = np.array(thicknesses, dtype=np.float64)
    deltas = np.abs(np.diff(arr))
    mean_delta = float(np.mean(deltas))
    max_delta = float(np.max(deltas))
    std_dev = float(np.std(arr))

    print(f"Frames analyzed: {len(arr)}")
    print(f"Mean thickness: {np.mean(arr):.2f} mm")
    print(f"Std dev: {std_dev:.3f} mm")
    print(f"Mean frame-to-frame delta: {mean_delta:.3f} mm")
    print(f"Max frame-to-frame delta: {max_delta:.3f} mm")

    assert mean_delta < 0.5, f"Frame-to-frame jitter too high: {mean_delta} mm"
    print("Stability benchmark PASSED")


if __name__ == "__main__":
    run_benchmark()
