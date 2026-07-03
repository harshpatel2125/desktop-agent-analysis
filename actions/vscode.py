# actions/vscode.py
import shutil
import subprocess
import time

import pyautogui

from config import CONFIG
from core import mouse
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


def open_file(rel_path: str):
    _focus()
    hotkey("command", "p")
    time.sleep(0.6)
    type_text(rel_path)
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(RNG.uniform(0.5, 1.0))


def _click_editor():
    _focus()
    mouse.move_bezier(pyautogui.position(),
                      mouse.editor_point(CONFIG.editor_x_range, CONFIG.editor_y_range))
    pyautogui.click()
    time.sleep(RNG.uniform(0.2, 0.4))


_LINES_PER_SCREEN = 40


def read_scroll(mode: str, line_count: int | None = None):
    """Read through the open file WITHOUT scrolling into the empty void past its end.

    Uses keyboard paging (PageDown/PageUp), which clamps at the last line — unlike the
    mouse wheel, which VS Code lets scroll a screen-plus into blank space. Short files
    that already fit on screen aren't scrolled at all; we just linger.
    """
    _click_editor()
    # start at the top so we read downward; Cmd+Up clamps at the file start.
    hotkey("command", "up")
    time.sleep(RNG.uniform(0.3, 0.7))

    # short file fully on screen -> don't page into emptiness, just read in place
    if line_count is not None and line_count <= _LINES_PER_SCREEN:
        for _ in range(RNG.randint(2, 4)):
            mouse.micro_jitter()
            time.sleep(RNG.uniform(0.8, 2.0))
        return

    pages = max(1, (line_count or 160) // _LINES_PER_SCREEN)
    if mode == "skim":
        for _ in range(min(pages, RNG.randint(2, pages + 1))):
            pyautogui.press("pagedown")            # clamps at last line — no void
            time.sleep(RNG.uniform(0.2, 0.6))
    else:  # slow reading
        for _ in range(min(pages + 1, RNG.randint(2, pages + 2))):
            pyautogui.press("pagedown")
            time.sleep(RNG.uniform(0.9, 2.2))
            if RNG.random() < 0.2:                 # occasionally page back up to re-read
                pyautogui.press("pageup")
                time.sleep(RNG.uniform(0.6, 1.4))


def navigate(line_count: int | None = None):
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
