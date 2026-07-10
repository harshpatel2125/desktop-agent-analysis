"""Detect GENUINE hardware input, ignoring the harness's own synthetic input.

Why this exists: `CGEventSourceSecondsSinceLastEventType(HIDSystemState)` — what the
old detector used — is reset by the process's OWN pyautogui/CGEventPost input on this
platform, not just by a real person. Measured directly: sitting still read ~3.4s idle,
and a single synthetic `moveTo` dropped it to ~0.06s. So HID idle cannot tell "a human
is here" from "the harness just moved the cursor," and the 1.5s grace window the old
code used to paper over that was both too short (false self-pauses in the 1.5-120s
window after our own nudge) and unable, in principle, to spot a real human mid-burst.

A CGEventTap sees every input event AND the source process id. Our own posted events
carry our PID; genuine hardware input carries PID 0 (WindowServer/driver). So we tap the
session, record the timestamp of any event whose source PID != our PID, and expose
`seconds_since_last_human_input()`. No grace window, no guessing — our own activity is
excluded by identity, not by timing.

Requires Input Monitoring permission (same class of permission pyautogui already needs
to POST events). If the tap can't be created, `active` is False and the caller should
fall back / warn rather than silently trust a bogus reading.
"""
import os
import threading
import time

import Quartz

_MY_PID = os.getpid()

# Any event a person could generate. Modifier-only presses arrive as FlagsChanged, so
# include it — otherwise holding Shift/Cmd alone wouldn't count as "a human is here".
_HUMAN_EVENTS = (
    Quartz.kCGEventLeftMouseDown, Quartz.kCGEventLeftMouseUp,
    Quartz.kCGEventRightMouseDown, Quartz.kCGEventRightMouseUp,
    Quartz.kCGEventOtherMouseDown, Quartz.kCGEventOtherMouseUp,
    Quartz.kCGEventMouseMoved,
    Quartz.kCGEventLeftMouseDragged, Quartz.kCGEventRightMouseDragged,
    Quartz.kCGEventOtherMouseDragged,
    Quartz.kCGEventKeyDown, Quartz.kCGEventKeyUp,
    Quartz.kCGEventFlagsChanged, Quartz.kCGEventScrollWheel,
)

# The OS disables a tap that blocks too long or on a fast user-switch; the callback must
# re-enable it or it goes deaf silently (which would look exactly like "pause stopped
# working"). These arrive as the event type in the callback.
_TAP_DISABLED = (Quartz.kCGEventTapDisabledByTimeout,
                 Quartz.kCGEventTapDisabledByUserInput)


class HumanInputMonitor:
    """Background CGEventTap tracking the last GENUINE (non-self) input.

    `seconds_since_last_human_input()` returns a large number until a real person acts,
    regardless of how much the harness itself is moving/clicking/typing. `active` is
    False if the tap couldn't be created (missing Input Monitoring permission) — the
    caller decides how to degrade.
    """

    def __init__(self, clock=time.monotonic, my_pid: int = _MY_PID):
        self._clock = clock
        self._my_pid = my_pid
        self._last_human = clock() - 10_000.0  # "no human input yet"
        self._lock = threading.Lock()
        self._stop = threading.Event()
        self._loop_ref = None
        self._active = False
        self._ready = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    @property
    def active(self) -> bool:
        return self._active

    def start(self, wait: float = 2.0) -> bool:
        """Start the tap thread; block up to `wait`s for it to report ready. Returns
        `active` so the caller can warn if the tap couldn't be created."""
        self._thread.start()
        self._ready.wait(wait)
        return self._active

    def stop(self):
        self._stop.set()
        loop = self._loop_ref
        if loop is not None:
            Quartz.CFRunLoopStop(loop)

    def seconds_since_last_human_input(self) -> float:
        with self._lock:
            return self._clock() - self._last_human

    def _mark_human(self):
        with self._lock:
            self._last_human = self._clock()

    def _callback(self, proxy, etype, event, refcon):
        try:
            if etype in _TAP_DISABLED:
                Quartz.CGEventTapEnable(self._tap, True)
                return event
            src_pid = Quartz.CGEventGetIntegerValueField(
                event, Quartz.kCGEventSourceUnixProcessID)
            if src_pid != self._my_pid:
                self._mark_human()
        except Exception:
            # A raising callback can destabilize the tap; never let it propagate.
            pass
        return event

    def _run(self):
        mask = 0
        for ev in _HUMAN_EVENTS:
            mask |= Quartz.CGEventMaskBit(ev)
        self._tap = Quartz.CGEventTapCreate(
            Quartz.kCGSessionEventTap, Quartz.kCGHeadInsertEventTap,
            Quartz.kCGEventTapOptionListenOnly, mask, self._callback, None)
        if not self._tap:
            self._active = False
            self._ready.set()
            return
        src = Quartz.CFMachPortCreateRunLoopSource(None, self._tap, 0)
        loop = Quartz.CFRunLoopGetCurrent()
        self._loop_ref = loop
        Quartz.CFRunLoopAddSource(loop, src, Quartz.kCFRunLoopCommonModes)
        Quartz.CGEventTapEnable(self._tap, True)
        self._active = True
        self._ready.set()
        while not self._stop.is_set():
            # Return to the loop periodically so stop() is honored promptly even if no
            # events arrive (CFRunLoopStop from stop() also breaks us out immediately).
            Quartz.CFRunLoopRunInMode(Quartz.kCFRunLoopDefaultMode, 0.5, False)
