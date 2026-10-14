from datetime import datetime
from pathlib import Path

import numpy as np

from tmpmask.app import (
    KEY_NONE,
    KEY_WINDOW_CLOSED,
    FrameReadError,
    run,
)
from tmpmask.config import Config
from tmpmask.handtypes import INDEX_TIP, MIDDLE_MCP, THUMB_TIP, WRIST, Hand


def make_hand(
    wrist: tuple[float, float],
    index_tip: tuple[float, float],
    thumb_tip: tuple[float, float],
    mcp: tuple[float, float] = (0.0, 100.0),
    is_pinch_pose: bool = False,
) -> Hand:
    pts = [(0.0, 0.0)] * 21
    pts[WRIST] = wrist
    pts[MIDDLE_MCP] = mcp
    pts[INDEX_TIP] = index_tip
    pts[THUMB_TIP] = thumb_tip
    if is_pinch_pose:
        # All 5 fingertips close together around (50, 50)
        from tmpmask.handtypes import FINGERTIPS

        for tip in FINGERTIPS:
            pts[tip] = (50.0, 50.0)
    return Hand(handedness="Right", points=tuple(pts))


class FakeTracker:
    def __init__(self, hands_sequence: list[list[Hand]] | None = None):
        self.calls: list[tuple[np.ndarray, int]] = []
        self.hands_sequence = hands_sequence or []
        self.idx = 0

    def detect(self, frame: np.ndarray, ts_ms: int) -> list[Hand]:
        self.calls.append((frame.copy(), ts_ms))
        if self.idx < len(self.hands_sequence):
            res = self.hands_sequence[self.idx]
            self.idx += 1
            return res
        return []


def test_run_ten_frames_two_hands(tmp_path: Path):
    h1 = make_hand((10.0, 50.0), (20.0, 20.0), (20.0, 80.0))
    h2 = make_hand((100.0, 50.0), (90.0, 20.0), (90.0, 80.0))
    tracker = FakeTracker([[h1, h2]] * 10)

    cfg = Config(output_dir=tmp_path)
    frames = [np.zeros((120, 160, 3), dtype=np.uint8) for _ in range(10)]

    time_counter = [0.0]

    def fake_clock() -> float:
        t = time_counter[0]
        time_counter[0] += 1.0 / 30.0
        return t

    code = run(frames, tracker, cfg, clock=fake_clock, show=None)
    assert code == 0
    assert len(tracker.calls) == 10
    timestamps = [call[1] for call in tracker.calls]
    for i in range(1, len(timestamps)):
        assert timestamps[i] > timestamps[i - 1]


def test_run_key_navigation_and_quit(tmp_path: Path):
    cfg = Config(output_dir=tmp_path)
    frames = [np.zeros((120, 160, 3), dtype=np.uint8) for _ in range(20)]
    tracker = FakeTracker()

    keys = [ord("n"), ord("p"), ord("5"), ord("5"), ord("q")]
    key_idx = 0

    def scripted_show(frame: np.ndarray) -> int:
        nonlocal key_idx
        if key_idx < len(keys):
            k = keys[key_idx]
            key_idx += 1
            return k
        return KEY_NONE

    messages: list[str] = []
    code = run(frames, tracker, cfg, show=scripted_show, say=messages.append)
    assert code == 0
    assert len(tracker.calls) == 5  # exited early on 'q'
    assert any("Тепловизор" in m for m in messages)
    assert any("Океан" in m for m in messages)
    # Check that '5' was only announced once
    ocean_messages = [m for m in messages if "Океан" in m]
    assert len(ocean_messages) == 1


def test_run_esc_and_window_closed(tmp_path: Path):
    cfg = Config(output_dir=tmp_path)
    tracker = FakeTracker()

    # Esc
    frames1 = [np.zeros((120, 160, 3), dtype=np.uint8) for _ in range(5)]
    code_esc = run(frames1, tracker, cfg, show=lambda f: 27)
    assert code_esc == 0

    # Window closed
    frames2 = [np.zeros((120, 160, 3), dtype=np.uint8) for _ in range(5)]
    code_closed = run(frames2, tracker, cfg, show=lambda f: KEY_WINDOW_CLOSED)
    assert code_closed == 0


def test_run_screenshot(tmp_path: Path):
    cfg = Config(output_dir=tmp_path)
    tracker = FakeTracker()
    frames = [np.zeros((120, 160, 3), dtype=np.uint8) for _ in range(3)]
    keys = [ord("s"), KEY_NONE, KEY_NONE]
    it = iter(keys)

    messages: list[str] = []
    fixed_time = datetime(2026, 10, 14, 15, 30, 0)
    code = run(
        frames,
        tracker,
        cfg,
        show=lambda f: next(it),
        say=messages.append,
        now=lambda: fixed_time,
    )
    assert code == 0
    screenshots = list(tmp_path.glob("*.png"))
    assert len(screenshots) == 1
    assert screenshots[0].name == "tmpmask_20261014_153000.png"
    assert any("Скриншот сохранён" in m for m in messages)


