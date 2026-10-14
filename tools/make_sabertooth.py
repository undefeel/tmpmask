#!/usr/bin/env python3
"""Script to extract sabertooth emblem from source image and write BGRA asset."""

from pathlib import Path

import cv2
import numpy as np

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_PATH = REPO_ROOT / "assets" / "source" / "sabertooth.png"
OUTPUT_PATH = REPO_ROOT / "tmpmask" / "assets" / "sabertooth.png"


def make_sabertooth(
    source_path: Path = SOURCE_PATH,
    output_path: Path = OUTPUT_PATH,
) -> None:
    if not source_path.exists():
        raise FileNotFoundError(f"Source image not found: {source_path}")

    img = cv2.imread(str(source_path))
    if img is None:
        raise ValueError(f"Failed to read source image: {source_path}")

    h, w = img.shape[:2]

    # Light pixels (all channels >= 200)
    light = (
        (img[:, :, 0] >= 200) & (img[:, :, 1] >= 200) & (img[:, :, 2] >= 200)
    ).astype(np.uint8) * 255

    # Flood fill from four corners to mark the exterior background
    flood = light.copy()
    ff_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    for pt in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if flood[pt[1], pt[0]] == 255:
            cv2.floodFill(flood, ff_mask, pt, 128)

    bg = flood == 128
    alpha = np.where(bg, 0, 255).astype(np.uint8)

    # Soften edge with small blur (<= 2 px)
    alpha_blurred = cv2.GaussianBlur(alpha, (3, 3), 0)

    # Bounding box of opaque area (so the circle touches image edges)
    ys, xs = np.where(alpha == 255)
    ymin, ymax = int(ys.min()), int(ys.max())
    xmin, xmax = int(xs.min()), int(xs.max())

    cropped_bgr = img[ymin : ymax + 1, xmin : xmax + 1]
    cropped_alpha = alpha_blurred[ymin : ymax + 1, xmin : xmax + 1]

    bgra = cv2.merge([
        cropped_bgr[:, :, 0],
        cropped_bgr[:, :, 1],
        cropped_bgr[:, :, 2],
        cropped_alpha,
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output_path), bgra)


if __name__ == "__main__":
    make_sabertooth()
