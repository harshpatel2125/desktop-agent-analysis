import time

import pyautogui


def hotkey(*keys, hold: float = 0.04) -> None:
    """Press a modifier chord reliably on macOS.

    `pyautogui.hotkey()` with `pyautogui.PAUSE = 0` (which the blackpearl sets for fast
    mouse motion) fires the modifier keydowns and the main key too fast for macOS to
    register them together — so e.g. Cmd+Shift+P silently degrades into a literal "p".
    This helper holds each modifier down with a small delay, presses the final key
    while they're held, then releases the modifiers in reverse order.

    A single key with no modifiers is just pressed.
    """
    *mods, final = keys
    for m in mods:
        pyautogui.keyDown(m)
        time.sleep(hold)
    if mods:
        time.sleep(hold)
    pyautogui.press(final)
    time.sleep(hold)
    for m in reversed(mods):
        pyautogui.keyUp(m)
        time.sleep(hold / 2)
