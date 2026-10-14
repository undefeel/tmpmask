import math
from collections.abc import Sequence

from tmpmask.handtypes import FINGERTIPS, Hand


def is_pinch(hand: Hand, ratio: float = 0.35) -> bool:
    """Return True when every fingertip is closer to their centroid than ratio * hand.size().

    A hand with size() == 0 is never a pinch.
    """
    scale = hand.size()
    if scale <= 0.0:
        return False

    tip_points = [hand.point(idx) for idx in FINGERTIPS]
    centroid_x = sum(p[0] for p in tip_points) / len(tip_points)
    centroid_y = sum(p[1] for p in tip_points) / len(tip_points)

    max_dist = ratio * scale
    for p in tip_points:
        dist = math.hypot(p[0] - centroid_x, p[1] - centroid_y)
        if dist >= max_dist:
            return False

    return True


class PinchTrigger:
    def __init__(
        self,
        ratio: float = 0.35,
        cooldown_s: float = 0.8,
        release_frames: int = 3,
    ) -> None:
        self.ratio = ratio
        self.cooldown_s = cooldown_s
        self.release_frames = release_frames

        self._armed = True
        self._consecutive_unpinched = 0
        self._last_trigger_time: float | None = None

    def update(self, hands: Sequence[Hand], now_s: float) -> bool:
        """Update trigger state and return True on rising edge of a pinch."""
        any_pinching = any(is_pinch(h, ratio=self.ratio) for h in hands)

        if any_pinching:
            self._consecutive_unpinched = 0
            if self._armed:
                can_trigger = (
                    self._last_trigger_time is None
                    or (now_s - self._last_trigger_time) >= self.cooldown_s
                )
                if can_trigger:
                    self._last_trigger_time = now_s
                    self._armed = False
                    return True
                else:
                    self._armed = False
                    return False
            return False
        else:
            if not self._armed:
                self._consecutive_unpinched += 1
                if self._consecutive_unpinched >= self.release_frames:
                    self._armed = True
            return False
