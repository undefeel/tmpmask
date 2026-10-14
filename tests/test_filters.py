import numpy as np
import pytest

from tmpmask.filters import FILTER_IDS, OVERLAY_IMAGES, FilterFn, get_filter, next_filter_id

CLASSIC_FILTER_IDS = [fid for fid in FILTER_IDS if fid not in OVERLAY_IMAGES]


@pytest.mark.parametrize("filter_id", CLASSIC_FILTER_IDS)
def test_filter_properties(filter_id: str) -> None:
    fn: FilterFn = get_filter(filter_id)

    # Use a non-uniform random image
    np.random.seed(42)
    img = np.random.randint(10, 245, (64, 64, 3), dtype=np.uint8)
    img_copy = img.copy()

    out = fn(img)

    # Acceptance checks:
    # 1. Output same shape and dtype as input
    assert out.shape == img.shape
    assert out.dtype == img.dtype

    # 2. Input unchanged
    assert np.array_equal(img, img_copy)

    # 3. Output differs from non-uniform random input
    assert not np.array_equal(out, img)


def test_pixelate_edge_sizes() -> None:
    fn = get_filter("pixelate")

    # 1x1 test
    img_1x1 = np.full((1, 1, 3), 128, dtype=np.uint8)
    out_1x1 = fn(img_1x1)
    assert out_1x1.shape == (1, 1, 3)
    assert out_1x1.dtype == np.uint8
    assert np.array_equal(out_1x1, img_1x1)

    # 17x9 test (odd sizes, small / non-multiples of 16)
    np.random.seed(123)
    img_17x9 = np.random.randint(0, 256, (17, 9, 3), dtype=np.uint8)
    img_17x9_copy = img_17x9.copy()
    out_17x9 = fn(img_17x9)
    assert out_17x9.shape == (17, 9, 3)
    assert out_17x9.dtype == np.uint8
    assert np.array_equal(img_17x9, img_17x9_copy)


def test_edges_on_black_frame() -> None:
    fn = get_filter("edges")
    black = np.zeros((50, 50, 3), dtype=np.uint8)
    out = fn(black)
    assert out.shape == black.shape
    assert out.dtype == black.dtype
    assert np.all(out == 0)


def test_edges_coloring() -> None:
    fn = get_filter("edges")
    # Frame with a high contrast vertical bar in the middle
    frame = np.zeros((60, 60, 3), dtype=np.uint8)
    frame[:, 30:] = 255
    out = fn(frame)
    assert out.shape == frame.shape
    assert out.dtype == frame.dtype

    # Non-zero pixels should be cyan BGR (255, 255, 0)
    non_zero = out[np.any(out > 0, axis=-1)]
    assert len(non_zero) > 0
    assert np.all(non_zero == [255, 255, 0])


def test_next_filter_id_cycling() -> None:
    assert next_filter_id("purple", 1) == "thermal"
    assert next_filter_id("sabertooth", 1) == "purple"  # wraps forward
    assert next_filter_id("purple", -1) == "sabertooth"  # wraps backward
    assert next_filter_id("sepia", 2) == "edges"
    assert next_filter_id("purple", 0) == "purple"
    assert next_filter_id("gray", len(FILTER_IDS)) == "gray"


def test_get_filter_unknown_id() -> None:
    with pytest.raises(KeyError):
        get_filter("nope")


def test_sabertooth_filter() -> None:
    assert len(FILTER_IDS) == 9
    assert FILTER_IDS[-1] == "sabertooth"

    fn = get_filter("sabertooth")
    img = np.array([[[1, 2, 3], [4, 5, 6]]], dtype=np.uint8)
    out = fn(img)
    assert out is not img
    assert np.array_equal(out, img)
