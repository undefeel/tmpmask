"""Image filter functions and registry."""

from collections.abc import Callable

import cv2
import numpy as np

FilterFn = Callable[[np.ndarray], np.ndarray]

FILTER_IDS: tuple[str, ...] = (
    "purple",
    "thermal",
    "invert",
    "gray",
    "ocean",
    "sepia",
    "pixelate",
    "edges",
)

# Classic sepia transformation matrix for BGR representation:
# [B']   [0.131 0.534 0.272] [B]
# [G'] = [0.168 0.686 0.349] [G]
# [R']   [0.189 0.769 0.393] [R]
# Derived from:
# tr = 0.393*r + 0.769*g + 0.189*b
# tg = 0.349*r + 0.686*g + 0.168*b
# tb = 0.272*r + 0.534*g + 0.131*b
_SEPIA_KERNEL_BGR = np.array(
    [
        [0.131, 0.534, 0.272],
        [0.168, 0.686, 0.349],
        [0.189, 0.769, 0.393],
    ],
    dtype=np.float32,
)


def filter_purple(frame: np.ndarray) -> np.ndarray:
    """Blend frame with solid purple BGR (160, 32, 128), weight 0.6 for colour."""
    purple = np.full_like(frame, (160, 32, 128), dtype=np.uint8)
    return cv2.addWeighted(frame, 0.4, purple, 0.6, 0.0)


def filter_thermal(frame: np.ndarray) -> np.ndarray:
    """Grayscale converted to COLORMAP_JET."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.applyColorMap(gray, cv2.COLORMAP_JET)


def filter_invert(frame: np.ndarray) -> np.ndarray:
    """Invert frame colors (255 - frame)."""
    return cv2.bitwise_not(frame)


def filter_gray(frame: np.ndarray) -> np.ndarray:
    """Grayscale converted back to 3-channel BGR."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)


def filter_ocean(frame: np.ndarray) -> np.ndarray:
    """Grayscale converted to COLORMAP_OCEAN."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return cv2.applyColorMap(gray, cv2.COLORMAP_OCEAN)


def filter_sepia(frame: np.ndarray) -> np.ndarray:
    """Classic sepia matrix applied in RGB order, clipped to 0..255."""
    return cv2.transform(frame, _SEPIA_KERNEL_BGR)


def filter_pixelate(frame: np.ndarray) -> np.ndarray:
    """Pixelate frame with 16 px block size."""
    h, w = frame.shape[:2]
    small_w = max(1, w // 16)
    small_h = max(1, h // 16)
    downscaled = cv2.resize(frame, (small_w, small_h), interpolation=cv2.INTER_LINEAR)
    return cv2.resize(downscaled, (w, h), interpolation=cv2.INTER_NEAREST)


def filter_edges(frame: np.ndarray) -> np.ndarray:
    """Canny edges colored cyan BGR (255, 255, 0) on a black background."""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 80, 160)
    out = np.zeros_like(frame)
    out[edges > 0] = (255, 255, 0)
    return out


_REGISTRY: dict[str, FilterFn] = {
    "purple": filter_purple,
    "thermal": filter_thermal,
    "invert": filter_invert,
    "gray": filter_gray,
    "ocean": filter_ocean,
    "sepia": filter_sepia,
    "pixelate": filter_pixelate,
    "edges": filter_edges,
}


def get_filter(filter_id: str) -> FilterFn:
    """Return filter function by id or raise KeyError."""
    if filter_id not in _REGISTRY:
        raise KeyError(f"Unknown filter id: {filter_id!r}")
    return _REGISTRY[filter_id]


def next_filter_id(current: str, step: int = 1) -> str:
    """Return next filter id cycling over FILTER_IDS. Step can be negative."""
    idx = FILTER_IDS.index(current)
    return FILTER_IDS[(idx + step) % len(FILTER_IDS)]
