import numpy as np

from tmpmask.handtypes import INDEX_TIP, THUMB_TIP, WRIST, Hand, Point
from tmpmask.portal import Quad, portal_quad, render_portal


def make_dummy_hand(
    wrist: Point,
    index_tip: Point,
    thumb_tip: Point,
    handedness: str = "Right",
) -> Hand:
    points = [(0.0, 0.0)] * 21
    points[WRIST] = wrist
    points[INDEX_TIP] = index_tip
    points[THUMB_TIP] = thumb_tip
    return Hand(handedness=handedness, points=tuple(points))


def test_portal_quad_hand_counts():
    h1 = make_dummy_hand((10.0, 10.0), (15.0, 15.0), (12.0, 12.0))
    h2 = make_dummy_hand((20.0, 20.0), (25.0, 25.0), (22.0, 22.0))
    h3 = make_dummy_hand((30.0, 30.0), (35.0, 35.0), (32.0, 32.0))

    assert portal_quad([]) is None
    assert portal_quad([h1]) is None
    assert portal_quad([h1, h2, h3]) is None


def test_portal_quad_order_and_sorting():
    left_hand = make_dummy_hand(
        wrist=(10.0, 50.0),
        index_tip=(15.0, 20.0),
        thumb_tip=(18.0, 30.0),
        handedness="Right",  # Should ignore handedness, purely sorted by wrist.x
    )
    right_hand = make_dummy_hand(
        wrist=(80.0, 50.0),
        index_tip=(75.0, 20.0),
        thumb_tip=(72.0, 30.0),
        handedness="Left",
    )

    expected: Quad = (
        (15.0, 20.0),  # left.INDEX_TIP
        (75.0, 20.0),  # right.INDEX_TIP
        (72.0, 30.0),  # right.THUMB_TIP
        (18.0, 30.0),  # left.THUMB_TIP
    )

    # Given in order [left, right]
    assert portal_quad([left_hand, right_hand]) == expected
    # Given in reversed order [right, left]
    assert portal_quad([right_hand, left_hand]) == expected


def test_render_portal_pixel_inside_and_outside():
    # 200x200 black frame
    frame = np.zeros((200, 200, 3), dtype=np.uint8)

    # 100x100 square quad from (50, 50) to (150, 150)
    quad: Quad = ((50.0, 50.0), (150.0, 50.0), (150.0, 150.0), (50.0, 150.0))

    def invert_filter(img: np.ndarray) -> np.ndarray:
        return 255 - img

    result = render_portal(frame, quad, invert_filter, opacity=1.0, outline=False)

    # Pixel well inside (100, 100) should be inverted: 255 - 0 = 255
    np.testing.assert_array_equal(result[100, 100], [255, 255, 255])

    # Pixel outside (10, 10) should be untouched: 0
    np.testing.assert_array_equal(result[10, 10], [0, 0, 0])


def test_render_portal_opacity_zero():
    frame = np.full((100, 100, 3), 42, dtype=np.uint8)
    quad: Quad = ((20.0, 20.0), (80.0, 20.0), (80.0, 80.0), (20.0, 80.0))

    def invert_filter(img: np.ndarray) -> np.ndarray:
        return 255 - img

    # Opacity 0 with outline=False -> identical to input
    result = render_portal(frame, quad, invert_filter, opacity=0.0, outline=False)
    np.testing.assert_array_equal(result, frame)

    # Opacity 0 with outline=True -> still identical to input (spec: opacity 0 outline is not drawn)
    result_with_outline = render_portal(frame, quad, invert_filter, opacity=0.0, outline=True)
    np.testing.assert_array_equal(result_with_outline, frame)

    # Clamping negative opacity -> treated as 0
    result_neg = render_portal(frame, quad, invert_filter, opacity=-0.5, outline=False)
    np.testing.assert_array_equal(result_neg, frame)


def test_render_portal_opacity_half():
    # Constant frame value 100
    frame = np.full((100, 100, 3), 100, dtype=np.uint8)
    quad: Quad = ((20.0, 20.0), (80.0, 20.0), (80.0, 80.0), (20.0, 80.0))

    def const_filter(img: np.ndarray) -> np.ndarray:
        return np.full_like(img, 200)

    result = render_portal(frame, quad, const_filter, opacity=0.5, outline=False)

    # Inside: 100 * 0.5 + 200 * 0.5 = 150
    np.testing.assert_array_equal(result[50, 50], [150, 150, 150])
    # Outside: 100
    np.testing.assert_array_equal(result[5, 5], [100, 100, 100])


def test_render_portal_input_not_mutated():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    frame_orig = frame.copy()
    quad: Quad = ((20.0, 20.0), (80.0, 20.0), (80.0, 80.0), (20.0, 80.0))

    def const_filter(img: np.ndarray) -> np.ndarray:
        return np.full_like(img, 255)

    _ = render_portal(frame, quad, const_filter, opacity=1.0, outline=True)
    np.testing.assert_array_equal(frame, frame_orig)


def test_render_portal_degenerate_and_out_of_frame_quads():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)

    def dummy_filter(img: np.ndarray) -> np.ndarray:
        return 255 - img

    # All points equal
    res1 = render_portal(
        frame,
        ((10.0, 10.0), (10.0, 10.0), (10.0, 10.0), (10.0, 10.0)),
        dummy_filter,
    )
    assert res1.shape == frame.shape

    # Collinear points
    res2 = render_portal(
        frame,
        ((10.0, 10.0), (20.0, 20.0), (30.0, 30.0), (40.0, 40.0)),
        dummy_filter,
    )
    assert res2.shape == frame.shape

    # Fully outside the frame
    res3 = render_portal(
        frame,
        ((-100.0, -100.0), (-50.0, -100.0), (-50.0, -50.0), (-100.0, -50.0)),
        dummy_filter,
    )
    assert res3.shape == frame.shape

    # Self-intersecting bow-tie quad
    res4 = render_portal(
        frame,
        ((10.0, 10.0), (90.0, 90.0), (90.0, 10.0), (10.0, 90.0)),
        dummy_filter,
    )
    assert res4.shape == frame.shape


def test_render_portal_outline():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    quad: Quad = ((20.0, 20.0), (80.0, 20.0), (80.0, 80.0), (20.0, 80.0))

    def noop_filter(img: np.ndarray) -> np.ndarray:
        return img.copy()

    # With outline=True and opacity>0, the boundary should have white / anti-aliased line pixels
    result = render_portal(frame, quad, noop_filter, opacity=1.0, outline=True)
    assert np.all(result[20, 50] > 200)
    assert np.all(result[20, 50] == result[20, 50, 0])  # R == G == B (white line)
