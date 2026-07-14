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
    """Open a file via the `code` CLI, positioned at the TOP (line 1).

    Uses the CLI — NOT keyboard automation — so it can NEVER type into the editor, paste
    into the wrong box, or open the wrong file (the exact bugs that plagued the Cmd+P +
    paste approach). `--goto <file>:1` also guarantees the view is at the top even if the
    file was previously open at the bottom. Validated at every step:
      - the file must exist on disk,
      - VS Code must be confirmed frontmost after opening (nudged + retried once).
    Returns True only once the file is open and VS Code is frontmost; False otherwise."""
    abs_path = os.path.join(CONFIG.project_path, rel_path)
    if not os.path.isfile(abs_path):
        return False
    subprocess.run(["code", "--reuse-window", "--goto", f"{abs_path}:1"], check=False)
    if not wait_until_frontmost(is_vscode_frontmost, timeout=5.0):
        activate_app(_VSCODE)                          # nudge focus, then retry once
        if not wait_until_frontmost(is_vscode_frontmost, timeout=3.0):
            return False
    time.sleep(RNG.uniform(0.5, 0.9))                  # let it render the file at the top
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


def _wheel(lines: int, up: bool = False, step: int = 4):
    """Wheel-scroll ~`lines` editor lines (DOWN by default, UP if up=True), in quick small
    steps. Pure wheel — no keyboard, so nothing can land in a focused popup."""
    notches = max(1, round(lines / _LINES_PER_NOTCH))
    done = 0
    while done < notches:
        n = min(step, notches - done)
        pyautogui.scroll(n if up else -n)             # + = UP, - = DOWN
        done += n
        time.sleep(RNG.uniform(0.1, 0.25))


def count_lines(abs_path: str):
    """Line count of a file, or None if unreadable (read-only; used to size scrolling)."""
    try:
        with open(abs_path, "r", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return None


_MIN_SCROLL_LINES = 120   # aim to scroll ~this far past the imports (long files only)


def _max_scroll(total_lines: int) -> int:
    """The furthest we can scroll DOWN before the view runs past the last line into blank
    space. Scrolling beyond this shows the empty void below the file — so we never do."""
    return max(0, total_lines - _LINES_PER_SCREEN)


def _scroll_down_past_imports(abs_path) -> int:
    """From the top, wheel DOWN past the imports — ~120 lines on long files, but NEVER past
    the file's content (a 100/150-line file only scrolls as far as its last screen, no blank
    void). Returns the number of lines actually scrolled (the landing position)."""
    if not is_vscode_frontmost():
        return 0
    total = count_lines(abs_path) or 400
    cap = _max_scroll(total)
    if cap <= 0:                                       # whole file fits on screen — don't scroll
        return 0
    _move_over_editor()
    desired = max(_MIN_SCROLL_LINES, round(RNG.uniform(0.10, 0.18) * total))
    target = min(desired, cap)                         # clamp to content — no void
    _wheel(target)
    return target


class FileReader:
    """Reads a held file by wheeling up/down like a person, staying WITHIN the file's
    content — it never marches down into the blank void past the last line. Tracks an
    approximate position and prefers scrolling back up as it nears the bottom."""

    def __init__(self, abs_path, start_pos: int = 0):
        total = count_lines(abs_path) or 400
        self.cap = _max_scroll(total)
        self.pos = max(0, min(start_pos, self.cap))

    def reset(self, start_pos: int = 0):
        self.pos = max(0, min(start_pos, self.cap))

    def step(self):
        """One reading scroll — small, bounded, up or down. No keys, no clicks."""
        if not is_vscode_frontmost() or self.cap <= 0:
            return
        _move_over_editor()
        near_bottom = self.pos >= self.cap - 5
        near_top = self.pos <= 5
        go_up = near_bottom or (not near_top and RNG.random() < 0.35)
        if go_up:
            d = min(RNG.randint(6, 16), self.pos)
            if d:
                _wheel(d, up=True)
                self.pos -= d
        else:
            d = min(RNG.randint(6, 16), self.cap - self.pos)
            if d:
                _wheel(d)
                self.pos += d


def open_and_read(rel_path: str) -> int:
    """The full, ordered per-file flow the schedule uses:

      1. open the file via the `code` CLI at line 1 (TOP) — no keyboard, can't edit
      2. VS Code confirmed frontmost + file rendered (validated inside open_file)
      3. scroll DOWN past the imports, bounded to the file's content (no blank void)

    Returns the landing scroll position (lines from top), or -1 if the file didn't open."""
    if not open_file(rel_path):                       # 1+2) open at top, focus validated
        return -1
    return _scroll_down_past_imports(os.path.join(CONFIG.project_path, rel_path))  # 3)


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
