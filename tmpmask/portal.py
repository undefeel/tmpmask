from collections.abc import Callable, Sequence

import cv2
import numpy as np

from tmpmask.handtypes import INDEX_TIP, THUMB_TIP, WRIST, Hand, Point

Quad = tuple[Point, Point, Point, Point]


def portal_quad(hands: Sequence[Hand]) -> Quad | None:
    """Extract portal quadrilateral from exactly two hands.

    Sorts hands by the x coordinate of their WRIST point (smaller x = left on screen).
    Returns (left.INDEX_TIP, right.INDEX_TIP, right.THUMB_TIP, left.THUMB_TIP) or None
    if hands count is not exactly 2.
    """
    if len(hands) != 2:
        return None

    left, right = sorted(hands, key=lambda h: h.point(WRIST)[0])
    return (
        left.point(INDEX_TIP),
        right.point(INDEX_TIP),
        right.point(THUMB_TIP),
        left.point(THUMB_TIP),
    )


def render_portal(
    frame: np.ndarray,
    quad: Quad,
    filter_fn: Callable[[np.ndarray], np.ndarray],
    opacity: float = 1.0,
    outline: bool = True,
) -> np.ndarray:
    """Render filtered portal inside quad onto a new frame.

    - Input frame is not mutated.
    - Mask is created with cv2.fillPoly using integer-rounded coordinates clipped into frame.
    - Inside mask: out = frame * (1 - opacity) + filtered * opacity.
    - Opacity clamped to [0.0, 1.0].
    - If outline and opacity > 0, closed quad boundary is drawn with white cv2.LINE_AA.
    - Degenerate quads do not raise.
    """
    h, w = frame.shape[:2]
    out = frame.copy()

    clamped_opacity = max(0.0, min(1.0, float(opacity)))

    # Round to int; clamp to a generous range around the frame so off-screen fingertips keep
    # the quad shape (fillPoly clips by itself) while avoiding int32 overflow.
    pts = []
    for x, y in quad:
        ix = max(-4 * w, min(5 * w, int(round(x))))
        iy = max(-4 * h, min(5 * h, int(round(y))))
        pts.append([ix, iy])

    poly_pts = np.array([pts], dtype=np.int32)

    if clamped_opacity > 0.0:
        mask = np.zeros((h, w), dtype=np.uint8)
        cv2.fillPoly(mask, poly_pts, 255)

        inside = mask > 0
        if np.any(inside):
            filtered = filter_fn(frame)
            if clamped_opacity == 1.0:
                out[inside] = filtered[inside]
            else:
                blended = (
                    frame[inside].astype(np.float32) * (1.0 - clamped_opacity)
                    + filtered[inside].astype(np.float32) * clamped_opacity
                )
                out[inside] = np.clip(np.round(blended), 0, 255).astype(frame.dtype)

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
