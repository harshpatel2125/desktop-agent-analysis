from dataclasses import dataclass
from datetime import datetime, time


@dataclass(frozen=True)
class Config:
    # paths
    project_path: str = "/Users/harsh/Documents/projects/warpspeed/warp-speed-ai-app"
    module_files_md: str = "config/module-files.md"   # source of truth for module→files
    links_json: str = "config/links.json"             # Jira/Slack link pools

    # schedule — OFF by default: this is a test blackpearl, so it runs any time/day.
    # (Flip enable_work_hours=True to restrict to the window below.)
    enable_work_hours: bool = False
    work_days: tuple[int, ...] = (0, 1, 2, 3, 4)  # Mon..Fri (Monday=0)
    work_start: time = time(9, 30)
    work_end: time = time(18, 30)

    # ---- the activity schedule (seconds) ----
    # One cycle = a VS Code work window + a short Jira/Slack excursion.
    vscode_window_secs: float = 20 * 60           # time spent in VS Code per cycle
    excursion_secs: float = 6 * 60                # time a Jira/Slack window stays open
    module_period_secs: float = 90 * 60           # switch feature/module every 1.5 h
    # A files-window opens 2 files: one short hold, one long hold (order randomized).
    file_hold_short_secs: float = 6 * 60
    file_hold_long_secs: float = 14 * 60
    # In a Claude window, switch to another chat after this much active time.
    claude_switch_after_secs: float = 6 * 60
    # During a file hold, do a small reading scroll every N active-seconds (< 60).
    reading_step_gap: tuple[float, float] = (30.0, 50.0)
    # Of the files opened, roughly this fraction are Components (rest Screens).
    component_prob: float = 0.30

    # feature flags
    enable_claude_extension: bool = True   # ⚠️ shows real chat history on screen (visual-only)
    enable_jira: bool = True
    enable_slack: bool = True
    debug_log: bool = False

    # Claude panel targeting (docked right). Aim at the MIDDLE of the transcript —
    # not the top switcher (which changes chats) or the bottom input box.
    claude_panel_x_frac: float = 0.85
    claude_scroll_y_range: tuple[float, float] = (0.45, 0.65)
    claude_scroll_amount: tuple[int, int] = (4, 10)  # wheel notches per step
    # switching between past Claude conversations: where the history/clock button sits.
    claude_switch_chat_prob: float = 0.5
    claude_history_btn_frac: tuple[float, float] = (0.965, 0.08)

    # editor click/scroll target area (screen fractions) — kept clear of the
    # right-docked Claude panel, the bottom-docked terminal, AND the top tab +
    # breadcrumb bar. Also the target zone for the cursor's periodic major moves.
    editor_x_range: tuple[float, float] = (0.25, 0.64)
    editor_y_range: tuple[float, float] = (0.24, 0.60)

    # background cursor nudger: makes a MAJOR cursor move at least this often, so the
    # cursor visibly moves ~every 30s even during long reading holds and excursions.
    enable_cursor_keeper: bool = True
    cursor_move_interval: tuple[float, float] = (24.0, 30.0)  # move at least every 30s

    # auto-pause when a real person uses the machine; resume after this many seconds
    # of no genuine (hardware) input. (See core/human_input.py: a CGEventTap records
    # only input NOT posted by this process, so the harness's own synthetic input is
    # never mistaken for a real person's — requires Input Monitoring permission.)
    enable_auto_pause: bool = True
    resume_after_idle: float = 120.0  # 2 minutes

    # keys
    pause_hotkey: tuple[str, ...] = ("ctrl", "alt", "p")


def is_active_now(cfg: Config, now: datetime) -> bool:
    if now.weekday() not in cfg.work_days:
        return False
    t = now.time()
    return cfg.work_start <= t < cfg.work_end


CONFIG = Config()
