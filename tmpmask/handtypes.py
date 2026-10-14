import math
from dataclasses import dataclass

Point = tuple[float, float]  # pixel coordinates (x, y)

WRIST = 0
THUMB_TIP = 4
INDEX_TIP = 8
MIDDLE_MCP = 9
MIDDLE_TIP = 12
RING_TIP = 16
PINKY_TIP = 20
FINGERTIPS = (THUMB_TIP, INDEX_TIP, MIDDLE_TIP, RING_TIP, PINKY_TIP)


@dataclass(frozen=True)
class Hand:
    handedness: str  # "Left" or "Right" as reported by MediaPipe
    points: tuple[Point, ...]  # exactly 21 landmarks in pixels

    def __post_init__(self):
        if len(self.points) != 21:
            raise ValueError(f"Hand must have exactly 21 points, got {len(self.points)}")

    def point(self, index: int) -> Point:
        return self.points[index]

    def size(self) -> float:
        """Distance WRIST -> MIDDLE_MCP, used as hand scale."""
        wrist = self.points[WRIST]
        mcp = self.points[MIDDLE_MCP]
        return math.hypot(mcp[0] - wrist[0], mcp[1] - wrist[1])
