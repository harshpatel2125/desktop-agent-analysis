# main.py
"""blackpearl — macOS activity simulator (schedule-driven, read-only).

Structure (see docs/superpowers/specs/2026-07-10-blackpearl-schedule-redesign.md):
  * A repeating CYCLE = a 20-min VS Code work window + a 6-min Jira/Slack excursion.
  * VS Code windows alternate: FILES (open 2 files, 6+14 min holds, scrolling) and
    CLAUDE (open 1 file, then read/switch chats in the Claude panel).
  * The active FEATURE/MODULE switches every 90 min (random, or a --module: sequence).
  * Files come from config/module-files.md (Screens mostly, Components occasionally).
  * Jira/Slack links rotate from config/links.json with no repeat until exhausted.
  * The cursor makes a major move ~every 30s. Auto-pause backs off for a real user; the
    schedule clock freezes while paused and resumes where it left off.

Read-only: no file editing, no terminal commands, no builds/installs/git — only opening,
reading, scrolling, and viewing Jira/Slack/Claude. Never commits/pushes.
Stop: PAUSE via `touch /tmp/blackpearl_pause` (resume: rm it), Ctrl+C, or slam a corner.
"""
import os
import sys
import signal
import threading
import time
from dataclasses import replace
from datetime import datetime

import pyautogui

from config import CONFIG, is_active_now
from core import mouse
from core.cursor import CursorKeeper
from core.file_picker import FilePicker
from core.links_config import load_links
from core.module_map import build_module_map, rotation_keys
from core.platform_mac import PauseController
from core.rng import RNG
from core.rotation import Rotator
from core.schedule import ActiveClock, ModuleScheduler, parse_module_flag
from actions import apps, vscode

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


