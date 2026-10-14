import pytest

from tmpmask.smoothing import PortalSmoother, Quad


def test_first_quad_returned_unchanged_and_fade_in():
    smoother = PortalSmoother(alpha=0.5, fade_in_frames=5, fade_out_frames=6)
    q1: Quad = ((10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0))

    # Frame 1: first quad returned unchanged with opacity 0.2 (1/5)
    out_quad, opacity = smoother.update(q1)
    assert out_quad == q1
    assert opacity == pytest.approx(0.2)

    # Frame 2
    out_quad, opacity = smoother.update(q1)
    assert out_quad == q1
    assert opacity == pytest.approx(0.4)

    # Frame 3
    out_quad, opacity = smoother.update(q1)
    assert out_quad == q1
    assert opacity == pytest.approx(0.6)

    # Frame 4
    out_quad, opacity = smoother.update(q1)
    assert out_quad == q1
    assert opacity == pytest.approx(0.8)

    # Frame 5: reaches exactly 1.0 after 5 frames
    out_quad, opacity = smoother.update(q1)
    assert out_quad == q1
    assert opacity == pytest.approx(1.0)

    # Frame 6: stays at 1.0
    out_quad, opacity = smoother.update(q1)
    assert out_quad == q1
    assert opacity == pytest.approx(1.0)


def test_ema_midpoint_with_alpha():
    smoother = PortalSmoother(alpha=0.5)
    q1: Quad = ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))
    smoother.update(q1)

    q2: Quad = ((10.0, 20.0), (30.0, 20.0), (30.0, 30.0), (10.0, 30.0))
    out_quad, _ = smoother.update(q2)
    expected = (
        (5.0, 10.0),
        (20.0, 10.0),
        (20.0, 20.0),
        (5.0, 20.0),
    )
    assert out_quad is not None
    for p, exp in zip(out_quad, expected, strict=True):
        assert p[0] == pytest.approx(exp[0])
        assert p[1] == pytest.approx(exp[1])


def test_jump_greater_than_reset_distance_snaps():
    smoother = PortalSmoother(alpha=0.5, reset_distance=200.0)
    q1: Quad = ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))
    smoother.update(q1)

    # Jump point 0 by 201 px (> 200)
    q2: Quad = ((201.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))
    out_quad, _ = smoother.update(q2)
    # Snaps directly to q2, no EMA
    assert out_quad == q2


def test_jump_within_reset_distance_smoothes():
    smoother = PortalSmoother(alpha=0.5, reset_distance=200.0)
    q1: Quad = ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))
    smoother.update(q1)

    # Jump point 0 by 100 px (<= 200)
    q2: Quad = ((100.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))
    out_quad, _ = smoother.update(q2)
    assert out_quad is not None
    assert out_quad[0] == pytest.approx((50.0, 0.0))


def test_fade_out_and_reacquire():
    smoother = PortalSmoother(fade_in_frames=5, fade_out_frames=6)
    q1: Quad = ((10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0))

    # Reach 1.0 opacity
    for _ in range(5):
        smoother.update(q1)

    # Fade out: losing the quad
    # Frame 1: 1.0 - 1/6 = 5/6
    out_quad, op1 = smoother.update(None)
    assert out_quad == q1
    assert op1 == pytest.approx(5.0 / 6.0)

    # Frame 2: 4/6
    out_quad, op2 = smoother.update(None)
    assert out_quad == q1
    assert op2 == pytest.approx(4.0 / 6.0)

    # Frame 3: 3/6
    out_quad, op3 = smoother.update(None)
    assert out_quad == q1
    assert op3 == pytest.approx(3.0 / 6.0)

    # Frame 4: 2/6
    out_quad, op4 = smoother.update(None)
    assert out_quad == q1
    assert op4 == pytest.approx(2.0 / 6.0)

    # Frame 5: 1/6
    out_quad, op5 = smoother.update(None)
    assert out_quad == q1
    assert op5 == pytest.approx(1.0 / 6.0)

    # Frame 6: reaches 0, returns (None, 0.0)
    out_quad, op6 = smoother.update(None)
    assert out_quad is None
    assert op6 == 0.0

    # Further updates with None stay (None, 0.0)
    out_quad, op_none = smoother.update(None)
    assert out_quad is None
    assert op_none == 0.0

    # Reacquire after that starts fresh at 0.2
    q2: Quad = ((50.0, 50.0), (60.0, 50.0), (60.0, 60.0), (50.0, 60.0))
    out_quad, op_reacquire = smoother.update(q2)
    assert out_quad == q2
    assert op_reacquire == pytest.approx(0.2)


def test_reset():
    smoother = PortalSmoother(fade_in_frames=5, fade_out_frames=6)
    q1: Quad = ((10.0, 10.0), (20.0, 10.0), (20.0, 20.0), (10.0, 20.0))

    smoother.update(q1)
    smoother.update(q1)
    smoother.reset()

    # After reset, update with None returns (None, 0.0)
    out_quad, op = smoother.update(None)
    assert out_quad is None
    assert op == 0.0

    # Next quad starts fresh as first quad
    out_quad, op = smoother.update(q1)
    assert out_quad == q1
    assert op == pytest.approx(0.2)


def test_initial_none_returns_none_zero():
    smoother = PortalSmoother()
    out_quad, op = smoother.update(None)
    assert out_quad is None
    assert op == 0.0
