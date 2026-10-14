from tmpmask.gestures import PinchTrigger, is_pinch
from tmpmask.handtypes import FINGERTIPS, MIDDLE_MCP, WRIST, Hand


def make_hand(
    wrist: tuple[float, float] = (0.0, 0.0),
    mcp: tuple[float, float] = (0.0, 100.0),
    fingertip_positions: dict[int, tuple[float, float]] | None = None,
) -> Hand:
    pts = [(0.0, 0.0)] * 21
    pts[WRIST] = wrist
    pts[MIDDLE_MCP] = mcp
    if fingertip_positions:
        for idx, pos in fingertip_positions.items():
            pts[idx] = pos
    return Hand(handedness="Right", points=tuple(pts))


def make_open_hand() -> Hand:
    # Scale = 100
    # Fingertips spread far from each other
    # e.g., tips spread at distance 50 from center (50, 50)
    # Centroid will be around (50, 50) and distance to tips ~ 50 > 0.35 * 100 = 35
    tips = {
        FINGERTIPS[0]: (0.0, 50.0),
        FINGERTIPS[1]: (50.0, 0.0),
        FINGERTIPS[2]: (100.0, 50.0),
        FINGERTIPS[3]: (50.0, 100.0),
        FINGERTIPS[4]: (50.0, 50.0),
    }
    return make_hand(wrist=(0.0, 0.0), mcp=(0.0, 100.0), fingertip_positions=tips)


def make_pinched_hand() -> Hand:
    # Scale = 100, ratio = 0.35 -> max allowed distance < 35
    # All fingertips tightly clustered around (50, 50) within distance 5
    tips = {
        FINGERTIPS[0]: (50.0, 51.0),
        FINGERTIPS[1]: (51.0, 50.0),
        FINGERTIPS[2]: (49.0, 50.0),
        FINGERTIPS[3]: (50.0, 49.0),
        FINGERTIPS[4]: (50.0, 50.0),
    }
    return make_hand(wrist=(0.0, 0.0), mcp=(0.0, 100.0), fingertip_positions=tips)


def test_is_pinch_open_hand():
    hand = make_open_hand()
    assert is_pinch(hand) is False


def test_is_pinch_pinched_hand():
    hand = make_pinched_hand()
    assert is_pinch(hand) is True


def test_is_pinch_zero_size_hand():
    # Wrist and MIDDLE_MCP at identical position -> size() == 0
    tips = {tip: (10.0, 10.0) for tip in FINGERTIPS}
    hand = make_hand(wrist=(10.0, 10.0), mcp=(10.0, 10.0), fingertip_positions=tips)
    assert hand.size() == 0.0
    assert is_pinch(hand) is False


def test_is_pinch_boundary_threshold():
    # Scale = 100, ratio = 0.35 -> max_dist = 35.0
    # Center = (0, 0). Place 4 fingertips at (0, 0) and 1 fingertip at (35.0, 0)
    # Centroid = (7.0, 0).
    # Distance from (35, 0) to (7, 0) = 28.0 < 35.0
    # Let's test custom ratio
    tips = {tip: (0.0, 0.0) for tip in FINGERTIPS[:-1]}
    tips[FINGERTIPS[-1]] = (50.0, 0.0)
    # Centroid: (10.0, 0.0)
    # Distance of 5th tip to centroid: 40.0
    # If ratio = 0.5, max_dist = 50.0 -> dist 40 < 50 -> True
    # If ratio = 0.35, max_dist = 35.0 -> dist 40 >= 35 -> False
    hand = make_hand(wrist=(0.0, 0.0), mcp=(0.0, 100.0), fingertip_positions=tips)
    assert is_pinch(hand, ratio=0.35) is False
    assert is_pinch(hand, ratio=0.5) is True


def test_pinch_trigger_empty_hands():
    trigger = PinchTrigger()
    assert trigger.update([], now_s=0.0) is False
    assert trigger.update([], now_s=1.0) is False


def test_pinch_trigger_holding_30_frames():
    trigger = PinchTrigger()
    pinched = make_pinched_hand()

    triggers = []
    # Hold pinch for 30 frames at 30 fps (dt = 0.033s)
    for frame in range(30):
        t = frame * (1.0 / 30.0)
        res = trigger.update([pinched], now_s=t)
        triggers.append(res)

    assert triggers[0] is True
    assert not any(triggers[1:])
    assert sum(triggers) == 1


def test_pinch_trigger_release_and_cooldown_success():
    trigger = PinchTrigger(cooldown_s=0.8, release_frames=3)
    pinched = make_pinched_hand()
    open_hand = make_open_hand()

    # Frame 0: Trigger 1
    assert trigger.update([pinched], now_s=0.0) is True

    # 3 frames release
    assert trigger.update([open_hand], now_s=0.1) is False
    assert trigger.update([open_hand], now_s=0.2) is False
    assert trigger.update([open_hand], now_s=0.3) is False  # Re-armed now

    # Pinch again after cooldown (now_s = 0.85 >= 0.0 + 0.8)
    assert trigger.update([pinched], now_s=0.85) is True


def test_pinch_trigger_insufficient_release_frames():
    trigger = PinchTrigger(cooldown_s=0.8, release_frames=3)
    pinched = make_pinched_hand()
    open_hand = make_open_hand()

    # Frame 0: Trigger 1
    assert trigger.update([pinched], now_s=0.0) is True

    # Only 2 frames release (< 3)
    assert trigger.update([open_hand], now_s=0.1) is False
    assert trigger.update([open_hand], now_s=0.2) is False

    # Pinch again after cooldown time, but not enough release frames
    assert trigger.update([pinched], now_s=1.0) is False


def test_pinch_trigger_within_cooldown():
    trigger = PinchTrigger(cooldown_s=0.8, release_frames=3)
    pinched = make_pinched_hand()
    open_hand = make_open_hand()

    # Frame 0: Trigger 1
    assert trigger.update([pinched], now_s=0.0) is True

    # 3 frames release (re-armed condition satisfied)
    assert trigger.update([open_hand], now_s=0.1) is False
    assert trigger.update([open_hand], now_s=0.2) is False
    assert trigger.update([open_hand], now_s=0.3) is False

    # Pinch again within cooldown (now_s = 0.5 < 0.8)
    # Armed state consumed without triggering
    assert trigger.update([pinched], now_s=0.5) is False

    # Even after cooldown expires, if we didn't release again, it won't trigger
    assert trigger.update([pinched], now_s=1.0) is False

    # Now release 3 frames
    assert trigger.update([open_hand], now_s=1.1) is False
    assert trigger.update([open_hand], now_s=1.2) is False
    assert trigger.update([open_hand], now_s=1.3) is False

    # And pinch again after cooldown from original (now_s=1.5 >= 0.8)
    assert trigger.update([pinched], now_s=1.5) is True


def test_pinch_trigger_multiple_hands_any_pinching():
    trigger = PinchTrigger()
    pinched = make_pinched_hand()
    open_hand = make_open_hand()

    # One open, one pinched -> should trigger
    assert trigger.update([open_hand, pinched], now_s=0.0) is True
