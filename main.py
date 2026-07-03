# main.py
"""blackpearl — macOS. READ THE SPEC before changing behavior:
docs/superpowers/specs/2026-07-01-blackpearl-design.md

Read-only w.r.t. source: no file editing, no TypeScript-breaking, no Claude commands/
prompts — only reading, scrolling, navigating, and running real (non-code-modifying)
dev commands (builds, installs, git pull). Never commits/pushes.
Stop: PAUSE via `touch /tmp/blackpearl_pause` (resume: rm it), Ctrl+C, or slam a screen corner.
"""
import os
import subprocess
import time
from datetime import datetime

import pyautogui

from config import CONFIG, is_active_now
from core.dwell import dwell
from core.exploration import build_project_map, ExplorationState
from core import mouse
from core.cursor import CursorKeeper
from core.pacing import paced_sleep
from core.platform_mac import PauseController
from core.rhythm import IntervalTimer
from core.rng import RNG
from actions import vscode, apps, terminal

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


def _line_count(path: str):
    """Number of lines in a file, or None if unreadable (used to avoid over-scrolling)."""
    try:
        with open(path, "r", errors="ignore") as f:
            return sum(1 for _ in f)
    except OSError:
        return None


def _metro_running() -> bool:
    """True if something is already listening on Metro's port 8081."""
    res = subprocess.run(
        ["lsof", "-iTCP:8081", "-sTCP:LISTEN", "-n", "-P"],
        capture_output=True, text=True, check=False,
    )
    return res.returncode == 0 and bool(res.stdout.strip())


def _stop_metro():
    """Kill whatever is listening on Metro's port 8081 (used on shutdown if we started it)."""
    pids = subprocess.run(
        ["lsof", "-tiTCP:8081", "-sTCP:LISTEN"],
        capture_output=True, text=True, check=False,
    ).stdout.split()
    for pid in pids:
        subprocess.run(["kill", pid], check=False)


def _ios_build_sequence(cfg):
    terminal.open_new_terminal()
    terminal.run_in_terminal(f'cd "{cfg.project_path}"')
    terminal.run_sequence(["cd ios", "pod install", "cd .."])
    terminal.run_in_terminal(f'pnpm ios:device "{cfg.ios_device}"')


def _npm_install(cfg, is_paused=lambda: False):
    terminal.open_new_terminal()
    terminal.run_in_terminal(f'cd "{cfg.project_path}"')
    terminal.run_in_terminal("npm i")          # accepted risk (pnpm repo)
    # a human would notice failure and retry with -f; blackpearl always follows up —
    # but a real user taking over cuts the wait short rather than grinding through it.
    if paced_sleep(RNG.uniform(20, 60), is_paused):
        terminal.run_in_terminal("npm i -f")


