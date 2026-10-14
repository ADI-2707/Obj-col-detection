from dataclasses import dataclass, field
from pathlib import Path

from vision.paths import get_default_log_dir


@dataclass(frozen=True)
class Config:
    source: int | str = 0
    model_path: str = "yolov8n.pt"
    confidence_threshold: float = 0.25
    track_buffer_length: int = 30
    ema_alpha: float = 0.4
    trail_length: int = 30
    stale_track_frames: int = 60
    output_dir: Path = field(default_factory=get_default_log_dir)
    display: bool = True
    fullscreen: bool = True

    def __post_init__(self):
        if not isinstance(self.fullscreen, bool):
            raise TypeError(
                f"fullscreen must be a boolean, "
                f"got {type(self.fullscreen).__name__}"
            )

        if isinstance(self.confidence_threshold, (int, float)):
            if not 0.0 < self.confidence_threshold < 1.0:
                raise ValueError(
                    f"confidence_threshold must be between 0 and 1 exclusive, "
                    f"got {self.confidence_threshold}"
                )
        else:
            raise TypeError(
                f"confidence_threshold must be a number, "
                f"got {type(self.confidence_threshold).__name__}"
            )

        if isinstance(self.ema_alpha, (int, float)):
            if not 0.0 < self.ema_alpha <= 1.0:
                raise ValueError(
                    f"ema_alpha must be between 0 exclusive and 1 inclusive, "
                    f"got {self.ema_alpha}"
                )
        else:
            raise TypeError(
                f"ema_alpha must be a number, "
                f"got {type(self.ema_alpha).__name__}"
            )

        if not isinstance(self.track_buffer_length, int) or self.track_buffer_length < 1:
            raise ValueError(
                f"track_buffer_length must be a positive integer, "
                f"got {self.track_buffer_length}"
            )

        if not isinstance(self.trail_length, int) or self.trail_length < 1:
            raise ValueError(
                f"trail_length must be a positive integer, "
                f"got {self.trail_length}"
            )

        if not isinstance(self.stale_track_frames, int) or self.stale_track_frames < 1:
            raise ValueError(
                f"stale_track_frames must be a positive integer, "
                f"got {self.stale_track_frames}"
            )

        if not isinstance(self.output_dir, Path):
            object.__setattr__(self, "output_dir", Path(self.output_dir))
