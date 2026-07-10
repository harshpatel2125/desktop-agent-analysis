"""Module rotation (which feature is active) and an active-time clock (freezes on pause).

- `ModuleScheduler` decides the feature for each 90-minute period:
    * `--module:a,b,c` (multiple)  -> strict cycle a, b, c, a, b, c, ...
    * `--module:a`     (single)    -> `a` for period 0, then random after
    * no flag                      -> random every period (never the same twice running)
- `ActiveClock` measures elapsed time that does NOT advance while paused, so a person
  taking over freezes the schedule instead of skipping the harness ahead.
"""
import threading
import time

from core.rng import RNG


def parse_module_flag(argv, valid_keys):
    """Extract a module sequence from args like `--module:email,calendar`.

    Returns a list of valid module keys in order (dropping unknown ones), or None if the
    flag is absent / yields nothing usable.
    """
    valid = set(valid_keys)
    for arg in argv:
        if arg.startswith("--module:") or arg.startswith("--module="):
            raw = arg.split(":", 1)[1] if arg.startswith("--module:") else arg.split("=", 1)[1]
            seq = [k.strip().lower() for k in raw.split(",") if k.strip()]
            seq = [k for k in seq if k in valid]
            return seq or None
    return None


class ModuleScheduler:
    """Maps a period index (elapsed // 90min) to a module key, memoized so a given period
    always resolves to the same module."""

    def __init__(self, all_keys, sequence=None, rng=RNG):
        self._keys = list(all_keys)
        self._seq = list(sequence) if sequence else None
        self._rng = rng
        self._chosen = []                      # module chosen per period index

    def module_for_period(self, i: int) -> str:
        while len(self._chosen) <= i:
            self._chosen.append(self._pick(len(self._chosen)))
        return self._chosen[i]

    def _pick(self, idx: int) -> str:
        if self._seq and len(self._seq) > 1:
            return self._seq[idx % len(self._seq)]
        if self._seq and len(self._seq) == 1:
            if idx == 0:
                return self._seq[0]
            return self._random(exclude=self._chosen[idx - 1])
        prev = self._chosen[idx - 1] if idx > 0 else None
        return self._random(exclude=prev)

    def _random(self, exclude=None) -> str:
        pool = [k for k in self._keys if k != exclude] or self._keys
        return self._rng.choice(pool)


class ActiveClock:
    """Elapsed seconds that advance only while NOT paused.

    Runs a background ticker in production; tests can drive it by toggling the paused
    state and calling `_pump()` after advancing an injected clock.
    """

    def __init__(self, is_paused, clock=time.monotonic, tick: float = 0.25):
        self._is_paused = is_paused
        self._clock = clock
        self._tick = tick
        self._active = 0.0
        self._last = clock()
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._last = self._clock()
        self._thread.start()

    def stop(self):
        self._stop.set()

    def elapsed(self) -> float:
        return self._active

    def _pump(self):
        now = self._clock()
        dt = now - self._last
        self._last = now
        if not self._is_paused():
            self._active += dt

    def _run(self):
        while not self._stop.wait(self._tick):
            self._pump()
