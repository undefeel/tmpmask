"""Application entry point and main loop."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable, Iterable, Sequence
from datetime import datetime
from typing import Any

import cv2
import numpy as np

from tmpmask.capture import Recorder, save_screenshot
from tmpmask.config import Config, parse_args
from tmpmask.filters import FILTER_IDS, get_filter, next_filter_id
from tmpmask.gestures import PinchTrigger
from tmpmask.portal import portal_quad, render_portal
from tmpmask.smoothing import PortalSmoother
from tmpmask.texts import filter_name, t
from tmpmask.tracker import HandTracker

KEY_NONE = -1  # show returned "no key pressed"
KEY_WINDOW_CLOSED = -2  # show returned "window closed by user"

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_CAMERA_OPEN = 3
EXIT_CAMERA_LOST = 4
EXIT_MODEL_MISSING = 5
EXIT_OUTPUT_DIR = 6


class FrameReadError(Exception):
    """Raised when camera fails to yield a frame."""


def run(
    frames: Iterable[np.ndarray],
    tracker: Any,
    config: Config,
    clock: Callable[[], float] = time.monotonic,
    show: Callable[[np.ndarray], int] | None = None,
    say: Callable[[str], None] = print,
    recorder: Recorder | None = None,
    now: Callable[[], datetime] = datetime.now,
) -> int:
    current = config.filter
    smoother = PortalSmoother()
    trigger = PinchTrigger()
    t0 = clock()

    if recorder is None:
        rec = Recorder(config.output_dir, 30.0)
    else:
        rec = recorder

    def switch_filter(new_id: str) -> None:
        nonlocal current
        if new_id != current:
            current = new_id
            say(t("messages.filter_switched", name=filter_name(current)))

    frame_iter = iter(frames)
    try:
        while True:
            # 1. read
            try:
                frame = next(frame_iter)
            except StopIteration:
                return EXIT_OK
            except FrameReadError:
                say(t("errors.camera_no_frame"))
                return EXIT_CAMERA_LOST

            # 2. mirror
            if config.mirror:
                frame = cv2.flip(frame, 1)

            # 3. detect
            now_s = clock()
            ts_ms = int((now_s - t0) * 1000)
            hands = tracker.detect(frame, ts_ms)

            # 4. pinch
            if trigger.update(hands, now_s):
                switch_filter(next_filter_id(current, 1))

            # 5. portal_quad
            quad = portal_quad(hands)

            # 6. smoother
            smoothed, opacity = smoother.update(quad)

            # 7. render_portal
            if smoothed is not None:
                clean = render_portal(frame, smoothed, get_filter(current), opacity)
            else:
                clean = frame

            # 8. recording dot & 9. record
            h, w = clean.shape[:2]
            if rec.is_recording:
                shown = clean.copy()
                r = max(6, round(h / 72))
                cv2.circle(shown, (w - 3 * r, 3 * r), r, (0, 0, 255), -1, cv2.LINE_AA)
                rec.write(clean)
            else:
                shown = clean

            # 10. show
            key = show(shown) if show is not None else KEY_NONE

            # 11. keys
            if key in (KEY_WINDOW_CLOSED, ord("q"), ord("Q"), 27):
                return EXIT_OK

            if key in (ord("n"), ord("N")):
                switch_filter(next_filter_id(current, 1))
            elif key in (ord("p"), ord("P")):
                switch_filter(next_filter_id(current, -1))
            elif ord("1") <= key <= ord("8"):
                idx = key - ord("1")
                if 0 <= idx < len(FILTER_IDS):
                    switch_filter(FILTER_IDS[idx])
            elif key in (ord("s"), ord("S")):
                try:
                    path = save_screenshot(clean, config.output_dir, now())
                    say(t("messages.screenshot_saved", path=path))
                except (OSError, RuntimeError) as exc:
                    say(t("errors.screenshot_failed", error=exc))
            elif key in (ord("r"), ord("R")):
                if not rec.is_recording:
                    try:
                        rec_w, rec_h = clean.shape[1], clean.shape[0]
                        path = rec.start((rec_w, rec_h), now())
                        say(t("messages.recording_started", path=path))
                    except (OSError, RuntimeError) as exc:
                        say(t("errors.recording_failed", error=exc))
                else:
                    path = rec.stop()
                    say(t("messages.recording_stopped", path=path))
    finally:
        if rec.is_recording:
            path = rec.stop()
            say(t("messages.recording_stopped", path=path))


def main(argv: Sequence[str] | None = None) -> int:
    config = parse_args(argv)

    if not config.model.is_file():
        print(t("errors.model_missing", path=config.model), file=sys.stderr)
        return EXIT_MODEL_MISSING

    try:
        config.output_dir.mkdir(parents=True, exist_ok=True)
        test_file = config.output_dir / ".tmpmask_write_test"
        test_file.touch(exist_ok=True)
        test_file.unlink(missing_ok=True)
    except OSError as exc:
        print(t("errors.output_dir", path=config.output_dir, error=exc), file=sys.stderr)
        return EXIT_OUTPUT_DIR

    cap = cv2.VideoCapture(config.camera)
    if not cap.isOpened():
        print(t("errors.camera_open", index=config.camera), file=sys.stderr)
        return EXIT_CAMERA_OPEN

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)

    tracker = HandTracker(config.model)
    win_title = t("app.title")
    cv2.namedWindow(win_title)

    print(
        t(
            "messages.startup_hint",
            filter=filter_name(config.filter),
            output_dir=config.output_dir,
        )
    )

    def frame_generator() -> Iterable[np.ndarray]:
        while True:
            fail_count = 0
            while fail_count < 30:
                ok, f = cap.read()
                if ok and f is not None:
                    yield f
                    break
                fail_count += 1
                time.sleep(0.03)
            else:
                raise FrameReadError

    def show_cb(frame: np.ndarray) -> int:
        cv2.imshow(win_title, frame)
        raw_key = cv2.waitKey(1)
        if cv2.getWindowProperty(win_title, cv2.WND_PROP_VISIBLE) < 1:
            return KEY_WINDOW_CLOSED
        k = raw_key & 0xFF
        if k == 0xFF:
            return KEY_NONE
        return k

    try:
        code = run(frame_generator(), tracker, config, show=show_cb)
    except KeyboardInterrupt:
        code = EXIT_OK
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()

    if code == EXIT_OK:
        print(t("messages.exit"))

    return code
