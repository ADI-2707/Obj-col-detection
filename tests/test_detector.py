import pytest

from vision.detector import Detector, DetectorError


class TestDetectorInit:
    def test_missing_extension_raises(self):
        with pytest.raises(DetectorError, match="Invalid model path"):
            Detector(model_path="no_extension_model")

    def test_invalid_model_file_raises(self):
        with pytest.raises(DetectorError, match="Failed to load"):
            Detector(model_path="does_not_exist_xyz.pt")
