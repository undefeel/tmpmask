from pathlib import Path

import cv2
import numpy as np
import pytest

from tmpmask.overlay import ASSETS_DIR, load_rgba, render_overlay
from tmpmask.portal import Quad


def test_shipped_asset():
    asset_path = ASSETS_DIR / "sabertooth.png"
    assert asset_path.exists()

    img = load_rgba(asset_path)
    assert isinstance(img, np.ndarray)
    assert img.dtype == np.uint8
    assert img.ndim == 3
    assert img.shape[2] == 4

    h, w = img.shape[:2]
    # Its four corner pixels have alpha 0
    assert img[0, 0, 3] == 0
    assert img[0, w - 1, 3] == 0
    assert img[h - 1, 0, 3] == 0
    assert img[h - 1, w - 1, 3] == 0

    # Its centre pixel has alpha 255
    assert img[h // 2, w // 2, 3] == 255

    # A pixel on a fang/fur area inside the circle is opaque
    # Fang pixel at (124, 258)
    assert img[124, 258, 3] == 255


def test_load_rgba_converts_3channel(tmp_path: Path):
    bgr_path = tmp_path / "test_bgr.png"
    bgr_img = np.full((20, 20, 3), 123, dtype=np.uint8)
    cv2.imwrite(str(bgr_path), bgr_img)

    loaded = load_rgba(bgr_path)
    assert loaded.shape == (20, 20, 4)
    assert loaded.dtype == np.uint8
    assert np.all(loaded[:, :, :3] == 123)
    assert np.all(loaded[:, :, 3] == 255)


def test_load_rgba_missing_file():
    with pytest.raises(FileNotFoundError):
        load_rgba("non_existent_image_12345.png")


def test_render_overlay_solid_red_and_outside_untouched():
    # 200x200 neutral gray frame (100, 100, 100)
    frame = np.full((200, 200, 3), 100, dtype=np.uint8)

    # 10x10 solid red opaque image (BGR = [0, 0, 255], Alpha = 255)
    red_rgba = np.zeros((10, 10, 4), dtype=np.uint8)
    red_rgba[:, :, :3] = [0, 0, 255]
    red_rgba[:, :, 3] = 255

    # 100x100 square quad from (50, 50) to (150, 150)
    # TL, TR, BR, BL
    quad: Quad = ((50.0, 50.0), (150.0, 50.0), (150.0, 150.0), (50.0, 150.0))

    out = render_overlay(frame, quad, red_rgba, opacity=1.0, outline=False)

    # Quad centre (100, 100) should be red
    np.testing.assert_array_equal(out[100, 100], [0, 0, 255])

    # Outside pixel (10, 10) left unchanged
    np.testing.assert_array_equal(out[10, 10], frame[10, 10])


def test_render_overlay_opacity_blend():
    frame = np.full((100, 100, 3), 100, dtype=np.uint8)

    red_rgba = np.zeros((10, 10, 4), dtype=np.uint8)
    red_rgba[:, :, :3] = [0, 0, 255]
    red_rgba[:, :, 3] = 255

    quad: Quad = ((20.0, 20.0), (80.0, 20.0), (80.0, 80.0), (20.0, 80.0))

    # Opacity 0.6: expected centre = 100 * (1 - 0.6) + [0, 0, 255] * 0.6 = [40, 40, 193]
    out = render_overlay(frame, quad, red_rgba, opacity=0.6, outline=False)

    expected = np.array([40, 40, 193], dtype=np.int16)
    actual = out[50, 50].astype(np.int16)
    assert np.all(np.abs(actual - expected) <= 2)


def test_render_overlay_transparent_image():
    frame = np.full((100, 100, 3), 100, dtype=np.uint8)

    # Completely transparent image (alpha = 0)
    transparent_rgba = np.full((10, 10, 4), (0, 255, 0, 0), dtype=np.uint8)
    quad: Quad = ((20.0, 20.0), (80.0, 20.0), (80.0, 80.0), (20.0, 80.0))

    out = render_overlay(frame, quad, transparent_rgba, opacity=1.0, outline=False)
    np.testing.assert_array_equal(out, frame)


def test_render_overlay_degenerate_and_bowtie():
    frame = np.full((100, 100, 3), 100, dtype=np.uint8)
    red_rgba = np.zeros((10, 10, 4), dtype=np.uint8)
    red_rgba[:, :, :3] = [0, 0, 255]
    red_rgba[:, :, 3] = 255

    # 1. All equal
    quad_equal: Quad = ((10.0, 10.0), (10.0, 10.0), (10.0, 10.0), (10.0, 10.0))
    res_equal = render_overlay(frame, quad_equal, red_rgba, opacity=1.0)
    assert res_equal.shape == frame.shape
    np.testing.assert_array_equal(res_equal, frame)

    # 2. Collinear
    quad_collinear: Quad = ((10.0, 10.0), (20.0, 20.0), (30.0, 30.0), (40.0, 40.0))
    res_collinear = render_overlay(frame, quad_collinear, red_rgba, opacity=1.0)
    assert res_collinear.shape == frame.shape
    np.testing.assert_array_equal(res_collinear, frame)

    # 3. Area < 4 px²
    quad_tiny: Quad = ((10.0, 10.0), (11.0, 10.0), (11.0, 11.0), (10.0, 11.0))
    res_tiny = render_overlay(frame, quad_tiny, red_rgba, opacity=1.0)
    assert res_tiny.shape == frame.shape
    np.testing.assert_array_equal(res_tiny, frame)

    # 4. Bow-tie (self-intersecting) quad - must not raise
    quad_bowtie: Quad = ((10.0, 10.0), (90.0, 90.0), (90.0, 10.0), (10.0, 90.0))
    res_bowtie = render_overlay(frame, quad_bowtie, red_rgba, opacity=1.0)
    assert res_bowtie.shape == frame.shape


def test_render_overlay_input_not_mutated():
    frame = np.full((100, 100, 3), 100, dtype=np.uint8)
    frame_orig = frame.copy()

    red_rgba = np.zeros((10, 10, 4), dtype=np.uint8)
    red_rgba[:, :, :3] = [0, 0, 255]
    red_rgba[:, :, 3] = 255

    quad: Quad = ((20.0, 20.0), (80.0, 20.0), (80.0, 80.0), (20.0, 80.0))

    _ = render_overlay(frame, quad, red_rgba, opacity=1.0, outline=True)
    np.testing.assert_array_equal(frame, frame_orig)


def test_render_overlay_outline():
    frame = np.zeros((100, 100, 3), dtype=np.uint8)
    transparent_rgba = np.zeros((10, 10, 4), dtype=np.uint8)
    quad: Quad = ((20.0, 20.0), (80.0, 20.0), (80.0, 80.0), (20.0, 80.0))

    # With outline=True and opacity > 0, boundary has white line pixels
    res = render_overlay(frame, quad, transparent_rgba, opacity=1.0, outline=True)
    assert np.all(res[20, 50] > 200)
    assert np.all(res[20, 50] == res[20, 50, 0])