def test_run_recording_start_stop(tmp_path: Path):
    cfg = Config(output_dir=tmp_path)
    tracker = FakeTracker()
    frames = [np.zeros((120, 160, 3), dtype=np.uint8) for _ in range(10)]
    # Frame 0: 'r' (start), Frame 1-3: KEY_NONE, Frame 4: 'r' (stop), rest: KEY_NONE
    keys = [ord("r"), KEY_NONE, KEY_NONE, KEY_NONE, ord("r")]
    key_iter = iter(keys)

    shown_frames: list[np.ndarray] = []

    def mock_show(frame: np.ndarray) -> int:
        shown_frames.append(frame.copy())
        try:
            return next(key_iter)
        except StopIteration:
            return KEY_NONE

    messages: list[str] = []
    fixed_time = datetime(2026, 10, 14, 15, 30, 0)
    code = run(
        frames,
        tracker,
        cfg,
        show=mock_show,
        say=messages.append,
        now=lambda: fixed_time,
    )
    assert code == 0
    videos = list(tmp_path.glob("*.mp4"))
    assert len(videos) == 1
    assert videos[0].stat().st_size > 0
    assert any("Запись начата" in m for m in messages)
    assert any("Запись остановлена" in m for m in messages)

    # Check that shown_frames while recording had red dot (BGR [0, 0, 255])
    # Shown frame index 1, 2, 3 were recorded
    # Radius r = max(6, round(120 / 72)) = 6. Center = (160 - 18, 18) = (142, 18).
    # Check pixel around (18, 142) in y, x
    rec_frame = shown_frames[2]
    assert np.array_equal(rec_frame[18, 142], [0, 0, 255])

    # Check frame 0 before recording was started: no red dot
    assert np.array_equal(shown_frames[0][18, 142], [0, 0, 0])


def test_run_recording_auto_finalized_on_exit(tmp_path: Path):
    cfg = Config(output_dir=tmp_path)
    tracker = FakeTracker()
    frames = [np.zeros((120, 160, 3), dtype=np.uint8) for _ in range(5)]
    # Frame 0: 'r', Frame 1: 'q'
    keys = [ord("r"), ord("q")]
    key_iter = iter(keys)

    messages: list[str] = []
    code = run(
        frames,
        tracker,
        cfg,
        show=lambda f: next(key_iter),
        say=messages.append,
    )
    assert code == 0
    videos = list(tmp_path.glob("*.mp4"))
    assert len(videos) == 1
    assert any("Запись остановлена" in m for m in messages)


def test_run_pinch_switches_filter(tmp_path: Path):
    cfg = Config(output_dir=tmp_path)
    pinched = make_hand((0.0, 0.0), (50.0, 50.0), (50.0, 50.0), is_pinch_pose=True)
    tracker = FakeTracker([[pinched]] * 5)
    frames = [np.zeros((120, 160, 3), dtype=np.uint8) for _ in range(5)]

    messages: list[str] = []
    code = run(frames, tracker, cfg, say=messages.append)
    assert code == 0
    switches = [m for m in messages if "Фильтр:" in m]
    assert len(switches) == 1
    assert "Тепловизор" in switches[0]


def test_run_camera_lost(tmp_path: Path):
    cfg = Config(output_dir=tmp_path)
    tracker = FakeTracker()

    def failing_frames():
        yield np.zeros((120, 160, 3), dtype=np.uint8)
        raise FrameReadError

    messages: list[str] = []
    code = run(failing_frames(), tracker, cfg, say=messages.append)
    assert code == 4
    assert any("Камера не вернула кадр" in m for m in messages)


def test_run_hands_portal_rendering(tmp_path: Path):
    cfg = Config(output_dir=tmp_path, filter="purple")
    # Left hand at x=30, Right hand at x=130
    h1 = make_hand((30.0, 60.0), (40.0, 30.0), (40.0, 90.0))
    h2 = make_hand((130.0, 60.0), (120.0, 30.0), (120.0, 90.0))

    # Send 10 identical frames with 2 hands to ensure smoother opacity reaches 1.0
    tracker = FakeTracker([[h1, h2]] * 10)
    input_frame = np.full((120, 160, 3), 100, dtype=np.uint8)
    frames = [input_frame.copy() for _ in range(10)]

    shown_frames: list[np.ndarray] = []
    code = run(
        frames,
        tracker,
        cfg,
        show=lambda f: shown_frames.append(f.copy()) or KEY_NONE,
    )
    assert code == 0
    # Inside the portal around center (60, 80), pixels should be modified by purple filter
    last_frame = shown_frames[-1]
    # Check center pixel
    assert not np.array_equal(last_frame[60, 80], input_frame[60, 80])


def test_run_different_hand_counts_no_portal(tmp_path: Path):
    cfg = Config(output_dir=tmp_path)
    h = make_hand((30.0, 60.0), (40.0, 30.0), (40.0, 90.0))
    # 0 hands, 1 hand, 3 hands
    tracker = FakeTracker([[], [h], [h, h, h]])
    frames = [np.full((120, 160, 3), 50, dtype=np.uint8) for _ in range(3)]

    shown_frames: list[np.ndarray] = []
    code = run(
        frames,
        tracker,
        cfg,
        show=lambda f: shown_frames.append(f.copy()) or KEY_NONE,
    )
    assert code == 0
    for f in shown_frames:
        assert np.array_equal(f, np.full((120, 160, 3), 50, dtype=np.uint8))


def test_run_mirror_flips_frame(tmp_path: Path):
    cfg = Config(output_dir=tmp_path, mirror=True)
    tracker = FakeTracker()
    test_frame = np.zeros((120, 160, 3), dtype=np.uint8)
    test_frame[:, 0:80] = 255  # Left half white, right half black

    code = run([test_frame], tracker, cfg)
    assert code == 0
    assert len(tracker.calls) == 1
    frame_received_by_tracker = tracker.calls[0][0]
    expected_flipped = np.fliplr(test_frame)
    assert np.array_equal(frame_received_by_tracker, expected_flipped)
