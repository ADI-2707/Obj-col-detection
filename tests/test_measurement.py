import numpy as np

from orbix.measurement import SlabMeasurementEngine, ThicknessMeasurement


def test_measurement_engine_synthetic_frame():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=640, height=360, frame_number=0)
    assert frame.shape == (360, 640, 3)
    assert frame.dtype == np.uint8


def test_measurement_engine_measure():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=800, height=500, frame_number=1)
    result = engine.measure(frame, roi=(50, 50, 700, 400), cursor_x=400)

    assert isinstance(result, ThicknessMeasurement)
    assert result.x_cursor == 400
    assert result.top_y < result.bottom_y
    assert result.thickness_px > 0
    assert result.thickness_mm > 0
    assert result.min_mm <= result.avg_mm <= result.max_mm
    assert 0.0 <= result.confidence_pct <= 100.0
    assert len(result.top_edges) == 700
    assert len(result.bottom_edges) == 700


def test_measurement_engine_custom_calibration():
    engine = SlabMeasurementEngine(calibration_mm_per_px=0.5)
    frame = engine.generate_synthetic_slab_frame(width=400, height=300)
    result = engine.measure(frame)
    assert abs(result.thickness_mm - result.thickness_px * 0.5) < 1e-4


def test_measurement_engine_x_cursor_alias():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=400, height=300)
    result = engine.measure(frame, x_cursor=250)
    assert result.x_cursor == 250

