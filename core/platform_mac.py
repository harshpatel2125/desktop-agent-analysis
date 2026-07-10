import os
import subprocess
import threading
import time

from AppKit import NSWorkspace  # pyobjc


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
_CHROME = "Google Chrome"


def is_vscode_frontmost() -> bool:
    return frontmost_app() in _VSCODE_NAMES


def is_chrome_frontmost() -> bool:
    return frontmost_app() == _CHROME


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

    Pauses when the sentinel file exists OR — if auto_pause is on — when a genuine
    person used the mouse/keyboard within the last `resume_after` seconds.

    "Genuine" is the whole game here. It reads `human_idle_fn`, which is backed by a
    CGEventTap that records only input NOT posted by this process (see
    `core.human_input`). That replaces the old HID-idle reading, which this platform
    resets on the harness's OWN synthetic input — making the harness's cursor nudges
    look like a human and forcing it to pause itself. Because self vs. human is now
    told apart by source PID, not by a timing grace window, a real person is detected
    even while the harness is mid-action, and the harness never false-pauses on itself.

    Manual pause: `touch /tmp/blackpearl_pause` (resume: remove it).
    """

    SENTINEL = "/tmp/blackpearl_pause"

    def __init__(self, auto_pause: bool = True, resume_after: float = 120.0,
                 human_idle_fn=None, poll: float = 0.5, on_error=None):
        self._paused = False
        self._auto_pause = auto_pause
        self._resume_after = resume_after
        self._monitor = None
        if human_idle_fn is None and auto_pause:
            from core.human_input import HumanInputMonitor
            self._monitor = HumanInputMonitor()
            human_idle_fn = self._monitor.seconds_since_last_human_input
        self._human_idle_fn = human_idle_fn or (lambda: float("inf"))
        self._poll_interval = poll
        self._on_error = on_error or (lambda exc: None)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    @property
    def monitor_active(self) -> bool:
        """True if the event-tap monitor is running (Input Monitoring granted). When
        False with auto_pause on, human detection is unavailable — only the sentinel
        file pauses — and the caller should warn."""
        return self._monitor is not None and self._monitor.active

    def start(self):
        if self._monitor is not None:
            self._monitor.start()
        self._thread.start()

    def stop(self):
        self._stop.set()
        if self._monitor is not None:
            self._monitor.stop()

    @property
    def paused(self) -> bool:
        return self._paused

    def _decide_paused(self, human_idle_seconds: float, sentinel_exists: bool) -> bool:
        if sentinel_exists:
            return True
        if not self._auto_pause:
            return False
        return human_idle_seconds < self._resume_after  # a real person was active

    def _poll(self):
        while not self._stop.is_set():
            try:
                idle = self._human_idle_fn() if self._auto_pause else float("inf")
                self._paused = self._decide_paused(idle, os.path.exists(self.SENTINEL))
            except Exception as exc:
                # Never let the poll thread die silently — a dead thread freezes
                # `paused` at its last value forever, which looks exactly like
                # "auto-pause stopped working" with no visible cause.
                self._on_error(exc)
            time.sleep(self._poll_interval)