def main():
    cfg = CONFIG
    debug = os.environ.get("BLACKPEARL_DEBUG") == "1"

    def dprint(msg):
        if debug:
            print(msg)

    # BLACKPEARL_TEST=1: same behavior, just compressed timings so you can watch a full
    # cycle + module switch in minutes. Holds still sum to the window (short+long==window).
    if os.environ.get("BLACKPEARL_TEST") == "1":
        cfg = replace(cfg,
                      vscode_window_secs=60, excursion_secs=20, module_period_secs=4 * 60,
                      file_hold_short_secs=15, file_hold_long_secs=45,
                      claude_switch_after_secs=20, reading_step_gap=(5.0, 10.0),
                      cursor_move_interval=(8.0, 12.0))
        dprint("BLACKPEARL_TEST=1 → FAST profile (compressed timings; behavior identical).")
    if debug:
        cfg = replace(cfg, debug_log=True)
    ignore_hours = os.environ.get("BLACKPEARL_IGNORE_HOURS") == "1"

    def log(msg):
        if cfg.debug_log:
            print(f"  · {msg}")

    # preflight
    import shutil
    if not shutil.which("code"):
        raise SystemExit("VS Code 'code' CLI not found. Run 'Shell Command: Install code command in PATH'.")
    if not os.path.isdir(os.path.join(cfg.project_path, ".git")):
        raise SystemExit(f"Project not a git repo: {cfg.project_path}")

    # Make pkill/SIGTERM run the same clean shutdown as Ctrl+C.
    def _terminate(signum, frame):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, _terminate)

    # ---- module map + schedule ----
    module_map = build_module_map(cfg.module_files_md, cfg.project_path)
    keys = rotation_keys(module_map)
    if not keys:
        raise SystemExit(f"No modules with existing files found via {cfg.module_files_md}")
    sequence = parse_module_flag(sys.argv[1:], keys)
    scheduler = ModuleScheduler(keys, sequence=sequence, rng=RNG)
    picker = FilePicker(RNG, component_prob=cfg.component_prob)

    links = load_links(cfg.links_json)
    jira_rot = Rotator(links.jira_urls)
    slack_rot = Rotator(links.slack_links)

    if sequence:
        dprint(f"Module sequence {sequence}; switch every {int(cfg.module_period_secs/60)}m.")
    else:
        dprint(f"Module: random every {int(cfg.module_period_secs/60)}m. Available: {keys}")
    dprint(f"Jira links: {len(jira_rot)}  Slack links: {len(slack_rot)}")

    # Serialize main-thread actions vs. the background cursor keeper.
    input_lock = threading.Lock()
    _stop = {"v": False}

    # ---- pause + active clock + cursor ----
    pause = PauseController(auto_pause=cfg.enable_auto_pause,
                            resume_after=cfg.resume_after_idle,
                            on_error=lambda e: dprint(f"  ! pause check failed: {e!r}"))
    pause.start()
    if cfg.enable_auto_pause and not pause.monitor_active:
        print("WARNING: could not start input monitor (grant Input Monitoring to your "
              "terminal in System Settings > Privacy & Security). Auto-pause on human "
              "activity is DISABLED — use `touch /tmp/blackpearl_pause` to pause.")

    clock = ActiveClock(is_paused=lambda: pause.paused)
    clock.start()

    def cursor_move():
        mouse.move_bezier(pyautogui.position(),
                          mouse.editor_point(cfg.editor_x_range, cfg.editor_y_range))

    cursor = None
    if cfg.enable_cursor_keeper:
        cursor = CursorKeeper(move_fn=cursor_move, is_paused=lambda: pause.paused,
                              interval=cfg.cursor_move_interval, lock=input_lock,
                              on_error=lambda e: dprint(f"  ! cursor move failed: {e!r}"))
        cursor.start()

    is_paused = lambda: pause.paused

    vscode.open_project(cfg.project_path)

    # ---- primitives ----
    def act(fn):
        """Run a discrete GUI action: wait out any pause, then hold input_lock so the
        cursor keeper can't move the cursor mid-click/type/bezier."""
        while pause.paused and not _stop["v"]:
            time.sleep(0.5)
        with input_lock:
            fn()

    def active_hold(total, step=None, on_resume=None):
        """Hold for `total` ACTIVE seconds (does not advance while paused). Every
        ~reading_step_gap active-seconds run step() (under the lock). On a pause→resume
        transition, run on_resume() to re-assert focus."""
        start = clock.elapsed()
        next_step = start + RNG.uniform(*cfg.reading_step_gap)
        was_paused = False
        while clock.elapsed() - start < total and not _stop["v"]:
            if pause.paused:
                was_paused = True
                time.sleep(1.0)
                continue
            if was_paused:
                was_paused = False
                if on_resume:
                    try:
                        act(on_resume)
                    except Exception as e:
                        dprint(f"  ! resume re-assert failed: {e!r}")
                next_step = clock.elapsed() + RNG.uniform(*cfg.reading_step_gap)
            if step and clock.elapsed() >= next_step:
                try:
                    act(step)
                except Exception as e:
                    dprint(f"  ! hold step failed: {e!r}")
                next_step = clock.elapsed() + RNG.uniform(*cfg.reading_step_gap)
            time.sleep(0.5)

    # ---- windows ----
    def open_and_hold(path, hold_secs):
        rel = os.path.relpath(path, cfg.project_path)
        log(f"open {rel} (hold {int(hold_secs)}s)")

        def open_and_settle():
            if vscode.open_file(rel):                 # False if the file is missing
                vscode.scroll_into_file(path)         # scroll past the imports (~20-35%)

        act(open_and_settle)
        active_hold(hold_secs,
                    step=lambda: vscode.reading_scroll(),
                    on_resume=open_and_settle)

    def files_window(groups):
        long_first = RNG.random() < 0.5
        holds = ([cfg.file_hold_long_secs, cfg.file_hold_short_secs] if long_first
                 else [cfg.file_hold_short_secs, cfg.file_hold_long_secs])
        for hold in holds:
            if _stop["v"]:
                return
            path, _kind = picker.next(groups)
            if path is None:
                active_hold(hold)
            else:
                open_and_hold(path, hold)

    def claude_window(groups):
        path, _kind = picker.next(groups)          # open one file (keeps the count going)
        if path:
            rel = os.path.relpath(path, cfg.project_path)
            log(f"open {rel} (claude window)")
            act(lambda: vscode.open_file(rel))
        if not cfg.enable_claude_extension:
            active_hold(cfg.vscode_window_secs)     # Claude off → just read the window out
            return
        act(lambda: apps.claude_focus_panel(cfg))
        win_start = clock.elapsed()
        switched = {"v": False}

        def step():
            if (not switched["v"]
                    and clock.elapsed() - win_start >= cfg.claude_switch_after_secs):
                apps.claude_switch_chat(cfg)
                switched["v"] = True
            else:
                apps.claude_scroll_step(cfg)

        active_hold(cfg.vscode_window_secs, step=step,
                    on_resume=lambda: apps.claude_focus_panel(cfg))

    def excursion(kind) -> bool:
        """Open a Jira/Slack window and hold it ~6 min (no actions). True if it ran."""
        if kind == "jira":
            if not cfg.enable_jira:
                return False
            url = jira_rot.next()
            if not url:
                return False
            log("jira excursion")
            act(lambda: apps.jira_board(url, is_paused))
        else:
            if not cfg.enable_slack:
                return False
            link = slack_rot.next()
            if not link:
                return False
            log("slack excursion")
            act(lambda: apps.open_slack_message(link, links.slack_team_id, is_paused))
        active_hold(cfg.excursion_secs)             # just keep it open; cursor still moves
        act(lambda: vscode._focus())                # come back to VS Code
        return True

    # ---- the cycle ----
    state = {"window": 0, "excursion": 0, "module": None}

    def run_cycle():
        if cfg.enable_work_hours and not ignore_hours and not is_active_now(cfg, datetime.now()):
            time.sleep(60.0)
            return
        # If we're resuming from a takeover at a cycle boundary, re-assert the project.
        if pause.paused:
            while pause.paused and not _stop["v"]:
                time.sleep(0.5)
            if _stop["v"]:
                return
            act(lambda: vscode.open_project(cfg.project_path))

        module = scheduler.module_for_period(int(clock.elapsed() // cfg.module_period_secs))
        if module != state["module"]:
            state["module"] = module
            picker.start_module()
            log(f"MODULE → {module}")
        groups = module_map[module]

        if state["window"] % 2 == 0:
            log(f"window {state['window']} FILES [{module}]")
            files_window(groups)
        else:
            log(f"window {state['window']} CLAUDE [{module}]")
            claude_window(groups)
        state["window"] += 1

        for _ in range(2):                          # try one excursion; skip disabled/empty
            kind = "jira" if state["excursion"] % 2 == 0 else "slack"
            state["excursion"] += 1
            if excursion(kind):
                break

    try:
        while True:
            try:
                run_cycle()
            except KeyboardInterrupt:
                raise
            except Exception as e:
                dprint(f"  ! recovered from error, continuing: {e!r}")
                time.sleep(1.0)
    except KeyboardInterrupt:
        dprint("\nStopping...")
    finally:
        _stop["v"] = True
        _pi = signal.signal(signal.SIGINT, signal.SIG_IGN)
        _pt = signal.signal(signal.SIGTERM, signal.SIG_IGN)
        try:
            pause.stop()
            clock.stop()
            if cursor is not None:
                cursor.stop()
            dprint("Done. No file edits, no terminal commands — nothing to revert.")
        finally:
            signal.signal(signal.SIGINT, _pi)
            signal.signal(signal.SIGTERM, _pt)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if os.environ.get("BLACKPEARL_DEBUG") == "1":
            print("\nStopped during startup (nothing was changed).")
