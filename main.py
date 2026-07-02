# main.py
"""activity harness — macOS. READ THE SPEC before changing behavior:
docs/superpowers/specs/2026-07-01-activity-harness-design.md

Transient only: every edit is reverted; never commits/pushes; leaves the repo as found.
Stop: PAUSE via `touch /tmp/harness_pause` (resume: rm it), Ctrl+C, or slam a screen corner.
"""
import os
import subprocess
import time
from datetime import datetime

import pyautogui

from config import CONFIG, is_active_now
from core.dwell import dwell
from core.exploration import build_project_map, ExplorationState
from core.gitsafe import GitSafe
from core import mouse
from core.platform_mac import PauseController
from core.rhythm import IntervalTimer, EditGate
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


def _npm_install(cfg):
    terminal.open_new_terminal()
    terminal.run_in_terminal(f'cd "{cfg.project_path}"')
    terminal.run_in_terminal("npm i")          # accepted risk (pnpm repo)
    # a human would notice failure and retry with -f; harness always follows up
    time.sleep(RNG.uniform(20, 60))
    terminal.run_in_terminal("npm i -f")


def main():
    cfg = CONFIG
    import shutil
    if not shutil.which("code"):
        raise SystemExit("VS Code 'code' CLI not found. Run 'Shell Command: Install code command in PATH'.")
    if not os.path.isdir(os.path.join(cfg.project_path, ".git")):
        raise SystemExit(f"Project not a git repo: {cfg.project_path}")

    # Make `pkill`/SIGTERM run the same clean shutdown as Ctrl+C (SIGINT) — otherwise
    # SIGTERM kills the process WITHOUT reverting, leaving harness edits in the working
    # tree that the next run would stage as its baseline (i.e. not a fresh start).
    import signal

    def _terminate(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _terminate)

    ignore_hours = os.environ.get("HARNESS_IGNORE_HOURS") == "1"
    # HARNESS_TEST=1: fast, file-open-heavy profile for watching it work quickly.
    # It ONLY overrides cadence — the realistic default profile is unchanged.
    # Implies work-hours bypass so you can test at any time.
    from dataclasses import replace
    if os.environ.get("HARNESS_TEST") == "1":
        # ONLY difference from a normal run is SPEED — every feature/behavior
        # (auto-pause, Claude, weights, safety) is identical to normal.
        cfg = replace(
            cfg,
            action_gap=(3.0, 8.0),          # ~seconds between actions
            state_dwell=(15.0, 30.0),       # short holds
            micro_activity_gap=(5.0, 10.0),  # frequent jitter
            edit_min_gap=45.0,              # edits/typing come around sooner
            jira_slack_interval=(40.0, 90.0),  # see the Jira->Slack cycle quickly
        )
        print("HARNESS_TEST=1 → FAST profile (short gaps only; all other behavior same as normal).")
    if os.environ.get("HARNESS_DEBUG") == "1":
        cfg = replace(cfg, debug_log=True)
        print("HARNESS_DEBUG=1 → logging each action.")
    if ignore_hours:
        print("HARNESS_IGNORE_HOURS=1 → work-hours/day gate bypassed.")
    src_root = os.path.join(cfg.project_path, "src")
    gitsafe = GitSafe(cfg.project_path)
    pause = PauseController(auto_pause=cfg.enable_auto_pause,
                           resume_after=cfg.resume_after_idle)
    pause.start()
    if cfg.enable_auto_pause:
        print(f"Auto-pause ON: backs off when you use the machine, resumes after "
              f"{int(cfg.resume_after_idle)}s of no real input.")
    if cfg.enable_claude_extension:
        print("WARNING: Claude browsing is ON — screenshots show your real chat history.")
        if cfg.enable_claude_prompt:
            print("WARNING: Claude PROMPT-SENDING is ON — it types + sends real messages; "
                  "with auto-edit on, Claude may modify your code. Turn off auto-edit, or "
                  "set enable_claude_prompt=False in config.py.")

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
    edit_gate = EditGate(cfg)

    idle_announced = False
    was_paused = False
    staged_baseline = False
    files_since_claude = 0
    from core.platform_mac import is_frontmost

    def _iteration():
        """One loop step. Returns early (like the old `continue`) after any action.
        Runs under a per-iteration guard so one failing action never stops the harness."""
        nonlocal was_paused, idle_announced, staged_baseline, files_since_claude, next_app

        if pause.paused:
            was_paused = True
            time.sleep(2.0)
            return
        if cfg.enable_work_hours and not ignore_hours and not is_active_now(cfg, datetime.now()):
            if not idle_announced:
                print(f"Idle: outside work hours ({cfg.work_start}-{cfg.work_end}, "
                      f"weekdays {cfg.work_days}). Nothing will run until then. "
                      f"Run with HARNESS_IGNORE_HOURS=1 to test now.")
                idle_announced = True
            time.sleep(60.0)
            return
        idle_announced = False

        # First active iteration: stage current changes as the baseline (git add -A).
        if not staged_baseline:
            gitsafe.stage_all()
            staged_baseline = True
            print("Staged current changes as baseline (git add -A). Your work is in "
                  "the index; harness edits revert to it. Never commits/pushes.")

        # resuming after a pause: re-assert the project's VS Code window before acting.
        if was_paused:
            vscode.open_project(cfg.project_path)
            was_paused = False

        def log(msg):
            if cfg.debug_log:
                print(f"  · {msg}")

        state_dwell = lambda: dwell(RNG.uniform(*cfg.state_dwell),
                                    mouse.micro_jitter,
                                    gap_range=cfg.micro_activity_gap,
                                    is_paused=lambda: pause.paused)

        time.sleep(RNG.uniform(*cfg.action_gap))

        # hourly-ish heavy actions
        if build_timer.due():
            log("ios build")
            _ios_build_sequence(cfg)
            build_timer.reset()
            return
        if cfg.enable_npm_install and install_timer.due():
            log("npm install")
            _npm_install(cfg)
            install_timer.reset()
            return
        if cfg.enable_backend_pull and backend_timer.due():
            log("backend pull")
            apps.backend_pull(cfg)
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

        # editing (transient), gated by min-gap + sampled interval
        if cfg.enable_editing and edit_gate.due():
            target = explore.next_file() or RNG.choice(pmap.all_files)
            if RNG.random() < cfg.break_fix_probability:
                log(f"break/fix {os.path.relpath(target, cfg.project_path)}")
                vscode.break_and_fix(gitsafe, target, cfg.project_path)
            else:
                log(f"edit/revert {os.path.relpath(target, cfg.project_path)}")
                vscode.edit_and_revert(gitsafe, target, cfg.project_path)
            edit_gate.fired()
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
            apps.claude_extension_browse(cfg)               # ~40%: browse Claude chat
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
            # Per-iteration guard: a single action blowing up must NOT stop the harness.
            # It runs continuously until you manually stop it (Ctrl+C / pkill / corner-slam).
            try:
                _iteration()
            except KeyboardInterrupt:
                raise                       # manual stop -> clean shutdown below
            except Exception as e:
                print(f"  ! recovered from error, continuing: {e!r}")
                time.sleep(1.0)
    except KeyboardInterrupt:
        print("\nStopping — reverting harness edits...")
    finally:
        # Shield cleanup from a SECOND Ctrl+C or pkill: ignore SIGINT/SIGTERM while the
        # git revert runs, so it completes atomically and always leaves the tree clean.
        _pi = signal.signal(signal.SIGINT, signal.SIG_IGN)
        _pt = signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            gitsafe.revert_all_touched()   # harness edits -> back to your staged baseline
            pause.stop()
            if metro_started and cfg.stop_metro_on_exit:
                _stop_metro()               # stop the Metro WE started (leaves yours alone)
            print("Done. Harness edits reverted to your staged baseline "
                  "(your work is staged; `git checkout .` drops anything left over).")
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
        print("\nStopped during startup (nothing was changed).")
