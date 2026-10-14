from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from tmpmask.tracker import DEFAULT_MODEL_PATH, HandTracker, landmarks_to_hands


def test_default_model_path_exists():
    assert DEFAULT_MODEL_PATH.name == "hand_landmarker.task"
    assert DEFAULT_MODEL_PATH.is_file()


def test_landmarks_to_hands_scaling_and_handedness():
    # 21 landmarks
    landmarks = [SimpleNamespace(x=i / 100.0, y=(i * 2) / 100.0) for i in range(21)]
    handedness = [[SimpleNamespace(category_name="Right")]]
    width = 200
    height = 100

    hands = landmarks_to_hands([landmarks], handedness, width, height)
    assert len(hands) == 1
    hand = hands[0]
    assert hand.handedness == "Right"
    assert len(hand.points) == 21
    # Check first point: 0 * 200 = 0, 0 * 100 = 0
    assert hand.point(0) == (0.0, 0.0)
    # Check point 10: x = 0.10 * 200 = 20.0, y = 0.20 * 100 = 20.0
    assert hand.point(10) == (20.0, 20.0)


def test_landmarks_to_hands_skips_invalid_landmark_count():
    # Hand with 20 landmarks (should be skipped)
    landmarks_20 = [SimpleNamespace(x=0.1, y=0.1) for _ in range(20)]
    # Valid hand with 21 landmarks
    landmarks_21 = [SimpleNamespace(x=0.2, y=0.2) for _ in range(21)]

    handedness = [
        [SimpleNamespace(category_name="Left")],
        [SimpleNamespace(category_name="Right")],
    ]

    hands = landmarks_to_hands([landmarks_20, landmarks_21], handedness, 100, 100)
    assert len(hands) == 1
    # Note that handedness[1] corresponds to the 2nd hand in the input list
    assert hands[0].handedness == "Right"
    assert len(hands[0].points) == 21


def test_landmarks_to_hands_missing_handedness():
    landmarks_21 = [SimpleNamespace(x=0.1, y=0.1) for _ in range(21)]

    # Empty handedness list
    hands = landmarks_to_hands([landmarks_21], [], 100, 100)
    assert len(hands) == 1
    assert hands[0].handedness == "Unknown"

    # Handedness entry is empty list
    hands_empty_entry = landmarks_to_hands([landmarks_21], [[]], 100, 100)
    assert len(hands_empty_entry) == 1
    assert hands_empty_entry[0].handedness == "Unknown"

    # Category name is None / missing
    missing_cat = [[SimpleNamespace(category_name=None)]]
    hands_no_cat = landmarks_to_hands([landmarks_21], missing_cat, 100, 100)
    assert len(hands_no_cat) == 1
    assert hands_no_cat[0].handedness == "Unknown"


def test_hand_tracker_missing_model_raises_file_not_found():
    non_existent = "/non/existent/path/model.task"
    with pytest.raises(FileNotFoundError) as exc_info:
        HandTracker(model_path=non_existent)
    assert non_existent in str(exc_info.value)


def test_hand_tracker_detect_blank_frame():
    tracker = HandTracker()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    hands = tracker.detect(frame, timestamp_ms=0)
    assert hands == []
    tracker.close()


def test_hand_tracker_non_increasing_timestamps():
    tracker = HandTracker()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    # Calling detect with the same timestamp or lower should not raise an error
    hands1 = tracker.detect(frame, timestamp_ms=100)
    hands2 = tracker.detect(frame, timestamp_ms=100)
    hands3 = tracker.detect(frame, timestamp_ms=50)
    assert hands1 == []
    assert hands2 == []
    assert hands3 == []
    tracker.close()


def test_hand_tracker_context_manager_closes():
    with HandTracker() as tracker:
        assert tracker._landmarker is not None
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        hands = tracker.detect(frame, timestamp_ms=10)
        assert hands == []

    assert tracker._landmarker is None
    # Calling close again should be a no-op
    tracker.close()


def test_hand_tracker_detect_after_close_raises():
    tracker = HandTracker()
    tracker.close()
    frame = np.zeros((480, 640, 3), dtype=np.uint8)
    with pytest.raises(RuntimeError, match="closed"):
        tracker.detect(frame, timestamp_ms=0)


def test_hand_tracker_mocked_options():
    with patch("tmpmask.tracker.HandLandmarker.create_from_options") as mock_create:
        mock_instance = MagicMock()
        mock_create.return_value = mock_instance

        tracker = HandTracker(
            model_path=DEFAULT_MODEL_PATH,
            max_hands=4,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.8,
        )
        assert mock_create.called
        options_arg = mock_create.call_args[0][0]
        assert options_arg.num_hands == 4
        assert options_arg.min_hand_detection_confidence == 0.7
        assert options_arg.min_tracking_confidence == 0.8
        tracker.close()
        mock_instance.close.assert_called_once()
