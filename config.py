from dataclasses import dataclass
from datetime import datetime, time


@dataclass(frozen=True)
class Config:
    # paths
    project_path: str = "/Users/harsh/Documents/projects/warpspeed/warp-speed-ai-app"
    backend_repo_path: str = "/Users/harsh/Documents/projects/warpspeed/warp-speed-ai-backend"
    ios_device: str = "Harsh's iPhone 12 Pro"
    android_target: str = ""  # empty => default emulator

    # schedule
    work_days: tuple[int, ...] = (0, 1, 2, 3, 4)  # Mon..Fri (Monday=0)
    work_start: time = time(9, 30)
    work_end: time = time(18, 30)

    # cadence (seconds)
    action_gap: tuple[float, float] = (20.0, 45.0)
    build_interval: tuple[float, float] = (45 * 60, 75 * 60)      # ~1h jittered
    install_interval: tuple[float, float] = (45 * 60, 75 * 60)    # ~1h jittered
    backend_pull_interval: tuple[float, float] = (100 * 60, 140 * 60)  # ~2h jittered
    backend_pull_linger: tuple[float, float] = (5 * 60, 9 * 60)   # >=5 min
    # timed Jira/Slack cycle: first excursion ~this long after start, then alternate.
    jira_slack_interval: tuple[float, float] = (20 * 60, 25 * 60)  # ~20-25 min
    command_timeout: float = 20 * 60

    # edit cadence
    edit_min_gap: float = 5 * 60
    edit_interval_dist: tuple[tuple[float, float], ...] = (
        ((5 * 60, 8 * 60), 0.20),
        ((10 * 60, 25 * 60), 0.55),
        ((30 * 60, 60 * 60), 0.25),
    )
    edit_burst_size: tuple[int, int] = (1, 3)
    break_fix_probability: float = 0.30  # of edit fires, chance it's a break/fix instead

    # rhythm (seconds)
    focus_burst: tuple[float, float] = (10 * 60, 25 * 60)
    short_break: tuple[float, float] = (1 * 60, 3 * 60)

    # feature flags
    enable_npm_install: bool = True
    enable_android_build: bool = False
    enable_editing: bool = True
    enable_claude_extension: bool = True   # ⚠️ shows real chat history on screen
    enable_backend_pull: bool = True
    debug_log: bool = False

    # external apps
    jira_url: str = "https://flixpremiere.atlassian.net/jira/software/projects/WS/boards/9?jql=assignee%20%3D%20712020%3A99f52d86-aac3-4f8f-86b2-fed545449c48"
    enable_jira: bool = True
    enable_slack: bool = True

    # dwell / anti-idle (seconds)
    state_dwell: tuple[float, float] = (120.0, 480.0)      # >= 2 min per state
    micro_activity_gap: tuple[float, float] = (30.0, 50.0)  # act before 60s idle

    # default-loop action weights: ~40% files (open/read), ~40% browse Claude,
    # the remaining ~20% split across navigate / browser / Jira / Slack / scroll.
    read_file_prob: float = 0.40
    claude_prob: float = 0.40
    # Claude panel targeting (docked right). Aim at the MIDDLE of the transcript —
    # not the top switcher (which changes chats) or the bottom input box.
    # Tune these to your panel: x fraction of screen width, y band (fractions).
    claude_panel_x_frac: float = 0.85
    claude_scroll_y_range: tuple[float, float] = (0.45, 0.65)
    claude_scroll_amount: tuple[int, int] = (4, 10)  # wheel notches per step
    # switching between past Claude conversations: chance to do it, and where the
    # history/clock button sits (screen fractions, top-right of the Claude panel).
    claude_switch_chat_prob: float = 0.5
    claude_history_btn_frac: tuple[float, float] = (0.965, 0.08)
    # typing a prompt into the Claude input box and SENDING it. ⚠️ this triggers a
    # real Claude response and (with auto-edit on) may modify your code.
    enable_claude_prompt: bool = True
    claude_prompt_prob: float = 0.5             # chance a Claude visit sends a prompt
    claude_input_frac: tuple[float, float] = (0.85, 0.90)  # input box (bottom of panel)
    # after ~this many file steps, force a Claude step (interleave files and Claude)
    files_per_claude: int = 2

    # editor click/scroll target area (screen fractions) — kept clear of the
    # right-docked Claude panel, the bottom-docked terminal, AND the top tab +
    # breadcrumb bar (clicking the breadcrumb opens the symbol dropdown). Tune to layout.
    editor_x_range: tuple[float, float] = (0.25, 0.64)
    editor_y_range: tuple[float, float] = (0.24, 0.60)

    # on shutdown, stop Metro (port 8081) IF the harness started it (leaves a Metro
    # you were already running alone).
    stop_metro_on_exit: bool = True

    # auto-pause when a real person uses the machine; resume after this many seconds
    # of no genuine (hardware) input. The harness's own injected input doesn't count.
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
