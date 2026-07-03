"""Tracks when the process last posted a SYNTHETIC input event.

Some CGEventSourceState idle-time queries can be reset by the process's own
CGEventPost-based input (moveTo/click/press/etc.), not just genuine hardware input.
That would defeat pause-detection: if the harness's own actions kept "idle" looking
small, a real user's activity would be indistinguishable from the harness's — a low
idle reading could be from either. `install()` wraps pyautogui's input-posting
functions once at startup so every call is timestamped; `seconds_since_last()` then
tells the caller how recently the harness itself acted. Pause-detection only trusts a
low idle reading as "a real human" once enough time has passed since our own last
injected input that the low reading can't be explained by us.
"""
import time as _time

import pyautogui

_last_injected = 0.0
_installed = False

_WRAPPED = ("moveTo", "click", "doubleClick", "tripleClick", "press", "scroll",
            "typewrite", "keyDown", "keyUp")


def _wrap(fn):
    def wrapped(*args, **kwargs):
        global _last_injected
        _last_injected = _time.monotonic()
        return fn(*args, **kwargs)
    return wrapped


def install():
    """Idempotent: wraps pyautogui's input functions once. Call before any GUI action."""
    global _installed
    if _installed:
        return
    for name in _WRAPPED:
        setattr(pyautogui, name, _wrap(getattr(pyautogui, name)))
    _installed = True


def seconds_since_last() -> float:
    return _time.monotonic() - _last_injected
