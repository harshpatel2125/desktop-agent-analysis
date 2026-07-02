import subprocess
import time

import pyautogui

from actions.terminal import open_new_terminal, run_in_terminal
from core import mouse
from core.keyboard_sim import type_text
from core.keys import hotkey
from core.platform_mac import activate_app
from core.rng import RNG

_VSCODE = "Visual Studio Code"
_CHROME = "Google Chrome"
_SLACK = "Slack"


def backend_pull(cfg):
    if not cfg.enable_backend_pull:
        return
    open_new_terminal()
    run_in_terminal(f'cd "{cfg.backend_repo_path}"')
    time.sleep(RNG.uniform(0.5, 1.2))
    run_in_terminal("git pull")             # best-effort; failure is fine
    # linger in the terminal >= 5 min
    lo, hi = cfg.backend_pull_linger
    time.sleep(RNG.uniform(lo, hi))
    # return focus to the editor pane
    activate_app(_VSCODE)
    hotkey("command", "1")


def _switch_claude_chat(cfg):
    """Open the conversation-history button and pick a different recent chat.

    Best-effort + tunable: clicks the history/clock button (top-right of the panel),
    then uses keyboard Down+Enter to select a different recent conversation — which
    works if the history opens as a keyboard-navigable list / quick-pick.
    """
    w, h = pyautogui.size()
    bx = int(w * cfg.claude_history_btn_frac[0])
    by = int(h * cfg.claude_history_btn_frac[1])
    mouse.move_bezier(pyautogui.position(), (bx, by))
    time.sleep(RNG.uniform(0.3, 0.6))
    pyautogui.click(bx, by)                          # open conversation history
    time.sleep(RNG.uniform(0.9, 1.6))
    for _ in range(RNG.randint(1, 4)):               # move to a different recent chat
        pyautogui.press("down")
        time.sleep(RNG.uniform(0.25, 0.6))
    pyautogui.press("enter")                          # open it
    time.sleep(RNG.uniform(1.0, 1.8))


_CLAUDE_PROMPTS = [
    "can you check this file looks okay?",
    "does this implementation look fine?",
    "any issues you can spot in the current file?",
    "is this all good?",
    "please review the current file",
    "anything you'd change here?",
    "looks correct to you?",
    "can you double-check this is fine?",
]


def _claude_scroll(cfg, up_steps: int, down_steps: int):
    """Focus the transcript and scroll it (up = older, down = recent)."""
    w, h = pyautogui.size()
    x = int(w * cfg.claude_panel_x_frac)
    y = int(h * RNG.uniform(*cfg.claude_scroll_y_range))
    mouse.move_bezier(pyautogui.position(), (x, y))
    time.sleep(RNG.uniform(0.3, 0.6))
    pyautogui.click(x, y)   # focus the webview so the wheel registers
    time.sleep(RNG.uniform(0.4, 0.8))
    lo, hi = cfg.claude_scroll_amount
    for _ in range(up_steps):
        pyautogui.scroll(RNG.randint(lo, hi))
        time.sleep(RNG.uniform(1.0, 2.2))
    for _ in range(down_steps):
        pyautogui.scroll(-RNG.randint(lo, hi))
        time.sleep(RNG.uniform(0.8, 1.6))


def _claude_send_prompt(cfg):
    """Type a general prompt into Claude's input box and SEND it.

    ⚠️ This triggers a real Claude response; with auto-edit on Claude may modify code.
    """
    if not cfg.enable_claude_prompt:
        return
    w, h = pyautogui.size()
    ix = int(w * cfg.claude_input_frac[0])
    iy = int(h * cfg.claude_input_frac[1])
    mouse.move_bezier(pyautogui.position(), (ix, iy))
    time.sleep(RNG.uniform(0.3, 0.6))
    pyautogui.click(ix, iy)   # focus the input box
    time.sleep(RNG.uniform(0.4, 0.8))
    type_text(RNG.choice(_CLAUDE_PROMPTS))
    time.sleep(RNG.uniform(0.4, 0.9))
    pyautogui.press("enter")  # send (user-chosen)
    time.sleep(RNG.uniform(1.0, 2.0))


def claude_extension_browse(cfg):
    """A realistic Claude session as a varied SEQUENCE: maybe switch chat, read
    (scroll), maybe send a prompt and wait, read some more, maybe switch again.

    NOTE: shows real chat content on screen and (if enable_claude_prompt) sends real
    messages. Keep the flags off if that's not acceptable.
    """
    if not cfg.enable_claude_extension:
        return
    activate_app(_VSCODE)
    time.sleep(RNG.uniform(0.4, 0.9))

    if RNG.random() < cfg.claude_switch_chat_prob:
        _switch_claude_chat(cfg)

    _claude_scroll(cfg, RNG.randint(2, 4), RNG.randint(1, 2))   # read

    if cfg.enable_claude_prompt and RNG.random() < cfg.claude_prompt_prob:
        _claude_send_prompt(cfg)                                 # ask something
        time.sleep(RNG.uniform(4.0, 10.0))                      # wait for a response
        _claude_scroll(cfg, RNG.randint(1, 2), RNG.randint(1, 2))  # read the reply

    if RNG.random() < 0.35:
        _switch_claude_chat(cfg)                                 # occasionally move on

    activate_app(_VSCODE)


def _set_clipboard(text: str):
    subprocess.run(["pbcopy"], input=text, text=True, check=False)


def _get_clipboard() -> str:
    return subprocess.run(["pbpaste"], capture_output=True, text=True, check=False).stdout


def jira_board(cfg):
    """Open a new Chrome tab on the assigned Jira board (view-only).

    Pastes the URL into the address bar (Cmd+V) instead of typing it char-by-char —
    faster and no keystroke-timing signature. Restores your clipboard afterward.
    """
    if not cfg.enable_jira:
        return
    subprocess.run(["open", "-a", _CHROME], check=False)  # launch or focus Chrome
    time.sleep(RNG.uniform(1.0, 2.0))
    prev_clip = _get_clipboard()                  # save the user's clipboard
    _set_clipboard(cfg.jira_url)
    hotkey("command", "t")                        # new tab (address bar focused)
    time.sleep(RNG.uniform(0.4, 0.8))
    hotkey("command", "v")                        # paste the URL — no manual typing
    time.sleep(RNG.uniform(0.2, 0.5))
    pyautogui.press("enter")
    time.sleep(RNG.uniform(1.5, 3.0))             # let the board load
    _set_clipboard(prev_clip)                     # restore the user's clipboard


def open_slack(cfg):
    """Bring Slack to the front (launch it if it isn't running)."""
    if not cfg.enable_slack:
        return
    subprocess.run(["open", "-a", _SLACK], check=False)    # focus if running, else launch
    time.sleep(RNG.uniform(2.0, 4.0))
    activate_app(_SLACK)
    time.sleep(RNG.uniform(0.5, 1.0))
