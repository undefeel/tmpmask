from pathlib import Path
from types import TracebackType
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode

from tmpmask.handtypes import Hand

DEFAULT_MODEL_PATH: Path = (
    Path(__file__).resolve().parent.parent / "models" / "hand_landmarker.task"
)


def landmarks_to_hands(
    hand_landmarks: list[Any],
    handedness: list[Any],
    width: int,
    height: int,
) -> list[Hand]:
    hands: list[Hand] = []
    for i, landmarks in enumerate(hand_landmarks):
        if len(landmarks) != 21:
            continue

        label = "Unknown"
        if i < len(handedness) and handedness[i]:
            first_category = handedness[i][0]
            label = getattr(first_category, "category_name", None) or "Unknown"

        points = tuple((lm.x * width, lm.y * height) for lm in landmarks)
        hands.append(Hand(handedness=label, points=points))

    return hands


class HandTracker:
    def __init__(
        self,
        model_path: Path | str = DEFAULT_MODEL_PATH,
        max_hands: int = 2,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ) -> None:
        path = Path(model_path).resolve()
        if not path.is_file():
            raise FileNotFoundError(f"Model file not found: {path}")

        self._last_timestamp_ms = -1
        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(path)),
            running_mode=RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=min_detection_confidence,
            min_tracking_confidence=min_tracking_confidence,
        )
        self._landmarker: HandLandmarker | None = HandLandmarker.create_from_options(options)

    def detect(self, frame_bgr: np.ndarray, timestamp_ms: int) -> list[Hand]:
        if self._landmarker is None:
            raise RuntimeError("HandTracker is closed")

        if timestamp_ms <= self._last_timestamp_ms:
            timestamp_ms = self._last_timestamp_ms + 1
        self._last_timestamp_ms = timestamp_ms

        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, timestamp_ms)

        height, width = frame_bgr.shape[:2]
        return landmarks_to_hands(result.hand_landmarks, result.handedness, width, height)

    def close(self) -> None:
        if self._landmarker is not None:
            self._landmarker.close()
            self._landmarker = None

    def __enter__(self) -> "HandTracker":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.close()
