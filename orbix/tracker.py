import warnings

import supervision as sv


class ObjectTracker:
    def __init__(self, track_buffer_length: int = 30):
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=FutureWarning)
            self._tracker = sv.ByteTrack(
                lost_track_buffer=track_buffer_length,
            )

    def update(self, detections: sv.Detections) -> sv.Detections:
        if len(detections) == 0:
            return detections

        return self._tracker.update_with_detections(detections)

    def reset(self):
        self._tracker.reset()
