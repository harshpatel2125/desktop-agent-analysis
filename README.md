# Blackpearl (macOS)

A red-team **activity-simulation blackpearl** for testing **the monitoring agent** (an employee
presence/attendance monitor). It drives realistic, human-paced developer activity in
VS Code on a real React Native project so you can observe *which of the monitoring agent's presence
signals can be fooled by synthetic-but-human-looking behavior* — and therefore where
the monitoring agent's detection needs hardening.

It is **transient and non-destructive**: your work is staged as a baseline, every edit
the blackpearl makes is reverted, and it **never commits or pushes**.

> ⚠️ **Honest scope.** This simulates *human-looking* activity. It does **not** claim to
> be undetectable. In particular it uses `pyautogui` (software-injected input), which the
> OS flags as synthetic (`CGEventPost`) — a monitor that checks the input-source flag can
> still catch it. See [Detection vectors & limitations](#detection-vectors--limitations).

---

## Table of contents

- [What it does](#what-it-does)
- [How it works](#how-it-works)
- [Requirements](#requirements)
- [Setup](#setup)
- [Running it](#running-it)
- [Environment flags](#environment-flags)
- [Stop / pause / resume](#stop--pause--resume)
- [Testing](#testing)
- [Configuration](#configuration)
- [Safety model](#safety-model)
- [Claude interaction (read this)](#claude-interaction-read-this)
- [Tuning to your screen layout](#tuning-to-your-screen-layout)
- [Project structure](#project-structure)
- [Detection vectors & limitations](#detection-vectors--limitations)
- [Troubleshooting](#troubleshooting)

---

## What it does

While you're away, the blackpearl makes the machine look like an engineer actively working
on the `warp-speed-ai-app` Expo/React Native project:

- **Reads code** — opens real files, scrolls through them at human speeds (page-by-page,
  clamped at the file end so it never scrolls into empty space), lingers, re-reads.
- **Works in Claude** — scrolls the Claude Code chat transcript, switches between past
  conversations, and (optionally) types and sends a prompt, waits for the reply, reads it.
- **Navigates code** — Go to Line, Find, Go to Symbol, switch tabs, Go to Definition.
- **Edits transiently** — occasionally makes a small edit or introduces a TypeScript error,
  "looks" at it, then **reverts it** (never kept, never committed).
- **Runs real dev commands** — starts Metro, periodically runs a real iOS build
  (`pod install` → `pnpm ios:device`), random `npm i`, and pulls a sibling backend repo.
- **Cycles through Jira & Slack** on a timer (see [How it works](#how-it-works)).
- **Paces itself like a human** — jittered gaps, 2-minute+ dwells on each view with
  sub-minute micro-activity so it never crosses a ~60s idle threshold, active only during
  work hours, and it **auto-pauses the instant you touch the machine**.

---

## How it works

The main loop ([main.py](main.py)) runs one action per iteration, gated and weighted:

1. **Pause gate** — if a real user is active (or the pause sentinel exists), do nothing.
2. **Work-hours gate** — only act on `work_days` within `work_start`–`work_end`.
3. **Baseline** — on the first active iteration, `git add -A` stages your current work.
4. **Heavy actions** (each on its own jittered timer):
   - iOS build (~1 h): `cd ios` → `pod install` → `cd ..` → `pnpm ios:device "<device>"`
   - `npm i` (~1 h), then `npm i -f` on failure
   - backend `git pull` (~2 h), linger ≥5 min
   - **Jira/Slack cycle** (~20–25 min, alternating): first **Jira**, then **Slack**, then
     Jira, then Slack… Files + Claude fill the time in between.
5. **Edit** (gated, ≥5 min apart): transient edit-and-revert or break-and-fix-TypeScript.
6. **Default action** (the bulk of the time), weighted:
   | Action | ~Weight |
   |---|---|
   | Read a file | 40% |
   | Browse Claude | 40% |
   | Navigate (in-editor) | ~18% |
   | Scroll | ~2% |

   After 2 file steps in a row, the next step is forced to Claude (interleave).

Every view-establishing action is followed by a **dwell** (2–8 min) that keeps tiny
mouse/scroll activity going every 30–50 s so the screen never looks idle.

---

## Requirements

- **macOS** (uses `osascript`, `open -a`, `pyobjc` Quartz/AppKit; Windows not supported yet).
- **Python 3.13** (Homebrew `python@3.14` has a broken `pyexpat`/`plistlib` on some
  machines; the project pins `>=3.13`).
- **[uv](https://github.com/astral-sh/uv)** for env + running.
- **VS Code** with the `code` CLI on `PATH`
  (Command Palette → *Shell Command: Install 'code' command in PATH*).
- The target project must be a **git repo** (it is).
- **Accessibility permission** for the terminal app you launch it from
  (System Settings → Privacy & Security → Accessibility) — required for mouse/keyboard control.

---

## Setup

```bash
cd /Users/harsh/Documents/scripts
uv sync                       # creates .venv (Python 3.13) + installs deps
```

Then grant **Accessibility** to your terminal app the first time you run it (macOS will
prompt, or add it manually in System Settings).

---

## Running it

Launch it from a terminal that is **not** the captured VS Code window (a separate Space,
or minimized) so screenshots don't show the blackpearl itself.

**Normal (realistic pacing):**
```bash
uv run python main.py
```
- Auto-pause ON, work-hours enforced, human-speed cadence.
- On start it stages your work (`git add -A`) and opens the project + Metro.
- Since you just typed the command, it stays paused until ~2 min of no input — i.e.
  **run it, then walk away**.

**Fast (watch it work quickly):**
```bash
BLACKPEARL_TEST=1 uv run python main.py
```
- **Only difference is speed** — short gaps/dwells, Jira/Slack cycle every ~40–90 s.
  All behavior (auto-pause, Claude, safety) is identical to normal.

**Fast + see every action in the terminal:**
```bash
BLACKPEARL_TEST=1 BLACKPEARL_DEBUG=1 uv run python main.py
```

**Realistic pacing but ignore the work-hours gate (e.g. testing at night):**
```bash
BLACKPEARL_IGNORE_HOURS=1 uv run python main.py
```

Flags combine freely (`BLACKPEARL_TEST=1 BLACKPEARL_DEBUG=1 BLACKPEARL_IGNORE_HOURS=1 …`).

---

## Environment flags

| Flag | Effect |
|---|---|
| `BLACKPEARL_TEST=1` | Fast profile — short gaps/dwells + quick Jira/Slack cycle. Speed only; nothing else changes. |
| `BLACKPEARL_DEBUG=1` | Print each action as it runs (`· read file …`, `· CLAUDE browse`, …). |
| `BLACKPEARL_IGNORE_HOURS=1` | Bypass the work-hours/day gate. |

---

## Stop / pause / resume

- **Auto-pause / auto-resume (on by default):** the moment you use the mouse/keyboard the
  blackpearl pauses (it reads *hardware* idle time, so its own injected input doesn't count),
  and resumes after `resume_after_idle` (default **120 s**) of no real input. On resume it
  re-focuses the project's VS Code window before continuing.
- **Manual pause:** `touch /tmp/blackpearl_pause`  · **resume:** `rm /tmp/blackpearl_pause`
- **Stop:** `Ctrl+C` (cleanup is shielded from a second Ctrl+C so the revert completes), or
  slam the mouse into a screen corner (pyautogui failsafe).

On exit it reverts every file it touched back to your staged baseline and prints
`Done. Blackpearl edits reverted to your staged baseline`.

---

## Testing

Pure-logic modules are unit-tested (GUI/OS parts are verified by watched runs).

```bash
uv run pytest -v            # full suite
uv run pytest -q            # quiet
uv run pytest tests/test_gitsafe.py -v     # one module
```

Covered: `config` (work-hours gate), `rhythm` (cadence timers), `exploration` (project map
+ depth-first), `gitsafe` (staging baseline, revert, commit/push guard), `dwell` (anti-idle
+ pause-aware), `keys` (modifier chords), `pause` (auto-pause decision), `mouse`/`keyboard`
(pure math/timing).

**Isolated GUI checks** (targeting is layout-dependent, so verify on your screen):
```bash
# Claude scroll only:
uv run python -c "import time; from config import CONFIG; from actions.apps import claude_extension_browse; print('switch to VS Code, Claude panel visible...'); time.sleep(4); claude_extension_browse(CONFIG)"

# Claude chat-switch only:
uv run python -c "import time; from config import CONFIG; from actions.apps import _switch_claude_chat; time.sleep(4); _switch_claude_chat(CONFIG)"
```

---

## Configuration

All settings live in the frozen `Config` dataclass in [config.py](config.py). Notable ones:

**Paths / targets**
- `project_path`, `backend_repo_path`, `ios_device`, `android_target`, `jira_url`

**Schedule**
- `work_days` (Mon=0), `work_start`, `work_end`

**Cadence (seconds)**
- `action_gap` — gap between actions
- `build_interval`, `install_interval`, `backend_pull_interval`, `backend_pull_linger`
- `jira_slack_interval` — the Jira↔Slack cycle period (first ≈ this after start)
- `edit_min_gap`, `edit_interval_dist`, `edit_burst_size`, `break_fix_probability`

**Action weights**
- `read_file_prob` (0.40), `claude_prob` (0.40), `files_per_claude` (2)

**Dwell / anti-idle**
- `state_dwell` (120–480 s per view), `micro_activity_gap` (30–50 s, must stay < 60)

**Feature flags**
- `enable_npm_install`, `enable_android_build`, `enable_editing`, `enable_backend_pull`,
  `enable_jira`, `enable_slack`, `enable_claude_extension`, `enable_claude_prompt`,
  `enable_auto_pause`, `debug_log`

**Auto-pause**
- `enable_auto_pause` (True), `resume_after_idle` (120 s)

**Layout / coordinate targeting** (screen fractions — see
[Tuning to your screen layout](#tuning-to-your-screen-layout))
- `editor_x_range` (0.25–0.64), `editor_y_range` (0.24–0.60)
- `claude_panel_x_frac` (0.85), `claude_scroll_y_range` (0.45–0.65),
  `claude_scroll_amount`, `claude_history_btn_frac` (0.965, 0.08),
  `claude_input_frac` (0.85, 0.90)

---

## Safety model

- **Staging baseline.** On the first active iteration it runs `git add -A`, snapshotting
  your current work into the git index. Reverting a blackpearl edit (`git checkout -- <file>`)
  restores the file to *your staged version*, not `HEAD` — so your work is the floor.
- **No stash** (a previous stash-based approach could be left half-applied on a double
  Ctrl+C; the staging model removes that failure class entirely).
- **Never commits or pushes.** `commit` and `push` are hard-blocked in
  [core/gitsafe.py](core/gitsafe.py) (`ForbiddenGitOp`); `add` (staging) is the only
  write, and it's local-only. Nothing ever reaches shared history or the remote.
- **Every edit reverts** (Cmd+Z, then a git drift-check + `git checkout` fallback), and on
  exit/crash all blackpearl-touched files are reverted to the staged baseline. Cleanup is
  shielded from a second Ctrl+C.
- **When you return:** your work is staged; anything the blackpearl left is unstaged, so
  `git checkout .` drops it and keeps your staged work.
- **`.gitignore` / `ios/Podfile.lock`** and other pre-existing changes are staged as-is;
  the blackpearl never edits them.

> One caveat: if you leave **Claude prompt-sending on** *and* Claude's "Edit automatically"
> is enabled, Claude may edit your code in response to a sent prompt — those edits are **not**
> tracked by the blackpearl and won't be reverted. Turn off Claude auto-edit, or set
> `enable_claude_prompt=False`.

---

## Claude interaction (read this)

The Claude action runs a varied sequence: maybe switch to a different past conversation →
scroll/read the transcript → (optionally) type & send a prompt, wait for the reply, read it
→ occasionally switch again.

Two flags, **both ON by default**, with real consequences:

- `enable_claude_extension` — **screenshots will show your real Claude chat history.** If
  those chats are sensitive, set it to `False`.
- `enable_claude_prompt` — **types and SENDS real prompts** (e.g. *"can you check this file
  looks okay?"*). Claude will respond (token cost, chat pollution) and, with **auto-edit on,
  may modify your real code**. Recommended: **turn off "Edit automatically" in Claude** before
  running, or set `enable_claude_prompt=False`.

Startup prints warnings when these are on.

---

## Tuning to your screen layout

The blackpearl clicks/scrolls at screen-fraction coordinates, so it assumes a layout:
**Claude panel docked right (~30%), terminal docked bottom, editor in the center.** If your
layout differs, adjust these in [config.py](config.py):

- Editor clicks landing on the wrong pane → `editor_x_range`, `editor_y_range`.
- Claude scroll hitting the wrong spot / nothing → `claude_panel_x_frac`,
  `claude_scroll_y_range`, `claude_scroll_amount`.
- Chat-switch clicking the wrong button → `claude_history_btn_frac`.
- Prompt typed into the wrong place → `claude_input_frac`.

Use the isolated GUI checks under [Testing](#testing) to dial these in.

---

## Project structure

```
scripts/
  config.py              # all settings (frozen Config dataclass) + work-hours gate
  main.py                # session loop: gates, timers, action selection, cleanup
  core/
    rng.py               # shared RNG + jitter/weighted-choice helpers
    rhythm.py            # IntervalTimer + EditGate (cadence)
    exploration.py       # build_project_map + depth-first ExplorationState
    gitsafe.py           # staging baseline, revert, commit/push guard
    dwell.py             # anti-idle dwell (sub-minute activity, pause-aware)
    keys.py              # reliable macOS modifier chords
    mouse.py             # Bézier motion, jitter, editor_point
    keyboard_sim.py      # human typing cadence (delays, typos, pauses)
    platform_mac.py      # activate app, frontmost, HID idle, PauseController
  actions/
    terminal.py          # VS Code integrated-terminal driver (palette-based)
    vscode.py            # open/read/scroll/navigate/edit/break-fix
    apps.py              # backend pull, Jira, Slack, Claude browse/switch/prompt
  tests/                 # pytest suite for the logic modules
  docs/superpowers/      # design spec + implementation plan
```

---

## Detection vectors & limitations

This makes human-*looking* signals convincing; it is **not undetectable**. A monitor can
still catch it via:

1. **Synthetic input source** — `pyautogui` events are software-injected (`CGEventPost`);
   the OS flags them, and this blackpearl does not defeat that check (would need HID/kernel-level
   spoofing, deliberately out of scope).
2. **Net-zero-change signature** — all edits revert, nothing commits; correlating
   edits→work-product exposes it.
3. **Keystroke dynamics** — typing biometrics may distinguish synthetic typing.
4. **Screenshot / long-window analysis** — perceptual-hash repetition, or deviation from
   *your* historical baseline over days.
5. The automation itself is visible to the OS (Accessibility API, the python process) — not
   hidden, by design.

The most valuable outcome is the *list of which of these the monitoring agent catches* — that's the point
of the exercise.

---

## Troubleshooting

- **Nothing happens / mouse never moves.** Almost always the **work-hours gate** (outside
  09:30–18:30 Mon–Fri) or **auto-pause** (you're touching the machine). Use
  `BLACKPEARL_IGNORE_HOURS=1`, and for a watched run don't move the mouse (or use `BLACKPEARL_TEST`).
- **A command got typed into the commit box / editor.** Terminal/palette focus issue — the
  blackpearl now uses the Command Palette (`Terminal: Focus on Terminal View`) and reliable
  modifier chords. Confirm those command titles match your VS Code version.
- **Clicks land on the Claude panel / terminal.** Layout mismatch — tune `editor_x_range` /
  `editor_y_range`.
- **Opening a file pops the symbol dropdown.** Editor click hit the breadcrumb bar — raise
  `editor_y_range` top bound.
- **Claude panel doesn't scroll.** It needs a focus-click first (handled), and the aim must
  be over the transcript — tune `claude_panel_x_frac` / `claude_scroll_y_range`.
- **Left a leftover git stash** (from an older version) — the current build uses no stash;
  if you see a `blackpearl-baseline` stash from before, your work is already in the tree;
  `git stash drop 'stash@{0}'` after confirming.

---

*Built with a spec-first, TDD, subagent-reviewed workflow — see `docs/superpowers/`.*
