import math

from tmpmask.handtypes import Point

Quad = tuple[Point, Point, Point, Point]


class PortalSmoother:
    def __init__(
        self,
        alpha: float = 0.5,
        fade_in_frames: int = 5,
        fade_out_frames: int = 6,
        reset_distance: float = 200.0,
    ) -> None:
        self.alpha = float(alpha)
        self.fade_in_frames = int(fade_in_frames)
        self.fade_out_frames = int(fade_out_frames)
        self.reset_distance = float(reset_distance)

        self._state: Quad | None = None
        self._opacity: float = 0.0

    def reset(self) -> None:
        self._state = None
        self._opacity = 0.0

    def update(self, quad: Quad | None) -> tuple[Quad | None, float]:
        if quad is not None:
            if self._state is None:
                self._state = quad
            else:
                # Check if any point jumped more than reset_distance
                jumped = any(
                    math.hypot(p[0] - s[0], p[1] - s[1]) > self.reset_distance
                    for p, s in zip(quad, self._state, strict=True)
                )
                if jumped:
                    self._state = quad
                else:
                    smoothed = tuple(
                        (
                            self.alpha * p[0] + (1.0 - self.alpha) * s[0],
                            self.alpha * p[1] + (1.0 - self.alpha) * s[1],
                        )
                        for p, s in zip(quad, self._state, strict=True)
                    )
                    self._state = (smoothed[0], smoothed[1], smoothed[2], smoothed[3])

            self._opacity = min(1.0, self._opacity + 1.0 / self.fade_in_frames)
            return self._state, self._opacity

        if self._state is None:
            return None, 0.0

        self._opacity -= 1.0 / self.fade_out_frames
        if self._opacity <= 1e-9:
            self._state = None
            self._opacity = 0.0
            return None, 0.0

        return self._state, self._opacity
