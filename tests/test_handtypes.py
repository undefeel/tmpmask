import pytest

from tmpmask.__main__ import main
from tmpmask.handtypes import (
    FINGERTIPS,
    INDEX_TIP,
    MIDDLE_MCP,
    MIDDLE_TIP,
    PINKY_TIP,
    RING_TIP,
    THUMB_TIP,
    WRIST,
    Hand,
)


def test_hand_valid_construction():
    points = tuple((float(i), float(i * 2)) for i in range(21))
    hand = Hand(handedness="Right", points=points)
    assert hand.handedness == "Right"
    assert len(hand.points) == 21
    assert hand.point(0) == (0.0, 0.0)
    assert hand.point(WRIST) == (0.0, 0.0)
    assert hand.point(MIDDLE_MCP) == (9.0, 18.0)


def test_hand_invalid_points_count():
    points_20 = tuple((float(i), float(i)) for i in range(20))
    with pytest.raises(ValueError, match="exactly 21 points"):
        Hand(handedness="Left", points=points_20)

    points_22 = tuple((float(i), float(i)) for i in range(22))
    with pytest.raises(ValueError, match="exactly 21 points"):
        Hand(handedness="Left", points=points_22)


def test_hand_size():
    # Construct points where WRIST is at (0, 0) and MIDDLE_MCP is at (3, 4) -> distance = 5
    pts = [(0.0, 0.0)] * 21
    pts[WRIST] = (0.0, 0.0)
    pts[MIDDLE_MCP] = (3.0, 4.0)
    hand = Hand(handedness="Right", points=tuple(pts))
    assert hand.size() == pytest.approx(5.0)


def test_constants():
    assert WRIST == 0
    assert THUMB_TIP == 4
    assert INDEX_TIP == 8
    assert MIDDLE_MCP == 9
    assert MIDDLE_TIP == 12
    assert RING_TIP == 16
    assert PINKY_TIP == 20
    assert FINGERTIPS == (4, 8, 12, 16, 20)


def test_main_smoke(capsys):
    import tmpmask.app
    assert main is tmpmask.app.main
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    captured = capsys.readouterr()
    assert "tmpmask" in captured.out
