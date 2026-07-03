import time as _time
from typing import Callable

from core.rng import RNG


def paced_sleep(seconds: float,
                 is_paused: Callable[[], bool],
                 chunk_range=(1.0, 2.0),
                 sleep: Callable[[float], None] = _time.sleep,
                 clock: Callable[[], float] = _time.monotonic) -> bool:
    """Sleep for `seconds`, checking `is_paused()` every chunk_range seconds.

    A real user taking over the machine cuts the wait short instead of the harness
    grinding through the full duration (which is what made long waits like the
    backend-pull linger or an edit's "persist" sleep look like "auto-pause isn't
    working" — the flag flipped, but nothing was checking it mid-sleep).

    Returns True if the full duration elapsed unpaused, False if it was cut short.
    """
    end = clock() + seconds
    while clock() < end:
        if is_paused():
            return False
        nap = min(RNG.uniform(*chunk_range), end - clock())
        sleep(nap)
    return not is_paused()
