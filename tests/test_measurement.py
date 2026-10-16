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


def test_temporal_filter_convergence():
    engine = SlabMeasurementEngine()
    frame1 = engine.generate_synthetic_slab_frame(width=400, height=300, frame_number=0)
    frame2 = engine.generate_synthetic_slab_frame(width=400, height=300, frame_number=1)
    res1 = engine.measure(frame1)
    res2 = engine.measure(frame2)
    assert engine._prev_cur_top is not None
    assert engine._prev_cur_bot is not None
    assert abs(res2.top_y - res1.top_y) < 5.0
    assert abs(res2.bottom_y - res1.bottom_y) < 5.0


def test_engine_reset_state():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=400, height=300, frame_number=0)
    engine.measure(frame)
    assert engine._prev_top_edges is not None
    engine.reset_state()
    assert engine._prev_top_edges is None
    assert engine._prev_bottom_edges is None
    assert engine._prev_cur_top is None


def test_outlier_noise_rejection():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=400, height=300, frame_number=0)
    frame[10:25, 150:156] = (255, 255, 255)
    result = engine.measure(frame)
    assert result.is_valid is True
    assert result.thickness_mm > 0
    assert result.max_mm < 350.0


def test_two_point_calibration_accuracy():
    engine = SlabMeasurementEngine(calibration_mm_per_px=0.34757)
    dist_px = 226.3
    known_mm = 78.0
    derived_scale = known_mm / dist_px
    engine.calibration = derived_scale
    assert abs(engine.calibration - 0.34467) < 1e-4
    measured_thickness_mm = dist_px * engine.calibration
    assert abs(measured_thickness_mm - 78.0) < 1e-4


def test_measurement_completely_black_frame():
    engine = SlabMeasurementEngine()
    black_frame = np.zeros((720, 1280, 3), dtype=np.uint8)
    result = engine.measure(black_frame)
    assert result.is_valid is False
    assert result.confidence_pct == 0.0
    assert result.status_text == "LOW CONFIDENCE"


def test_measurement_completely_white_frame():
    engine = SlabMeasurementEngine()
    white_frame = np.full((720, 1280, 3), 255, dtype=np.uint8)
    result = engine.measure(white_frame)
    assert result.is_valid is False
    assert result.confidence_pct == 0.0
    assert result.status_text == "LOW CONFIDENCE"


def test_measurement_dynamic_roi_size_change():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=1000, height=600)
    res1 = engine.measure(frame, roi=(50, 50, 800, 500))
    assert len(res1.top_edges) == 800
    res2 = engine.measure(frame, roi=(50, 50, 400, 500))
    assert len(res2.top_edges) == 400
    assert res2.is_valid is True


def test_measurement_cursor_extreme_out_of_bounds():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=800, height=600)
    res_neg = engine.measure(frame, roi=(100, 100, 600, 400), cursor_x=-99999)
    assert 100 <= res_neg.x_cursor < 700
    res_pos = engine.measure(frame, roi=(100, 100, 600, 400), cursor_x=99999)
    assert 100 <= res_pos.x_cursor < 700


def test_measurement_minimal_10x10_roi():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=200, height=200)
    result = engine.measure(frame, roi=(10, 10, 10, 10))
    assert isinstance(result, ThicknessMeasurement)
    assert len(result.top_edges) == 10
    assert len(result.bottom_edges) == 10


def test_measurement_heavy_scale_occlusion():
    engine = SlabMeasurementEngine()
    frame = engine.generate_synthetic_slab_frame(width=600, height=400, frame_number=0)
    frame[140:180, 200:350] = (15, 12, 10)
    result = engine.measure(frame, roi=(50, 50, 500, 300))
    assert result.is_valid is True
    assert result.thickness_mm > 0.0
    assert result.max_mm < 350.0



