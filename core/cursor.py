import threading

from core.rng import RNG


class CursorKeeper:
    """Background thread that nudges the cursor at least every `interval` (max) seconds.

    This guarantees the cursor keeps moving even during the main loop's long sleeps
    (edit "persist" waits, backend linger, npm-install waits, etc.), so no idle gap
    forms. It SKIPS while `is_paused()` is True, so it never fights a real user who has
    taken over the machine. A move error is reported via `on_error` (not silently
    dropped — a swallowed exception here looks exactly like "the cursor stopped moving
    for no reason") but never kills the thread.
    """

    def __init__(self, move_fn, is_paused, interval=(12.0, 20.0), lock=None,
                 on_error=None):
        self._move = move_fn
        self._is_paused = is_paused
        self._interval = interval           # (min, max) seconds; max must stay <= target
        self._lock = lock                   # shared with the main loop; None = no lock
        self._on_error = on_error or (lambda exc: None)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    def _run(self):
        # wait() returns True if stopped, False on timeout — an interruptible sleep of
        # at most `interval` seconds, so a nudge is attempted at least that often.
        while not self._stop.wait(RNG.uniform(*self._interval)):
            if self._is_paused():
                continue
            # Never post a nudge while the main loop holds the input_lock (it's mid-
            # action): a concurrent move would drag the cursor off a click/bezier target.
            # A held lock means the main loop is itself producing movement, so skipping
            # this tick leaves no idle gap. try-acquire so we never block the timer.
            if self._lock is not None and not self._lock.acquire(blocking=False):
                continue
            try:
                self._move()
            except Exception as exc:
                self._on_error(exc)
            finally:
                if self._lock is not None:
                    self._lock.release()
