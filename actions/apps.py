import subprocess
import time

import pyautogui

from core import mouse
from core.platform_mac import (activate_app, frontmost_app, is_chrome_frontmost,
                               is_vscode_frontmost, wait_until_frontmost)
from core.rng import RNG
from core.slack_link import permalink_to_deeplink

_VSCODE = "Visual Studio Code"
_CHROME = "Google Chrome"
_SLACK = "Slack"


# ---------------------------------------------------------------- Claude panel
# The Claude panel is docked on the right (~30% of the window). These helpers are
# visual-only: they focus the transcript and scroll / switch chats — never type or send.

def claude_focus_panel(cfg) -> bool:
    """Bring VS Code forward and click the transcript so the wheel scrolls it. Confirms
    VS Code actually came to the front before clicking, so the click can't land in
    whatever app was previously frontmost."""
    activate_app(_VSCODE)
    if not wait_until_frontmost(is_vscode_frontmost, timeout=3.0):
        return False
    time.sleep(RNG.uniform(0.3, 0.6))
    w, h = pyautogui.size()
    x = int(w * cfg.claude_panel_x_frac)
    y = int(h * RNG.uniform(*cfg.claude_scroll_y_range))
    mouse.move_bezier(pyautogui.position(), (x, y))
    time.sleep(RNG.uniform(0.3, 0.6))
    pyautogui.click(x, y)                              # focus the webview
    time.sleep(RNG.uniform(0.3, 0.6))
    return True


def claude_scroll_step(cfg):
    """One reading scroll of the transcript — mostly up (older), sometimes back down.
    Skips if VS Code isn't frontmost so the wheel never scrolls another app."""
    if not is_vscode_frontmost():
        return
    lo, hi = cfg.claude_scroll_amount
    up = RNG.random() < 0.7
    amount = RNG.randint(lo, hi)
    pyautogui.scroll(amount if up else -amount)
    time.sleep(RNG.uniform(0.8, 1.8))


def claude_switch_chat(cfg):
    """Open the conversation-history button and pick a different recent chat.

    Clicks the history/clock button (top-right of the panel), then Down+Enter to select
    a different recent conversation (works when history is a keyboard-navigable list)."""
    if not is_vscode_frontmost():                      # confirm before clicking anything
        return
    w, h = pyautogui.size()
    bx = int(w * cfg.claude_history_btn_frac[0])
    by = int(h * cfg.claude_history_btn_frac[1])
    mouse.move_bezier(pyautogui.position(), (bx, by))
    time.sleep(RNG.uniform(0.3, 0.6))
    pyautogui.click(bx, by)                            # open conversation history
    time.sleep(RNG.uniform(0.9, 1.6))
    for _ in range(RNG.randint(1, 4)):                # move to a different recent chat
        pyautogui.press("down")
        time.sleep(RNG.uniform(0.25, 0.6))
    pyautogui.press("enter")                          # open it
    time.sleep(RNG.uniform(1.0, 1.8))


# ---------------------------------------------------------------- Jira (Chrome)

def jira_board(url: str, is_paused=lambda: False):
    """Open `url` in Chrome DIRECTLY via `open` — no keyboard (no Cmd+T / paste / Enter),
    no clipboard. `open -a` hands the URL to Chrome, which opens it in a new tab and comes
    to the front. View-only; no further actions — just open and let it load."""
    if not url or is_paused():
        return
    subprocess.run(["open", "-a", _CHROME, url], check=False)   # open the URL directly
    wait_until_frontmost(is_chrome_frontmost, timeout=5.0)      # confirm it fronted
    time.sleep(RNG.uniform(1.5, 3.0))                           # let the board load


# ---------------------------------------------------------------- Slack (app)

def _is_slack_frontmost() -> bool:
    return frontmost_app() == _SLACK


def open_slack_message(permalink: str, team_id: str, is_paused=lambda: False):
    """Open a Slack message in the DESKTOP app by converting the permalink to a
    `slack://` deep link (focuses the specific message). Falls back to just focusing
    Slack if the permalink can't be parsed. No actions after — just open."""
    if not permalink or is_paused():
        return
    deep = permalink_to_deeplink(permalink, team_id)
    if deep:
        subprocess.run(["open", deep], check=False)   # slack:// -> Slack app, that message
    else:
        subprocess.run(["open", "-a", _SLACK], check=False)  # fallback: focus the app
    wait_until_frontmost(_is_slack_frontmost, timeout=5.0)
    time.sleep(RNG.uniform(0.5, 1.0))
