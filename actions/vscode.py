# actions/vscode.py
import os
import shutil
import subprocess
import time

import pyautogui

from config import CONFIG
from core import mouse
from core.clipboard import get_clipboard, set_clipboard
from core.keyboard_sim import type_text
from core.keys import hotkey
from core.platform_mac import activate_app, is_vscode_frontmost, wait_until_frontmost
from core.rng import RNG

_VSCODE = "Visual Studio Code"


class FocusLostError(RuntimeError):
    """VS Code never actually came to the foreground. Callers must NOT type/click when
    this is raised — that is exactly what previously landed keystrokes in whatever
    window (e.g. the terminal running this script) happened to still have focus."""


def _focus():
    activate_app(_VSCODE)
    if not wait_until_frontmost(is_vscode_frontmost, timeout=3.0):
        raise FocusLostError("VS Code did not come to the foreground in time")
    time.sleep(RNG.uniform(0.15, 0.35))  # brief settle now that focus is CONFIRMED


def open_project(path: str):
    if shutil.which("code"):
        subprocess.run(["code", "--reuse-window", path], check=False)
    else:
        subprocess.run(["open", "-a", _VSCODE, path], check=False)
    time.sleep(2.0)
    _focus()


def open_file(rel_path: str) -> bool:
    """Open a file by PASTING its path into Quick Open (Cmd+P) — never typing it.

    Typing the path char-by-char mangled shifted characters (e.g. `(tabs)` came out as
    `9tabs)`, `.tsx` truncated to `.ts`) and could open the wrong file or none. Pasting
    the exact path (Cmd+V), like the Jira flow, is 100% accurate. The path is also checked
    to exist on disk first, so a bad entry is skipped rather than left as junk in the
    Quick Open box. Returns True if it attempted to open, False if the file is missing.
    """
    if not os.path.isfile(os.path.join(CONFIG.project_path, rel_path)):
        return False
    _focus()
    # Pull keyboard focus INTO the editor before opening Quick Open. Critical after a
    # Claude window: focus may be sitting in the Claude webview or the terminal, where
    # Cmd+P can be captured and the pasted path would land in the WRONG box. A click in
    # the editor body puts focus in the code (and dismisses any stray popup) first.
    _click_editor()
    if not is_vscode_frontmost():                     # confirm before any keystroke
        return False
    prev_clip = get_clipboard()                      # save the user's clipboard
    set_clipboard(rel_path)
    hotkey("command", "p")                            # open Quick Open (input focused)
    time.sleep(RNG.uniform(0.5, 0.8))
    if not is_vscode_frontmost():                     # re-verify before pasting
        pyautogui.press("escape")
        set_clipboard(prev_clip)
        return False
    hotkey("command", "v")                           # paste the exact path — no typos
    time.sleep(RNG.uniform(0.7, 1.1))                # let Quick Open filter to the match
    pyautogui.press("return")
    time.sleep(RNG.uniform(0.6, 1.0))
    set_clipboard(prev_clip)                         # restore the user's clipboard
    return True


def _click_editor():
    _focus()
    mouse.move_bezier(pyautogui.position(),
                      mouse.editor_point(CONFIG.editor_x_range, CONFIG.editor_y_range))
    pyautogui.click()
    time.sleep(RNG.uniform(0.2, 0.4))


_LINES_PER_SCREEN = 40


