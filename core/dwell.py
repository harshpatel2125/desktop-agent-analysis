import time as _time
from typing import Callable

from core.rng import RNG


def dwell(seconds: float,
          activity: Callable[[], None],
          gap_range=(30.0, 50.0),
          sleep: Callable[[float], None] = _time.sleep,
          clock: Callable[[], float] = _time.monotonic,
          is_paused: Callable[[], bool] | None = None) -> int:
    """Hold a state for `seconds`, invoking `activity()` on a jittered sub-minute
    cadence (gap_range must stay under 60s) so no inactivity gap crosses an idle
    threshold. Returns the number of activity bursts performed.

    If `is_paused` is given and returns True, the dwell stops early WITHOUT firing
    activity — so the harness doesn't keep jittering while a real user is active
    (the caller's loop then handles the pause)."""
    end = clock() + seconds
    bursts = 0
    while clock() < end:
        if is_paused is not None and is_paused():
            break
        remaining = end - clock()
        nap = min(RNG.uniform(*gap_range), remaining)
        sleep(nap)
        if clock() < end:
            if is_paused is not None and is_paused():
                break
            activity()
            bursts += 1
    return bursts