def main():
    cfg = CONFIG
    # Must happen before ANY pyautogui call: wraps input-posting functions so
    # PauseController can tell "the harness just acted" apart from "a human just acted".
    from core.injected import install as install_input_tracking
    install_input_tracking()

    import shutil
    if not shutil.which("code"):
        raise SystemExit("VS Code 'code' CLI not found. Run 'Shell Command: Install code command in PATH'.")
    if not os.path.isdir(os.path.join(cfg.project_path, ".git")):
        raise SystemExit(f"Project not a git repo: {cfg.project_path}")

    # Make `pkill`/SIGTERM run the same clean shutdown as Ctrl+C (SIGINT) — otherwise
    # SIGTERM kills the process WITHOUT reverting, leaving blackpearl edits in the working
    # tree that the next run would stage as its baseline (i.e. not a fresh start).
    import signal

    def _terminate(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _terminate)

    # Realism, not concealment: a real developer's terminal doesn't scroll with
    # "· read file X" / "· CLAUDE browse" debug lines — that output is itself a
    # tell if the terminal is ever visible on screen. So routine status/activity
    # output is off by default; BLACKPEARL_DEBUG=1 turns it on for local debugging.
    # (This has no bearing on screen/input-based detection — a monitor doesn't read
    # this process's stdout — it's purely about not looking obviously scripted.)
    debug = os.environ.get("BLACKPEARL_DEBUG") == "1"

    def dprint(msg):
        if debug:
            print(msg)

    ignore_hours = os.environ.get("BLACKPEARL_IGNORE_HOURS") == "1"
    # BLACKPEARL_TEST=1: fast, file-open-heavy profile for watching it work quickly.
    # It ONLY overrides cadence — the realistic default profile is unchanged.
    from dataclasses import replace
    if os.environ.get("BLACKPEARL_TEST") == "1":
        # ONLY difference from a normal run is SPEED — every feature/behavior
        # (auto-pause, Claude, weights, safety) is identical to normal.
        cfg = replace(
            cfg,
            action_gap=(3.0, 8.0),          # ~seconds between actions
            state_dwell=(15.0, 30.0),       # short holds
            micro_activity_gap=(5.0, 10.0),  # frequent jitter
            jira_slack_interval=(40.0, 90.0),  # see the Jira->Slack cycle quickly
        )
        dprint("BLACKPEARL_TEST=1 → FAST profile (short gaps only; all other behavior same as normal).")
    if debug:
        cfg = replace(cfg, debug_log=True)
        dprint("BLACKPEARL_DEBUG=1 → logging each action.")
    if ignore_hours:
        dprint("BLACKPEARL_IGNORE_HOURS=1 → work-hours/day gate bypassed.")
    src_root = os.path.join(cfg.project_path, "src")

    def _pause_error(exc):
        # A dead poll thread freezes `paused` forever — exactly what "auto-pause
        # stopped working" looks like from the outside. Surfaced only in debug mode.
        dprint(f"  ! auto-pause check failed, retrying: {exc!r}")

    pause = PauseController(auto_pause=cfg.enable_auto_pause,
                           resume_after=cfg.resume_after_idle,
                           on_error=_pause_error)
    pause.start()
    dprint(f"Auto-pause ON: backs off when you use the machine, resumes after "
           f"{int(cfg.resume_after_idle)}s of no real input.")
    # Background cursor nudger — keeps the cursor moving every ~20s even during long
    # sleeps; skips while paused (real user active) so it never fights you.
    cursor = None
    if cfg.enable_cursor_keeper:
        cursor = CursorKeeper(move_fn=mouse.micro_jitter,
                              is_paused=lambda: pause.paused,
                              interval=cfg.cursor_move_interval,
                              on_error=lambda exc: dprint(f"  ! cursor nudge failed: {exc!r}"))
        cursor.start()
    dprint("Claude browsing is ON — screenshots show your real chat history "
           "(visual-only: scrolling and switching chats, never typing/sending anything).")

    pmap = build_project_map(src_root)
    explore = ExplorationState(pmap)

    vscode.open_project(cfg.project_path)
    # Start Metro only if it isn't already running (port 8081). If the project's
    # VS Code + Metro are already up, reuse them instead of spawning a duplicate.
    metro_started = False
    if not _metro_running():
        terminal.open_new_terminal()
        terminal.run_in_terminal(f'cd "{cfg.project_path}" && pnpm start')
        metro_started = True

    build_timer = IntervalTimer(cfg.build_interval)
    install_timer = IntervalTimer(cfg.install_interval)
    backend_timer = IntervalTimer(cfg.backend_pull_interval)
    apps_timer = IntervalTimer(cfg.jira_slack_interval)  # timed Jira/Slack cycle
    next_app = "jira"                                    # first excursion is Jira

    idle_announced = False
    was_paused = False
    files_since_claude = 0
    from core.platform_mac import is_frontmost

    def _iteration():
        """One loop step. Returns early (like the old `continue`) after any action.
        Runs under a per-iteration guard so one failing action never stops the blackpearl."""
        nonlocal was_paused, idle_announced, files_since_claude, next_app

        if pause.paused:
            was_paused = True
            time.sleep(2.0)
            return
        if cfg.enable_work_hours and not ignore_hours and not is_active_now(cfg, datetime.now()):
            if not idle_announced:
                dprint(f"Idle: outside work hours ({cfg.work_start}-{cfg.work_end}, "
                       f"weekdays {cfg.work_days}). Nothing will run until then. "
                       f"Run with BLACKPEARL_IGNORE_HOURS=1 to test now.")
                idle_announced = True
            time.sleep(60.0)
            return
        idle_announced = False

        # resuming after a pause: re-assert the project's VS Code window before acting.
        if was_paused:
            vscode.open_project(cfg.project_path)
            was_paused = False

        def log(msg):
            if cfg.debug_log:
                print(f"  · {msg}")

        is_paused = lambda: pause.paused
        state_dwell = lambda: dwell(RNG.uniform(*cfg.state_dwell),
                                    mouse.micro_jitter,
                                    gap_range=cfg.micro_activity_gap,
                                    is_paused=is_paused)

        time.sleep(RNG.uniform(*cfg.action_gap))

        # hourly-ish heavy actions
        if build_timer.due():
            log("ios build")
            _ios_build_sequence(cfg)
            build_timer.reset()
            return
        if cfg.enable_npm_install and install_timer.due():
            log("npm install")
            _npm_install(cfg, is_paused=is_paused)
            install_timer.reset()
            return
        if cfg.enable_backend_pull and backend_timer.due():
            log("backend pull")
            apps.backend_pull(cfg, is_paused=is_paused)
            backend_timer.reset()
            return

        # timed Jira/Slack cycle: alternate Jira/Slack forever; files+Claude fill between.
        if apps_timer.due():
            if next_app == "jira" and cfg.enable_jira:
                log("jira board (timed)")
                apps.jira_board(cfg)
                state_dwell()
                next_app = "slack"
            elif next_app == "slack" and cfg.enable_slack:
                log("slack (timed)")
                apps.open_slack(cfg)
                state_dwell()
                next_app = "jira"
            else:
                next_app = "slack" if next_app == "jira" else "jira"  # disabled → flip
            apps_timer.reset()
            return

        # default: mostly files + Claude, with light in-editor navigation.
        roll = RNG.random()
        if cfg.enable_claude_extension and files_since_claude >= cfg.files_per_claude:
            log(f"CLAUDE browse (after {files_since_claude} file steps)")
            apps.claude_extension_browse(cfg)
            files_since_claude = 0
            state_dwell()
        elif roll < cfg.read_file_prob:                     # ~40%: open + read a file
            target = explore.next_file()
            if target:
                log(f"read file {os.path.relpath(target, cfg.project_path)}")
                vscode.open_file(os.path.relpath(target, cfg.project_path))
                explore.mark_read(target)
                vscode.read_scroll(RNG.choice(["slow", "slow", "skim"]),
                                   line_count=_line_count(target))
                files_since_claude += 1
                state_dwell()
            else:
                log("read file (none left to explore)")
        elif roll < cfg.read_file_prob + cfg.claude_prob and cfg.enable_claude_extension:
            log("CLAUDE browse")
            apps.claude_extension_browse(cfg)  # ~40%: Claude chat (visual-only)
            files_since_claude = 0
            state_dwell()
        elif roll < 0.98:
            log("navigate")
            vscode.navigate()
            state_dwell()
        else:
            log("scroll")
            vscode.read_scroll("slow")
            state_dwell()

        # foreground watcher: if focus drifted off VS Code, come back
        if not is_frontmost("Code") and not is_frontmost("Visual Studio Code"):
            vscode._focus()

    try:
        while True:
            # Per-iteration guard: a single action blowing up must NOT stop the blackpearl.
            # It runs continuously until you manually stop it (Ctrl+C / pkill / corner-slam).
            try:
                _iteration()
            except KeyboardInterrupt:
                raise                       # manual stop -> clean shutdown below
            except Exception as e:
                dprint(f"  ! recovered from error, continuing: {e!r}")
                time.sleep(1.0)
    except KeyboardInterrupt:
        dprint("\nStopping...")
    finally:
        # Shield cleanup from a SECOND Ctrl+C or pkill: ignore SIGINT/SIGTERM while it runs.
        _pi = signal.signal(signal.SIGINT, signal.SIG_IGN)
        _pt = signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            pause.stop()
            if cursor is not None:
                cursor.stop()
            if metro_started and cfg.stop_metro_on_exit:
                _stop_metro()               # stop the Metro WE started (leaves yours alone)
            dprint("Done. No file edits were made (editing is disabled) — nothing to revert.")
        finally:
            signal.signal(signal.SIGINT, _pi)
            signal.signal(signal.SIGTERM, _pt)


if __name__ == "__main__":
    # Catch Ctrl+C that lands during startup (before the loop's own try/except),
    # so early aborts exit quietly instead of dumping a traceback. Nothing is staged
    # or edited yet at that point, so there's nothing to revert here.
    try:
        main()
    except KeyboardInterrupt:
        if os.environ.get("BLACKPEARL_DEBUG") == "1":
            print("\nStopped during startup (nothing was changed).")
