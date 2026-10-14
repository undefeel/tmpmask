from __future__ import annotations

from datetime import datetime
from pathlib import Path

import cv2
import numpy as np


def timestamp_name(prefix: str, ext: str, now: datetime) -> str:
    """Generate timestamped filename without directory, e.g. tmpmask_20261014_153012.png."""
    clean_ext = ext.lstrip(".")
    formatted_ts = now.strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{formatted_ts}.{clean_ext}"


def _get_unique_path(output_dir: Path, filename: str) -> Path:
    """Resolve collision by appending _1, _2, etc. before the extension if file exists."""
    dest = output_dir / filename
    if not dest.exists():
        return dest

    stem = dest.stem
    suffix = dest.suffix
    counter = 1
    while True:
        candidate = output_dir / f"{stem}_{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


def save_screenshot(frame: np.ndarray, output_dir: Path, now: datetime | None = None) -> Path:
    """Save an image frame as PNG to output_dir with collision resolution."""
    output_dir.mkdir(parents=True, exist_ok=True)
    current_time = now if now is not None else datetime.now()
    base_name = timestamp_name("tmpmask", "png", current_time)
    file_path = _get_unique_path(output_dir, base_name)

    success = cv2.imwrite(str(file_path), frame)
    if not success:
        raise RuntimeError(f"Failed to write screenshot to {file_path}")

    return file_path


class Recorder:
    """Video recorder using cv2.VideoWriter with mp4v codec."""

    def __init__(self, output_dir: Path, fps: float = 30.0) -> None:
        self.output_dir = output_dir
        self.fps = float(fps)
        self._writer: cv2.VideoWriter | None = None
        self._path: Path | None = None
        self._frame_size: tuple[int, int] | None = None

    @property
    def is_recording(self) -> bool:
        return self._writer is not None

    @property
    def path(self) -> Path | None:
        return self._path

    def start(self, frame_size: tuple[int, int], now: datetime | None = None) -> Path:
        if self.is_recording:
            raise RuntimeError("Recorder is already recording")

        self.output_dir.mkdir(parents=True, exist_ok=True)
        current_time = now if now is not None else datetime.now()
        base_name = timestamp_name("tmpmask", "mp4", current_time)
        file_path = _get_unique_path(self.output_dir, base_name)

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(file_path), fourcc, self.fps, frame_size)
        if not writer.isOpened():
            raise RuntimeError(f"Failed to open video writer for {file_path}")

        self._writer = writer
        self._path = file_path
        self._frame_size = frame_size
        return file_path

    def write(self, frame: np.ndarray) -> None:
        if not self.is_recording or self._writer is None or self._frame_size is None:
            return

        target_w, target_h = self._frame_size
        height, width = frame.shape[:2]
        if (width, height) != (target_w, target_h):
            frame = cv2.resize(frame, (target_w, target_h))

        self._writer.write(frame)

    def stop(self) -> Path | None:
        if not self.is_recording or self._writer is None:
            return None

        self._writer.release()
        self._writer = None
        self._frame_size = None
        return self._path
