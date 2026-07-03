import time as _time
from typing import Callable

from core.rng import RNG


class IntervalTimer:
    """Fires once per sampled interval; re-samples on reset()."""

    def __init__(self, interval_range, clock: Callable[[], float] = _time.monotonic):
        self._range = interval_range
        self._clock = clock
        self._last = clock()
        self._sampled = self._draw()

    def _draw(self) -> float:
        lo, hi = self._range
        return RNG.uniform(lo, hi)

    def due(self) -> bool:
        return (self._clock() - self._last) >= self._sampled

    def reset(self) -> None:
        self._last = self._clock()
        self._sampled = self._draw()
