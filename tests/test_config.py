from pathlib import Path

import pytest

from mill_motion.config import Config


class TestConfigDefaults:
    def test_default_source_is_zero(self, default_config):
        assert default_config.source == 0

    def test_default_confidence(self, default_config):
        assert default_config.confidence_threshold == 0.25

    def test_default_ema_alpha(self, default_config):
        assert default_config.ema_alpha == 0.4

    def test_default_output_dir_is_path(self, default_config):
        assert isinstance(default_config.output_dir, Path)

    def test_default_display_enabled(self, default_config):
        assert default_config.display is True


class TestConfigValidation:
    def test_confidence_zero_raises(self):
        with pytest.raises(ValueError, match="confidence_threshold"):
            Config(confidence_threshold=0.0)

    def test_confidence_one_raises(self):
        with pytest.raises(ValueError, match="confidence_threshold"):
            Config(confidence_threshold=1.0)

    def test_confidence_negative_raises(self):
        with pytest.raises(ValueError, match="confidence_threshold"):
            Config(confidence_threshold=-0.1)

    def test_confidence_string_raises(self):
        with pytest.raises(TypeError, match="confidence_threshold"):
            Config(confidence_threshold="high")

    def test_ema_alpha_zero_raises(self):
        with pytest.raises(ValueError, match="ema_alpha"):
            Config(ema_alpha=0.0)

    def test_ema_alpha_negative_raises(self):
        with pytest.raises(ValueError, match="ema_alpha"):
            Config(ema_alpha=-0.5)

    def test_ema_alpha_one_is_valid(self):
        config = Config(ema_alpha=1.0)
        assert config.ema_alpha == 1.0

    def test_track_buffer_zero_raises(self):
        with pytest.raises(ValueError, match="track_buffer_length"):
            Config(track_buffer_length=0)

    def test_trail_length_zero_raises(self):
        with pytest.raises(ValueError, match="trail_length"):
            Config(trail_length=0)

    def test_stale_track_frames_zero_raises(self):
        with pytest.raises(ValueError, match="stale_track_frames"):
            Config(stale_track_frames=0)


class TestConfigOverrides:
    def test_custom_source_string(self):
        config = Config(source="video.mp4")
        assert config.source == "video.mp4"

    def test_custom_confidence(self):
        config = Config(confidence_threshold=0.5)
        assert config.confidence_threshold == 0.5

    def test_custom_output_dir(self):
        config = Config(output_dir=Path("/tmp/output"))
        assert config.output_dir == Path("/tmp/output")

    def test_display_disabled(self):
        config = Config(display=False)
        assert config.display is False

    def test_frozen_raises_on_mutation(self, default_config):
        with pytest.raises(AttributeError):
            default_config.source = 1