def read_scroll(mode: str, line_count: int | None = None, is_paused=lambda: False):
    """Read through the open file WITHOUT scrolling into the empty void past its end.

    Uses keyboard paging (PageDown/PageUp), which clamps at the last line — unlike the
    mouse wheel, which VS Code lets scroll a screen-plus into blank space. Short files
    that already fit on screen aren't scrolled at all; we just linger.

    Stops promptly if `is_paused()` flips True (a real person took over) rather than
    grinding through every remaining page while they're trying to use the machine.
    """
    if is_paused():
        return
    _click_editor()
    # start at the top so we read downward; Cmd+Up clamps at the file start.
    hotkey("command", "up")
    time.sleep(RNG.uniform(0.3, 0.7))

    # short file fully on screen -> don't page into emptiness, just read in place
    if line_count is not None and line_count <= _LINES_PER_SCREEN:
        for _ in range(RNG.randint(2, 4)):
            if is_paused():
                return
            mouse.micro_jitter()
            time.sleep(RNG.uniform(0.8, 2.0))
        return

    pages = max(1, (line_count or 160) // _LINES_PER_SCREEN)
    if mode == "skim":
        for _ in range(min(pages, RNG.randint(2, pages + 1))):
            if is_paused():
                return
            pyautogui.press("pagedown")            # clamps at last line — no void
            time.sleep(RNG.uniform(0.2, 0.6))
    else:  # slow reading
        for _ in range(min(pages + 1, RNG.randint(2, pages + 2))):
            if is_paused():
                return
            pyautogui.press("pagedown")
            time.sleep(RNG.uniform(0.9, 2.2))
            if RNG.random() < 0.2:                 # occasionally page back up to re-read
                pyautogui.press("pageup")
                time.sleep(RNG.uniform(0.6, 1.4))


_LINES_PER_NOTCH = 3   # ~how many editor lines one mouse-wheel notch scrolls (approx)


def _move_over_editor():
    """Move the mouse over the editor body (NO click) so the wheel scrolls the code pane."""
    mouse.move_bezier(pyautogui.position(),
                      mouse.editor_point(CONFIG.editor_x_range, CONFIG.editor_y_range))
    time.sleep(RNG.uniform(0.2, 0.5))


def _wheel(lines_down: int, step: int = 4):
    """Scroll the editor DOWN by ~lines_down lines using the mouse wheel, in quick steps.
    Pure wheel — no keyboard, so nothing can land in a focused popup."""
    notches = max(1, round(lines_down / _LINES_PER_NOTCH))
    done = 0
    while done < notches:
        n = min(step, notches - done)
        pyautogui.scroll(-n)                          # negative = scroll DOWN
        done += n
        time.sleep(RNG.uniform(0.1, 0.25))


def reading_scroll(times: int | None = None):
    """A short reading scroll during a file 'hold' — just move over the editor and wheel
    down a little. No keys, no clicks, so it can never open or navigate a popup."""
    if not is_vscode_frontmost():
        return
    _move_over_editor()
    times = times if times is not None else RNG.randint(2, 4)
    _wheel(lines_down=RNG.randint(8, 20) * (times // 2 or 1))


def count_lines(abs_path: str):
    """Line count of a file, or None if unreadable (read-only; used to size scrolling)."""
    try:
        with open(abs_path, "r", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return None


_MIN_SCROLL_LINES = 120   # always scroll at least this far past the imports


def scroll_into_file(abs_path=None, min_frac: float = 0.10, max_frac: float = 0.18):
    """Right after opening, scroll DOWN well past the imports — at least ~120 lines
    (more for long files). Dead simple: move the mouse over the editor and wheel down.
    NO Cmd keys, NO PageDown, NO clicks — so it can't open or navigate a popup."""
    if not is_vscode_frontmost():
        return
    line_count = count_lines(abs_path) if abs_path else None
    if line_count is not None and line_count <= _LINES_PER_SCREEN:
        return                                        # short file: all of it already on screen
    _move_over_editor()
    total = line_count or 400
    target = max(_MIN_SCROLL_LINES, round(RNG.uniform(min_frac, max_frac) * total))
    target = min(target, max(_MIN_SCROLL_LINES, total - _LINES_PER_SCREEN))  # not past end
    _wheel(lines_down=target)


def navigate(line_count: int | None = None, is_paused=lambda: False):
    if is_paused():
        return
    _click_editor()
    choice = RNG.choice(["goto_line", "find", "symbol", "switch_tab", "definition"])
    if choice == "goto_line":
        hotkey("command", "g")
        time.sleep(0.6)
        # a real line number within the file (clamped), typed EXACTLY (no typos in a
        # number field — that was the "mistake": stray letters in the go-to-line box)
        hi = line_count if (line_count and line_count > 1) else 200
        type_text(str(RNG.randint(1, hi)), typo_rate=0.0)
        time.sleep(0.3)
        pyautogui.press("enter")
    elif choice == "find":
        hotkey("command", "f")
        time.sleep(0.5)
        # exact search term — no typos in the find box
        type_text(RNG.choice(["const ", "return", "useEffect", "import ", "props"]),
                  typo_rate=0.0)
        time.sleep(0.4)
        for _ in range(RNG.randint(2, 5)):
            if is_paused():
                break
            pyautogui.press("enter")            # next match
            time.sleep(RNG.uniform(0.4, 1.0))
        pyautogui.press("escape")               # close the find widget
    elif choice == "symbol":
        hotkey("command", "shift", "o")
        time.sleep(0.6)
        for _ in range(RNG.randint(0, 5)):
            pyautogui.press("down")
            time.sleep(RNG.uniform(0.15, 0.4))
        pyautogui.press("enter")
    elif choice == "switch_tab":
        if RNG.random() < 0.5:
            hotkey("control", "tab")
        else:
            hotkey("control", "shift", "tab")
    elif choice == "definition":
        # land the cursor on a real identifier first — a bare F12 on whitespace just
        # shows "No definition found". Double-click selects the word under the cursor.
        pyautogui.doubleClick()
        time.sleep(RNG.uniform(0.2, 0.5))
        pyautogui.press("f12")
        time.sleep(RNG.uniform(0.6, 1.2))
