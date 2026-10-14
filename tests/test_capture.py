from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import cv2
import numpy as np
import pytest

from tmpmask.capture import Recorder, save_screenshot, timestamp_name


def test_timestamp_name_format():
    dt = datetime(2026, 10, 14, 15, 30, 12)
    name = timestamp_name("tmpmask", "png", dt)
    assert name == "tmpmask_20261014_153012.png"

    # Also check with leading dot in extension
    name_with_dot = timestamp_name("tmpmask", ".png", dt)
    assert name_with_dot == "tmpmask_20261014_153012.png"


def test_collision_suffix(tmp_path: Path):
    dt = datetime(2026, 10, 14, 15, 30, 12)
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    path1 = save_screenshot(frame, tmp_path, now=dt)
    assert path1.name == "tmpmask_20261014_153012.png"
    assert path1.exists()

    path2 = save_screenshot(frame, tmp_path, now=dt)
    assert path2.name == "tmpmask_20261014_153012_1.png"
    assert path2.exists()

    path3 = save_screenshot(frame, tmp_path, now=dt)
    assert path3.name == "tmpmask_20261014_153012_2.png"
    assert path3.exists()


def test_save_screenshot_readable_and_equal_shape(tmp_path: Path):
    frame = np.random.randint(0, 256, (120, 160, 3), dtype=np.uint8)
    saved_path = save_screenshot(frame, tmp_path)

    assert saved_path.exists()
    loaded = cv2.imread(str(saved_path))
    assert loaded is not None
    assert loaded.shape == frame.shape
    # Lossless PNG check
    np.testing.assert_array_equal(loaded, frame)


def test_save_screenshot_failure(tmp_path: Path):
    frame = np.zeros((10, 10, 3), dtype=np.uint8)
    with patch("cv2.imwrite", return_value=False):
        with pytest.raises(RuntimeError, match="Failed to write screenshot"):
            save_screenshot(frame, tmp_path)


def test_recorder_flow(tmp_path: Path):
    rec_dir = tmp_path / "videos"
    recorder = Recorder(rec_dir, fps=30.0)

    assert not recorder.is_recording
    assert recorder.path is None

    # stop when idle returns None
    assert recorder.stop() is None

    frame_size = (320, 240)  # (width, height)
    dt = datetime(2026, 10, 14, 12, 0, 0)
    video_path = recorder.start(frame_size, now=dt)

    assert recorder.is_recording
    assert recorder.path == video_path
    assert video_path.name == "tmpmask_20261014_120000.mp4"

    # double start raises RuntimeError
    with pytest.raises(RuntimeError, match="already recording"):
        recorder.start(frame_size)

    # write 10 frames
    frame = np.zeros((240, 320, 3), dtype=np.uint8)
    for _ in range(10):
        recorder.write(frame)

    stopped_path = recorder.stop()
    assert stopped_path == video_path
    assert not recorder.is_recording
    assert recorder.path == video_path  # current or last file

    # video file exists, size > 0, VideoCapture reports >= 1 frame
    assert video_path.exists()
    assert video_path.stat().st_size > 0

    cap = cv2.VideoCapture(str(video_path))
    assert cap.isOpened()
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    assert frame_count >= 1


def test_recorder_resize_frame(tmp_path: Path):
    recorder = Recorder(tmp_path, fps=30.0)
    recorder.start((320, 240))

    # Frame of another size (height=480, width=640) does not raise
    diff_frame = np.zeros((480, 640, 3), dtype=np.uint8)
    recorder.write(diff_frame)

    # Write when not recording is a no-op
    recorder.stop()
    recorder.write(diff_frame)


def test_recorder_collision(tmp_path: Path):
    recorder = Recorder(tmp_path, fps=30.0)
    dt = datetime(2026, 10, 14, 12, 0, 0)

    p1 = recorder.start((160, 120), now=dt)
    recorder.stop()

    p2 = recorder.start((160, 120), now=dt)
    recorder.stop()

    assert p1.name == "tmpmask_20261014_120000.mp4"
    assert p2.name == "tmpmask_20261014_120000_1.mp4"


def test_recorder_open_failure(tmp_path: Path):
    recorder = Recorder(tmp_path, fps=30.0)
    with patch("cv2.VideoWriter.isOpened", return_value=False):
        with pytest.raises(RuntimeError, match="Failed to open video writer"):
            recorder.start((320, 240))
