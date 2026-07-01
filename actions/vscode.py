# actions/vscode.py
import os
import shutil
import subprocess
import time

import pyautogui

from config import CONFIG
from core import mouse
from core.keyboard_sim import type_text
from core.keys import hotkey
from core.platform_mac import activate_app
from core.rng import RNG

_VSCODE = "Visual Studio Code"


def _focus():
    activate_app(_VSCODE)
    time.sleep(RNG.uniform(0.4, 0.8))


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


def _revert_with_fallback(gitsafe, file_abs, repo_root, undo_presses):
    """Cmd+Z primary; git drift-check + checkout fallback. Always leaves file clean."""
    _focus()
    for _ in range(undo_presses):
        hotkey("command", "z")
        time.sleep(RNG.uniform(0.2, 0.5))
    hotkey("command", "s")  # save so git sees the reverted state
    time.sleep(0.5)
    rel = os.path.relpath(file_abs, repo_root)
    if not gitsafe.file_is_clean(rel):
        gitsafe.revert_file(rel)


def edit_and_revert(gitsafe, file_abs, repo_root):
    rel = os.path.relpath(file_abs, repo_root)
    gitsafe.note_touched(rel)
    open_file(rel)
    _click_editor()
    try:
        # jump somewhere and insert a harmless comment on its own line
        hotkey("command", "g")
        time.sleep(0.4)
        type_text(str(RNG.randint(5, 60)))
        pyautogui.press("enter")
        pyautogui.press("home")
        type_text("// note: reviewing this section\n")
        hotkey("command", "s")
        # persist the edit a few minutes, then revert
        time.sleep(RNG.uniform(60, 240))
    finally:
        # one comment line ~ a handful of undo units; fallback guarantees clean
        _revert_with_fallback(gitsafe, file_abs, repo_root, undo_presses=RNG.randint(3, 6))


def break_and_fix(gitsafe, file_abs, repo_root):
    rel = os.path.relpath(file_abs, repo_root)
    gitsafe.note_touched(rel)
    open_file(rel)
    _click_editor()
    try:
        hotkey("command", "g")
        time.sleep(0.4)
        type_text(str(RNG.randint(5, 60)))
        pyautogui.press("enter")
        pyautogui.press("home")
        # a line that reliably fails tsc but is self-contained
        type_text("const __tmp_bad: number = 'oops'\n")
        hotkey("command", "s")
        time.sleep(RNG.uniform(30, 120))  # "look at" the error
    finally:
        _revert_with_fallback(gitsafe, file_abs, repo_root, undo_presses=RNG.randint(3, 6))
