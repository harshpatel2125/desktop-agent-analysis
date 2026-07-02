import os
import subprocess
import threading
import time

from AppKit import NSWorkspace  # pyobjc
from Quartz import (  # pyobjc
    CGEventSourceSecondsSinceLastEventType,
    kCGEventSourceStateHIDSystemState,
)

_ANY_INPUT_EVENT = 0xFFFFFFFF  # kCGAnyInputEventType


def hid_idle_seconds() -> float:
    """Seconds since the last REAL hardware (HID) input event.

    Crucially this uses the HID system state, which is NOT reset by injected
    (pyautogui/CGEvent) events — so the blackpearl's own synthetic input does not
    count. This measures only genuine human mouse/keyboard activity.
    """
    return float(CGEventSourceSecondsSinceLastEventType(
        kCGEventSourceStateHIDSystemState, _ANY_INPUT_EVENT))


def activate_app(name: str) -> None:
    # `open -a` is more reliable than AppleScript `tell ... to activate`, which
    # intermittently fails with "-609 Connection is invalid" right after launch
    # or under load. `open -a` brings the app to the front (launching if needed).
    subprocess.run(["open", "-a", name], check=False)


def frontmost_app() -> str:
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return app.localizedName() if app else ""


def is_frontmost(name: str) -> bool:
    return frontmost_app() == name


class PauseController:
    """Pause flag driven by (a) a sentinel file and (b) real human activity.

    Pauses when the sentinel file exists OR — if auto_pause is on — when a real
    person has used the mouse/keyboard within the last `resume_after` seconds.
    Because it reads HID idle time (which the blackpearl's own injected input does
    NOT reset), the script backs off the instant you touch the machine and
    resumes only after `resume_after` seconds of no genuine input.

    Manual pause: `touch /tmp/blackpearl_pause` (resume: remove it).
    """

    SENTINEL = "/tmp/blackpearl_pause"

    def __init__(self, auto_pause: bool = True, resume_after: float = 120.0,
                 idle_fn=hid_idle_seconds, poll: float = 0.5):
        self._paused = False
        self._auto_pause = auto_pause
        self._resume_after = resume_after
        self._idle_fn = idle_fn
        self._poll_interval = poll
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    @property
    def paused(self) -> bool:
        return self._paused

    def _decide_paused(self, idle_seconds: float, sentinel_exists: bool) -> bool:
        if sentinel_exists:
            return True
        if self._auto_pause and idle_seconds < self._resume_after:
            return True  # a human was active within the last `resume_after` seconds
        return False

    def _poll(self):
        while not self._stop.is_set():
            idle = self._idle_fn() if self._auto_pause else float("inf")
            self._paused = self._decide_paused(idle, os.path.exists(self.SENTINEL))
            time.sleep(self._poll_interval)
