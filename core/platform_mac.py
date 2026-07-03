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
    """Seconds since the last input event seen at the HID system state.

    NOTE: on some macOS versions/configurations this can also be reset by the
    process's OWN synthetically-posted (pyautogui/CGEventPost) input, not only by
    genuine hardware input. `PauseController` compensates for that with a short
    grace window (see `core.injected`) rather than trusting this value alone.
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


_VSCODE_NAMES = ("Code", "Visual Studio Code")  # localizedName() varies by build


def is_vscode_frontmost() -> bool:
    return frontmost_app() in _VSCODE_NAMES


def wait_until_frontmost(check_fn, timeout: float = 3.0, poll: float = 0.15) -> bool:
    """Poll `check_fn()` until it's True or `timeout` seconds pass. Returns the final
    reading. Use this before typing anything — activate_app() only REQUESTS focus;
    it doesn't confirm the OS actually switched it (animation delay, Spaces, a modal
    stealing focus, etc.), and typing without confirming can land keystrokes in
    whatever window WAS focused (e.g. the terminal running this script)."""
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if check_fn():
            return True
        time.sleep(poll)
    return check_fn()


class PauseController:
    """Pause flag driven by (a) a sentinel file and (b) real human activity.

    Pauses when the sentinel file exists OR — if auto_pause is on — when a real
    person appears to have used the mouse/keyboard within the last `resume_after`
    seconds. It reads HID idle time, which is *intended* to reflect only genuine
    hardware input — but a low reading right after the script's OWN injected input
    would be indistinguishable from a real human touching the machine. To guard
    against that, a low idle reading is only trusted once at least `own_input_grace`
    seconds have passed since the script itself last posted input (tracked by
    `core.injected`) — so a self-caused blip can't be mistaken for either "the human
    is here" or, just as importantly, "the human left" reasoning holding while we're
    mid-action.

    Manual pause: `touch /tmp/blackpearl_pause` (resume: remove it).
    """

    SENTINEL = "/tmp/blackpearl_pause"

    def __init__(self, auto_pause: bool = True, resume_after: float = 120.0,
                 idle_fn=hid_idle_seconds, own_input_recency_fn=None,
                 own_input_grace: float = 1.5, poll: float = 0.5,
                 on_error=None):
        self._paused = False
        self._auto_pause = auto_pause
        self._resume_after = resume_after
        self._idle_fn = idle_fn
        if own_input_recency_fn is None:
            from core.injected import seconds_since_last as own_input_recency_fn
        self._own_input_recency_fn = own_input_recency_fn
        self._own_input_grace = own_input_grace
        self._poll_interval = poll
        self._on_error = on_error or (lambda exc: None)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    @property
    def paused(self) -> bool:
        return self._paused

    def _decide_paused(self, idle_seconds: float, sentinel_exists: bool,
                        own_input_recent: bool) -> bool:
        if sentinel_exists:
            return True
        if not self._auto_pause:
            return False
        if own_input_recent:
            # A low idle reading right now could be explained by OUR OWN last action —
            # don't trust it either way; fall back to "not paused" so the harness keeps
            # working through its own activity instead of falsely pausing on itself.
            return False
        return idle_seconds < self._resume_after  # a human was active recently

    def _poll(self):
        while not self._stop.is_set():
            try:
                idle = self._idle_fn() if self._auto_pause else float("inf")
                own_recent = (self._own_input_recency_fn() < self._own_input_grace
                              if self._auto_pause else False)
                self._paused = self._decide_paused(
                    idle, os.path.exists(self.SENTINEL), own_recent)
            except Exception as exc:
                # Never let the poll thread die silently — a dead thread freezes
                # `paused` at its last value forever, which looks exactly like
                # "auto-pause stopped working" with no visible cause.
                self._on_error(exc)
            time.sleep(self._poll_interval)
