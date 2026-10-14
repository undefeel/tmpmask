"""Sabertooth asset loading and perspective overlay rendering module."""

from pathlib import Path

import cv2
import numpy as np

from tmpmask.portal import Quad

ASSETS_DIR: Path = Path(__file__).resolve().parent / "assets"


def load_rgba(path: Path | str) -> np.ndarray:
    """Load image from path as 4-channel BGRA/RGBA uint8 array.

    - cv2.imread(..., IMREAD_UNCHANGED)
    - 3-channel input gets alpha 255
    - FileNotFoundError if missing
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Image file not found: {path}")

    img = cv2.imread(str(p), cv2.IMREAD_UNCHANGED)
    if img is None:
        raise FileNotFoundError(f"Failed to decode image: {path}")

    if img.ndim == 2:
        # Grayscale -> BGRA
        bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        alpha = np.full((img.shape[0], img.shape[1], 1), 255, dtype=np.uint8)
        return np.concatenate([bgr, alpha], axis=2)

    if img.shape[2] == 3:
        alpha = np.full((img.shape[0], img.shape[1], 1), 255, dtype=np.uint8)
        return np.concatenate([img, alpha], axis=2)

    return img


def _is_degenerate_quad(quad: Quad) -> bool:
    """Check whether a quad is degenerate (area < 4 px², collinear, or all equal)."""
    p0, p1, p2, p3 = quad

    # All equal
    if p0 == p1 == p2 == p3:
        return True

    # 4 points collinear
    # Check max triangle area among triples formed with p0, p1, p2, p3
    def tri_area(a, b, c) -> float:
        return 0.5 * abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]))

    t1 = tri_area(p0, p1, p2)
    t2 = tri_area(p0, p1, p3)
    t3 = tri_area(p0, p2, p3)
    t4 = tri_area(p1, p2, p3)

    if max(t1, t2, t3, t4) < 1e-4:
        return True

    # Quad area: decompose into triangles (p0, p1, p2) and (p0, p2, p3)
    # Using sum of triangle areas ensures self-intersecting quads (bow-ties) have positive area
    total_area = t1 + t3
    if total_area < 4.0:
        return True

    return False


def render_overlay(
    frame: np.ndarray,
    quad: Quad,
    image_rgba: np.ndarray,
    opacity: float = 1.0,
    outline: bool = True,
) -> np.ndarray:
    """Render perspective-warped overlay image inside quad onto a new frame.

    - Input frame is not mutated.
    - Perspective-warp image_rgba so its corners (0,0), (w,0), (w,h), (0,h) map to
      quad points in order.
    - Output size = frame size, INTER_LINEAR, border transparent.
    - Per-pixel blend:
        a = alpha / 255 * clamp(opacity, 0, 1)
        out = frame * (1 - a) + warped_bgr * a
    - Pixels outside the quad are untouched.
    - If outline and opacity > 0, draw closed quad like portal.render_portal does
      (white, thickness 1, cv2.LINE_AA).
    - Degenerate quads (area < 4 px², collinear, all equal) or cv2.error from the transform
      return a copy of the frame without raising.
    - Self-intersecting quads must not raise.
    """
    h, w = frame.shape[:2]
    out = frame.copy()

    clamped_opacity = max(0.0, min(1.0, float(opacity)))

    # Compute poly points for outline
    pts = []
    for x, y in quad:
        ix = max(-4 * w, min(5 * w, int(round(x))))
        iy = max(-4 * h, min(5 * h, int(round(y))))
        pts.append([ix, iy])
    poly_pts = np.array([pts], dtype=np.int32)

    # Check for degenerate quad
    if _is_degenerate_quad(quad):
        return frame.copy()

    if clamped_opacity > 0.0:
        h_src, w_src = image_rgba.shape[:2]
        src_pts = np.array(
            [[0.0, 0.0], [float(w_src), 0.0], [float(w_src), float(h_src)], [0.0, float(h_src)]],
            dtype=np.float32,
        )
        dst_pts = np.array(quad, dtype=np.float32)

        try:
            m = cv2.getPerspectiveTransform(src_pts, dst_pts)
            warped = cv2.warpPerspective(
                image_rgba,
                m,
                (w, h),
                flags=cv2.INTER_LINEAR,
                borderMode=cv2.BORDER_CONSTANT,
                borderValue=(0, 0, 0, 0),
            )
        except cv2.error:
            return frame.copy()

        warped_alpha = warped[:, :, 3].astype(np.float32) / 255.0
        a = warped_alpha * clamped_opacity  # shape (h, w)

        active = a > 0.0
        if np.any(active):
            a_sub = a[active, np.newaxis]
            warped_bgr = warped[active, :3].astype(np.float32)
            frame_sub = frame[active].astype(np.float32)

            blended = frame_sub * (1.0 - a_sub) + warped_bgr * a_sub
            out[active] = np.clip(np.round(blended), 0, 255).astype(frame.dtype)

    if outline and clamped_opacity > 0.0:
        cv2.polylines(
            out,
            poly_pts,
            isClosed=True,
            color=(255, 255, 255),
            thickness=1,
            lineType=cv2.LINE_AA,
        )

    return out
