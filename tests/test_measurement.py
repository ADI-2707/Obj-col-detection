import numpy as np

from vision.measurement import SlabMeasurementEngine, ThicknessMeasurement


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


def test_thickness_profile_mm_property():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=400, height=300)
    result = engine.measure(frame)
    profile = result.thickness_profile_mm
    assert isinstance(profile, list)
    assert len(profile) > 0
    assert all(isinstance(v, float) for v in profile)


def test_measurement_tolerance_in_spec():
    engine = SlabMeasurementEngine()
    engine.lower_limit_mm = 10.0
    engine.upper_limit_mm = 300.0
    frame = engine.generate_synthetic_slab_frame(width=600, height=400)
    result = engine.measure(frame)
    assert result.is_normal is True
    assert result.status_text == "NORMAL"
    assert result.warning_text == ""


def test_measurement_tolerance_out_of_spec_upper():
    engine = SlabMeasurementEngine()
    engine.lower_limit_mm = 10.0
    engine.upper_limit_mm = 30.0
    frame = engine.generate_synthetic_slab_frame(width=600, height=400)
    result = engine.measure(frame)
    assert result.is_normal is False
    assert result.status_text == "OUT OF SPEC"
    assert "tolerance" in result.warning_text.lower()


def test_measurement_tolerance_out_of_spec_lower():
    engine = SlabMeasurementEngine()
    engine.lower_limit_mm = 200.0
    engine.upper_limit_mm = 300.0
    frame = engine.generate_synthetic_slab_frame(width=600, height=400)
    result = engine.measure(frame)
    assert result.is_normal is False
    assert result.status_text == "OUT OF SPEC"


def test_measurement_engine_roi_boundary_clamping():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=400, height=300)
    result = engine.measure(frame, roi=(-100, -50, 1000, 800))
    assert isinstance(result, ThicknessMeasurement)
    assert result.x_cursor >= 0
    assert len(result.top_edges) == 400


def test_measurement_empty_or_tiny_frame():
    engine = SlabMeasurementEngine()
    tiny_frame = np.zeros((10, 10, 3), dtype=np.uint8)
    result = engine.measure(tiny_frame)
    assert isinstance(result, ThicknessMeasurement)
    assert result.is_valid is False


def test_measurement_color_spaces():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=400, height=300)
    for space in ["grayscale", "hsv", "lab"]:
        engine.colour_space = space
        result = engine.measure(frame)
        assert isinstance(result, ThicknessMeasurement)
        assert result.thickness_mm > 0


def test_measurement_threshold_modes():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=400, height=300)
    for mode in ["otsu", "adaptive", "manual"]:
        engine.threshold_mode = mode
        engine.manual_threshold = 120
        result = engine.measure(frame)
        assert isinstance(result, ThicknessMeasurement)
        assert result.thickness_mm > 0


def test_measurement_custom_blur():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=400, height=300)
    engine.blur_ksize = 7
    result_odd = engine.measure(frame)
    assert isinstance(result_odd, ThicknessMeasurement)

    engine.blur_ksize = 6
    result_even = engine.measure(frame)
    assert isinstance(result_even, ThicknessMeasurement)



