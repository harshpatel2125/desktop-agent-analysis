import threading

from core.rng import RNG


class CursorKeeper:
    """Background thread that nudges the cursor at least every `interval` (max) seconds.

    This guarantees the cursor keeps moving even during the main loop's long sleeps
    (edit "persist" waits, backend linger, npm-install waits, etc.), so no idle gap
    forms. It SKIPS while `is_paused()` is True, so it never fights a real user who has
    taken over the machine. Move errors are swallowed so the keeper never dies.
    """

    def __init__(self, move_fn, is_paused, interval=(12.0, 20.0)):
        self._move = move_fn
        self._is_paused = is_paused
        self._interval = interval           # (min, max) seconds; max must stay <= target
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
            if not self._is_paused():
                try:
                    self._move()
                except Exception:
                    pass
