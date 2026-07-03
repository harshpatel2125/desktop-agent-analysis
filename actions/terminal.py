import time

import pyautogui

from core.keyboard_sim import type_text
from core.keys import hotkey
from core.platform_mac import activate_app, is_vscode_frontmost, wait_until_frontmost
from core.rng import RNG

_VSCODE = "Visual Studio Code"


class FocusLostError(RuntimeError):
    """VS Code never actually came to the foreground — do not type/click."""


def _focus_vscode():
    activate_app(_VSCODE)
    if not wait_until_frontmost(is_vscode_frontmost, timeout=3.0):
        raise FocusLostError("VS Code did not come to the foreground in time")
    time.sleep(RNG.uniform(0.2, 0.4))  # brief settle now that focus is CONFIRMED


def _run_palette_command(title: str):
    """Run a VS Code command by its exact title via the Command Palette.

    This is deterministic — unlike Ctrl+` (a TOGGLE), Cmd+Shift+P grabs focus from
    anywhere in the window (even the Source Control commit box), so a command can
    never leak into an editor/SCM field. The title is typed WITHOUT typo simulation
    so the palette's top match is exact.
    """
    _focus_vscode()
    hotkey("command", "shift", "p")
    time.sleep(RNG.uniform(0.5, 0.9))
    type_text(title, typo_rate=0.0)          # exact — no typos in a command name
    time.sleep(RNG.uniform(0.4, 0.7))
    pyautogui.press("enter")
    time.sleep(RNG.uniform(0.5, 0.9))


def open_new_terminal():
    _run_palette_command("Terminal: Create New Terminal")


def focus_terminal():
    _run_palette_command("Terminal: Focus on Terminal View")


def run_in_terminal(command: str):
    """Type a command into the focused terminal and press enter. Non-blocking."""
    focus_terminal()
    type_text(command)
    time.sleep(RNG.uniform(0.2, 0.6))
    pyautogui.press("enter")


def run_sequence(commands, gap=(0.5, 1.5)):
    focus_terminal()
    for cmd in commands:
        type_text(cmd)
        time.sleep(RNG.uniform(0.2, 0.6))
        pyautogui.press("enter")
        time.sleep(RNG.uniform(*gap))
