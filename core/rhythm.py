import time as _time
from typing import Callable

from core.rng import RNG, weighted_choice


def sample_edit_interval(cfg) -> float:
    lo, hi = weighted_choice(cfg.edit_interval_dist)
    return RNG.uniform(lo, hi)


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


class EditGate:
    """Edit fires only when BOTH the min gap and a freshly sampled interval elapse."""

    def __init__(self, cfg, clock: Callable[[], float] = _time.monotonic):
        self._cfg = cfg
        self._clock = clock
        self._last = clock()
        self._sampled = sample_edit_interval(cfg)

    def due(self) -> bool:
        elapsed = self._clock() - self._last
        return elapsed >= self._cfg.edit_min_gap and elapsed >= self._sampled

    def fired(self) -> None:
        self._last = self._clock()
        self._sampled = sample_edit_interval(self._cfg)
