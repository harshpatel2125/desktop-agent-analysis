# Blackpearl Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a macOS red-team blackpearl that drives realistic, human-paced developer activity on `warp-speed-ai-app` so the monitoring agent's presence signals (input, screenshots, active app, processes) can be tested — with all edits transient and the repo left exactly as found.

**Architecture:** Restructure the existing single-file `main.py` into a small package: pure-logic modules (`config`, `core/rhythm`, `core/exploration`, `core/gitsafe`) that are unit-tested, plus GUI-driving modules (`core/mouse`, `core/keyboard_sim`, `core/platform_mac`, `actions/*`) that are concrete but verified via integration/manual runs. A `main.py` session loop selects weighted actions paced by the rhythm scheduler, gated by work-hours/days, with pause + cleanup handlers.

**Tech Stack:** Python 3.13, pyautogui, pyobjc (Quartz/AppKit), subprocess (osascript/git/pnpm), pytest, uv.

## Global Constraints

- Python floor: `>=3.13` (Homebrew python@3.14 has broken `pyexpat`/`plistlib` on this machine; `.venv` is built on 3.13). Verbatim from spec.
- Target project path: `/Users/harsh/Documents/projects/warpspeed/warp-speed-ai-app`.
- Backend repo path: `/Users/harsh/Documents/projects/warpspeed/warp-speed-ai-backend`.
- iOS device: `"Harsh's iPhone 12 Pro"`.
- Package manager for the target project: pnpm (`pnpm start`, `pnpm ios:device`, `pnpm android`).
- **Transient only:** every edit is reverted; the blackpearl performs **no `git commit`, no `git add`/staging, no `git push`** — ever. A guard must reject these.
- **No local anti-forensics** (no scrubbing reflog/history/process hiding). Remote-invisibility comes from never-commit/never-push + revert.
- Cleanup reverts **only files the blackpearl's own edit/break-fix actions touched** — never a blanket `git checkout .`; leave pre-existing changes, `ios/Podfile.lock`, `package-lock.json` alone.
- Active only on `WORK_DAYS` (default Mon–Fri) within `WORK_HOURS` (default 09:30–18:30).
- pyautogui failsafe stays ON (corner-slam abort); `PAUSE_HOTKEY` yields to a returning real user.
- All external commands best-effort (`check=False`), non-blocking, with `COMMAND_TIMEOUT`.

---

## File Structure

```
scripts/
  config.py                 # dataclass of all settings + is_active_now() gate
  core/
    __init__.py
    rng.py                  # single seeded-or-unseeded Random source + helpers
    rhythm.py               # RhythmScheduler + edit-interval sampling + Timer gates
    exploration.py          # build_project_map() + ExplorationState (depth-first)
    gitsafe.py              # GitSafe: stash/restore, drift-check, revert, commit/push guard
    mouse.py                # Bézier motion, overshoot, jitter (GUI)
    keyboard_sim.py         # human typing cadence generator + type() (GUI)
    platform_mac.py         # activate app, frontmost app, pause-hotkey listener (GUI/OS)
  actions/
    __init__.py
    terminal.py             # named VS Code terminals, non-blocking command runner (GUI)
    vscode.py               # open project, scroll modes, navigate, edit/revert, break/fix (GUI)
    apps.py                 # browser excursions, backend pull, claude ext (gated) (GUI)
  main.py                   # session loop wiring, gates, pause, cleanup
  tests/
    test_config.py
    test_rhythm.py
    test_exploration.py
    test_gitsafe.py
  pyproject.toml            # add pytest + describe deps
```

Existing `main.py` (the current single-file demo) is the reference for mouse/vscode idioms and is replaced by the new package `main.py` in Task 12.

---

### Task 1: Package scaffolding + `config.py` with active-time gate

**Files:**
- Create: `config.py`
- Create: `core/__init__.py`, `actions/__init__.py`, `tests/__init__.py`
- Create: `core/rng.py`
- Test: `tests/test_config.py`
- Modify: `pyproject.toml` (add pytest dev dependency)

**Interfaces:**
- Produces: `Config` dataclass (frozen) with all fields; module-level `CONFIG = Config()`; `is_active_now(cfg: Config, now: datetime) -> bool`.
- Produces: `core/rng.py` exposing `RNG` (an instance of `random.Random`) and thin helpers `jitter(base, frac)`, `weighted_choice(pairs)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
from datetime import datetime
from config import Config, is_active_now


def _dt(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm)


def test_active_inside_hours_on_workday():
    cfg = Config()  # defaults: Mon-Fri, 09:30-18:30
    # 2026-07-01 is a Wednesday
    assert is_active_now(cfg, _dt(2026, 7, 1, 10, 0)) is True


def test_inactive_before_start():
    cfg = Config()
    assert is_active_now(cfg, _dt(2026, 7, 1, 9, 0)) is False


def test_inactive_after_end():
    cfg = Config()
    assert is_active_now(cfg, _dt(2026, 7, 1, 19, 0)) is False


def test_inactive_on_weekend():
    cfg = Config()
    # 2026-07-04 is a Saturday
    assert is_active_now(cfg, _dt(2026, 7, 4, 10, 0)) is False


def test_boundary_start_inclusive_end_exclusive():
    cfg = Config()
    assert is_active_now(cfg, _dt(2026, 7, 1, 9, 30)) is True
    assert is_active_now(cfg, _dt(2026, 7, 1, 18, 30)) is False
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'config'`.

- [ ] **Step 3: Write minimal implementation**

```python
# config.py
from dataclasses import dataclass, field
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
    action_gap: tuple[float, float] = (30.0, 90.0)
    build_interval: tuple[float, float] = (45 * 60, 75 * 60)      # ~1h jittered
    install_interval: tuple[float, float] = (45 * 60, 75 * 60)    # ~1h jittered
    backend_pull_interval: tuple[float, float] = (100 * 60, 140 * 60)  # ~2h jittered
    backend_pull_linger: tuple[float, float] = (5 * 60, 9 * 60)   # >=5 min
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
    enable_browser_excursions: bool = True
    enable_editing: bool = True
    enable_claude_extension: bool = False  # off by default (self-incrimination risk)
    enable_backend_pull: bool = True
    debug_log: bool = False

    # keys
    pause_hotkey: tuple[str, ...] = ("ctrl", "alt", "p")


def is_active_now(cfg: Config, now: datetime) -> bool:
    if now.weekday() not in cfg.work_days:
        return False
    t = now.time()
    return cfg.work_start <= t < cfg.work_end


CONFIG = Config()
```

```python
# core/rng.py
import random

RNG = random.Random()  # unseeded: real entropy, no reproducible signature


def jitter(base: float, frac: float) -> float:
    """Return base +/- (frac * base), uniformly."""
    delta = base * frac
    return base + RNG.uniform(-delta, delta)


def weighted_choice(pairs):
    """pairs: iterable of (value, weight). Returns a chosen value."""
    values = [v for v, _ in pairs]
    weights = [w for _, w in pairs]
    return RNG.choices(values, weights=weights, k=1)[0]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_config.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Add pytest to pyproject and commit**

Add to `pyproject.toml` under a new `[dependency-groups]` (uv) section:

```toml
[dependency-groups]
dev = ["pytest>=8.0"]
```

Run: `uv sync` (expected: installs pytest). There is no git repo here yet; if the user has run `git init`, commit — otherwise skip the commit step.

```bash
git add config.py core/__init__.py core/rng.py actions/__init__.py tests/ pyproject.toml
git commit -m "feat: config + active-time gate with tests"
```

---

### Task 2: `core/rhythm.py` — cadence timers + edit-interval sampling

**Files:**
- Create: `core/rhythm.py`
- Test: `tests/test_rhythm.py`

**Interfaces:**
- Consumes: `config.Config`, `core.rng.RNG`, `core.rng.weighted_choice`.
- Produces:
  - `class IntervalTimer(interval_range: tuple[float,float], clock: Callable[[], float])` with `.due() -> bool` and `.reset()`. Fires when `clock() - last >= sampled`, where `sampled` is re-drawn on each `reset()`.
  - `sample_edit_interval(cfg) -> float` (weighted).
  - `class EditGate(cfg, clock)` with `.due() -> bool` and `.fired()`. Enforces `edit_min_gap` hard floor AND the sampled interval.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_rhythm.py
from config import Config
from core.rhythm import IntervalTimer, EditGate, sample_edit_interval


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def advance(self, dt):
        self.t += dt


def test_interval_timer_not_due_before_min():
    clk = FakeClock()
    # fixed range so sample is deterministic
    timer = IntervalTimer((100.0, 100.0), clock=clk)
    timer.reset()
    clk.advance(99.0)
    assert timer.due() is False
    clk.advance(2.0)
    assert timer.due() is True


def test_interval_timer_reset_redraws():
    clk = FakeClock()
    timer = IntervalTimer((100.0, 100.0), clock=clk)
    timer.reset()
    clk.advance(101.0)
    assert timer.due() is True
    timer.reset()
    assert timer.due() is False


def test_sample_edit_interval_within_declared_ranges():
    cfg = Config()
    lo = min(r[0][0] for r in cfg.edit_interval_dist)
    hi = max(r[0][1] for r in cfg.edit_interval_dist)
    for _ in range(200):
        s = sample_edit_interval(cfg)
        assert lo <= s <= hi


def test_edit_gate_respects_min_gap():
    cfg = Config(edit_min_gap=300.0,
                 edit_interval_dist=(((1.0, 1.0), 1.0),))  # sampled interval ~1s
    clk = FakeClock()
    gate = EditGate(cfg, clock=clk)
    gate.fired()            # just edited at t=0
    clk.advance(299.0)
    assert gate.due() is False   # min gap not satisfied even though sample is tiny
    clk.advance(2.0)
    assert gate.due() is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_rhythm.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.rhythm'`.

- [ ] **Step 3: Write minimal implementation**

```python
# core/rhythm.py
import time as _time
from typing import Callable

from core.rng import RNG, weighted_choice


def sample_edit_interval(cfg) -> float:
    lo, hi = weighted_choice(cfg.edit_interval_dist)
    return RNG.uniform(lo, hi)


class IntervalTimer:
    """Fires once per sampled interval; re-samples on reset()."""

    def __init__(self, interval_range, clock: Callable[[], float] = _time.monotonic):
        self._range = interval_range
        self._clock = clock
        self._last = clock()
        self._sampled = self._draw()

    def _draw(self) -> float:
        lo, hi = self._range
        return RNG.uniform(lo, hi)

    def due(self) -> bool:
        return (self._clock() - self._last) >= self._sampled

    def reset(self) -> None:
        self._last = self._clock()
        self._sampled = self._draw()


class EditGate:
    """Edit fires only when BOTH the min gap and a freshly sampled interval elapse."""

    def __init__(self, cfg, clock: Callable[[], float] = _time.monotonic):
        self._cfg = cfg
        self._clock = clock
        self._last = clock()
        self._sampled = sample_edit_interval(cfg)

    def due(self) -> bool:
        elapsed = self._clock() - self._last
        return elapsed >= self._cfg.edit_min_gap and elapsed >= self._sampled

    def fired(self) -> None:
        self._last = self._clock()
        self._sampled = sample_edit_interval(self._cfg)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_rhythm.py -v`
Expected: PASS (4 passed).

- [ ] **Step 5: Commit**

```bash
git add core/rhythm.py tests/test_rhythm.py
git commit -m "feat: rhythm timers + edit-interval sampling with tests"
```

---

### Task 3: `core/exploration.py` — dynamic project map + depth-first state

**Files:**
- Create: `core/exploration.py`
- Test: `tests/test_exploration.py`

**Interfaces:**
- Produces:
  - `build_project_map(src_root: str) -> ProjectMap` where `ProjectMap` has `.modules: dict[str, list[str]]` (module name → list of file paths) and `.all_files: list[str]`. Excludes `*.spec.ts`, `*.test.ts`, `*.stories.tsx`, and any path containing `node_modules`.
  - `class ExplorationState(pmap)` with `.next_file() -> str | None` (depth-first within a module before moving on) and `.mark_read(path)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_exploration.py
import os
from core.exploration import build_project_map, ExplorationState


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("// x\n")


def test_build_map_groups_by_module_and_excludes(tmp_path):
    root = str(tmp_path / "src")
    _touch(os.path.join(root, "features", "home", "index.ts"))
    _touch(os.path.join(root, "features", "home", "components", "Card.tsx"))
    _touch(os.path.join(root, "features", "home", "utils.test.ts"))   # excluded
    _touch(os.path.join(root, "features", "home", "Card.stories.tsx"))  # excluded
    _touch(os.path.join(root, "features", "profile", "index.ts"))
    _touch(os.path.join(root, "node_modules", "junk", "a.ts"))         # excluded

    pmap = build_project_map(root)

    assert set(pmap.modules.keys()) >= {"features/home", "features/profile"}
    home = pmap.modules["features/home"]
    assert any(p.endswith("index.ts") for p in home)
    assert any(p.endswith("Card.tsx") for p in home)
    assert not any("test" in p or "stories" in p for p in pmap.all_files)
    assert not any("node_modules" in p for p in pmap.all_files)


def test_exploration_depth_first_finishes_module_before_next(tmp_path):
    root = str(tmp_path / "src")
    _touch(os.path.join(root, "features", "home", "index.ts"))
    _touch(os.path.join(root, "features", "home", "a.tsx"))
    _touch(os.path.join(root, "features", "profile", "index.ts"))
    pmap = build_project_map(root)

    state = ExplorationState(pmap)
    first = state.next_file()
    state.mark_read(first)
    second = state.next_file()
    # first two files should be from the same module
    mod_of = {p: m for m, ps in pmap.modules.items() for p in ps}
    assert mod_of[first] == mod_of[second]


def test_next_file_returns_none_when_exhausted(tmp_path):
    root = str(tmp_path / "src")
    _touch(os.path.join(root, "features", "home", "index.ts"))
    pmap = build_project_map(root)
    state = ExplorationState(pmap)
    p = state.next_file()
    state.mark_read(p)
    assert state.next_file() is None
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_exploration.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.exploration'`.

- [ ] **Step 3: Write minimal implementation**

```python
# core/exploration.py
import os
from dataclasses import dataclass, field

from core.rng import RNG

_EXCLUDE_SUFFIXES = (".spec.ts", ".test.ts", ".stories.tsx")
_INCLUDE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx")


def _module_name(src_root: str, path: str) -> str:
    rel = os.path.relpath(path, src_root)
    parts = rel.split(os.sep)
    # group by first two path components when present (e.g. features/home)
    if len(parts) >= 3:
        return os.path.join(parts[0], parts[1])
    return parts[0]


@dataclass
class ProjectMap:
    modules: dict = field(default_factory=dict)
    all_files: list = field(default_factory=list)


def build_project_map(src_root: str) -> ProjectMap:
    pmap = ProjectMap()
    for dirpath, dirnames, filenames in os.walk(src_root):
        if "node_modules" in dirpath.split(os.sep):
            continue
        for name in filenames:
            if name.endswith(_EXCLUDE_SUFFIXES):
                continue
            if not name.endswith(_INCLUDE_SUFFIXES):
                continue
            full = os.path.join(dirpath, name)
            pmap.all_files.append(full)
            mod = _module_name(src_root, full)
            pmap.modules.setdefault(mod, []).append(full)
    return pmap


class ExplorationState:
    """Depth-first: exhaust one module's files before moving to another."""

    def __init__(self, pmap: ProjectMap):
        self._pmap = pmap
        self._read: set = set()
        self._current_module: str | None = None

    def _module_of(self, path: str) -> str:
        for m, files in self._pmap.modules.items():
            if path in files:
                return m
        return ""

    def _unread_in(self, module: str):
        return [p for p in self._pmap.modules.get(module, []) if p not in self._read]

    def next_file(self):
        # stay in the current module while it has unread files
        if self._current_module and self._unread_in(self._current_module):
            return RNG.choice(self._unread_in(self._current_module))
        # otherwise pick a new module that still has unread files
        candidates = [m for m in self._pmap.modules if self._unread_in(m)]
        if not candidates:
            return None
        self._current_module = RNG.choice(candidates)
        return RNG.choice(self._unread_in(self._current_module))

    def mark_read(self, path: str) -> None:
        self._read.add(path)
        self._current_module = self._module_of(path)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_exploration.py -v`
Expected: PASS (3 passed).

- [ ] **Step 5: Commit**

```bash
git add core/exploration.py tests/test_exploration.py
git commit -m "feat: dynamic project map + depth-first exploration state"
```

---

### Task 4: `core/gitsafe.py` — stash/restore, drift-check, scoped revert, commit/push guard

**Files:**
- Create: `core/gitsafe.py`
- Test: `tests/test_gitsafe.py`

**Interfaces:**
- Produces `class GitSafe(repo_path: str)` with:
  - `run(args: list[str]) -> subprocess.CompletedProcess` — raises `ForbiddenGitOp` if `args[0]` in `{commit, add, push}`.
  - `is_dirty() -> bool`
  - `stash_push() -> bool` (returns True if something was stashed), `stash_pop()`
  - `file_is_clean(path: str) -> bool` (path unchanged vs HEAD/index)
  - `revert_file(path: str)` — `git checkout -- <path>`
  - Tracks touched files: `note_touched(path)`, `revert_all_touched()`.
- Raises `ForbiddenGitOp(Exception)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_gitsafe.py
import subprocess
import pytest
from core.gitsafe import GitSafe, ForbiddenGitOp


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    f = repo / "a.txt"
    f.write_text("original\n")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    return repo, f


def test_forbidden_ops_raise(tmp_path):
    repo, _ = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    for bad in (["commit", "-m", "x"], ["add", "."], ["push"]):
        with pytest.raises(ForbiddenGitOp):
            gs.run(bad)


def test_file_is_clean_detects_change(tmp_path):
    repo, f = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    assert gs.file_is_clean("a.txt") is True
    f.write_text("changed\n")
    assert gs.file_is_clean("a.txt") is False


def test_revert_file_restores(tmp_path):
    repo, f = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    f.write_text("changed\n")
    gs.revert_file("a.txt")
    assert f.read_text() == "original\n"
    assert gs.file_is_clean("a.txt") is True


def test_stash_roundtrip_preserves_precheck_changes(tmp_path):
    repo, f = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    f.write_text("user-wip\n")           # pre-existing uncommitted work
    assert gs.is_dirty() is True
    assert gs.stash_push() is True
    assert f.read_text() == "original\n"  # stashed away
    gs.stash_pop()
    assert f.read_text() == "user-wip\n"  # restored


def test_revert_all_touched_only_touches_tracked(tmp_path):
    repo, f = _init_repo(tmp_path)
    other = repo / "b.txt"
    other.write_text("original-b\n")
    subprocess.run(["git", "add", "b.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "b"], cwd=repo, check=True)
    gs = GitSafe(str(repo))
    f.write_text("blackpearl-edit\n")
    other.write_text("user-edit-b\n")     # NOT tracked by blackpearl
    gs.note_touched("a.txt")
    gs.revert_all_touched()
    assert f.read_text() == "original\n"       # reverted
    assert other.read_text() == "user-edit-b\n"  # left alone
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_gitsafe.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.gitsafe'`.

- [ ] **Step 3: Write minimal implementation**

```python
# core/gitsafe.py
import subprocess

_FORBIDDEN = {"commit", "add", "push"}


class ForbiddenGitOp(Exception):
    pass


class GitSafe:
    def __init__(self, repo_path: str):
        self.repo = repo_path
        self._touched: set[str] = set()
        self._stashed = False

    def run(self, args: list[str]) -> subprocess.CompletedProcess:
        if args and args[0] in _FORBIDDEN:
            raise ForbiddenGitOp(f"git {args[0]} is not permitted by the blackpearl")
        return subprocess.run(
            ["git", *args], cwd=self.repo,
            capture_output=True, text=True, check=False,
        )

    def is_dirty(self) -> bool:
        out = self.run(["status", "--porcelain"]).stdout
        return bool(out.strip())

    def file_is_clean(self, path: str) -> bool:
        out = self.run(["status", "--porcelain", "--", path]).stdout
        return not out.strip()

    def revert_file(self, path: str) -> None:
        self.run(["checkout", "--", path])

    def note_touched(self, path: str) -> None:
        self._touched.add(path)

    def revert_all_touched(self) -> None:
        for path in sorted(self._touched):
            self.revert_file(path)
        self._touched.clear()

    def stash_push(self) -> bool:
        if not self.is_dirty():
            return False
        # include untracked so nothing user-made leaks into blackpearl edits
        res = self.run(["stash", "push", "-u", "-m", "blackpearl-baseline"])
        self._stashed = res.returncode == 0
        return self._stashed

    def stash_pop(self) -> None:
        if self._stashed:
            self.run(["stash", "pop"])
            self._stashed = False
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_gitsafe.py -v`
Expected: PASS (5 passed).

- [ ] **Step 5: Commit**

```bash
git add core/gitsafe.py tests/test_gitsafe.py
git commit -m "feat: git safety net with commit/push guard and scoped revert"
```

---

### Task 5: `core/mouse.py` — Bézier motion, overshoot, jitter

**Files:**
- Create: `core/mouse.py` (port + extend from existing `main.py:57-89`)
- Test: `tests/test_mouse.py` (pure-geometry only)

**Interfaces:**
- Consumes: `pyautogui`, `core.rng.RNG`.
- Produces:
  - `cubic_bezier(p0, p1, p2, p3, t) -> (x, y)` (pure)
  - `ease(t) -> float` (pure)
  - `move_bezier(start, end, duration=0.6, steps=80)` (GUI: calls `pyautogui.moveTo`)
  - `micro_jitter(radius=3, moves=…)` (GUI)
  - `editor_point() -> (x, y)` (GUI: uses `pyautogui.size()`)

- [ ] **Step 1: Write the failing test (pure geometry)**

```python
# tests/test_mouse.py
from core.mouse import cubic_bezier, ease


def test_bezier_endpoints():
    p0, p1, p2, p3 = (0, 0), (1, 1), (2, 2), (3, 3)
    assert cubic_bezier(p0, p1, p2, p3, 0.0) == (0.0, 0.0)
    assert cubic_bezier(p0, p1, p2, p3, 1.0) == (3.0, 3.0)


def test_ease_bounds():
    assert abs(ease(0.0) - 0.0) < 1e-9
    assert abs(ease(1.0) - 1.0) < 1e-9
    assert 0.0 <= ease(0.5) <= 1.0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_mouse.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.mouse'`.

- [ ] **Step 3: Write minimal implementation**

```python
# core/mouse.py
import math
import time

import pyautogui

from core.rng import RNG


def cubic_bezier(p0, p1, p2, p3, t):
    mt = 1 - t
    x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
    y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
    return x, y


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def move_bezier(start, end, duration=0.6, steps=80):
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    dist = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / dist, dx / dist
    bow = dist * RNG.uniform(0.05, 0.2) * RNG.choice([-1, 1])
    c1 = (sx + dx * 0.3 + nx * bow, sy + dy * 0.3 + ny * bow)
    c2 = (sx + dx * 0.7 + nx * bow * RNG.uniform(0.3, 1.0),
          sy + dy * 0.7 + ny * bow * RNG.uniform(0.3, 1.0))
    # duration scales mildly with distance (Fitts-ish)
    duration = duration * (0.6 + min(dist / 1200.0, 1.4))
    for i in range(1, steps + 1):
        t = ease(i / steps)
        x, y = cubic_bezier(start, c1, c2, end, t)
        pyautogui.moveTo(x, y)
        time.sleep(duration / steps)


def micro_jitter(radius=3, moves=None):
    """Small movements as if resting the hand while reading."""
    moves = moves if moves is not None else RNG.randint(1, 3)
    x, y = pyautogui.position()
    for _ in range(moves):
        pyautogui.moveTo(x + RNG.randint(-radius, radius), y + RNG.randint(-radius, radius))
        time.sleep(RNG.uniform(0.2, 0.8))


def editor_point():
    w, h = pyautogui.size()
    x = RNG.randint(int(w * 0.35), int(w * 0.92))
    y = RNG.randint(int(h * 0.22), int(h * 0.78))
    return x, y
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_mouse.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Manual integration check + commit**

Manual check (only when you can watch the screen; failsafe is on — slam a corner to abort):
`uv run python -c "from core.mouse import move_bezier, editor_point; import pyautogui; move_bezier(pyautogui.position(), editor_point())"`
Expected: cursor glides along a curved path to a point in the editor region.

```bash
git add core/mouse.py tests/test_mouse.py
git commit -m "feat: bezier mouse motion with jitter and Fitts-scaled duration"
```

---

### Task 6: `core/keyboard_sim.py` — human typing cadence

**Files:**
- Create: `core/keyboard_sim.py`
- Test: `tests/test_keyboard_sim.py` (delay generator only)

**Interfaces:**
- Consumes: `pyautogui`, `core.rng.RNG`.
- Produces:
  - `key_delay(prev_char: str | None, ch: str) -> float` (pure: longer after punctuation/space, faster within words).
  - `type_text(text: str, typo_rate=0.03)` (GUI: types char-by-char with delays, occasional typo→backspace→fix, thinking pauses).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_keyboard_sim.py
from core.keyboard_sim import key_delay


def test_delay_positive():
    assert key_delay(None, "a") > 0


def test_pause_longer_after_punctuation_on_average():
    import statistics
    after_punct = statistics.mean(key_delay(".", "x") for _ in range(500))
    within_word = statistics.mean(key_delay("a", "b") for _ in range(500))
    assert after_punct > within_word
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_keyboard_sim.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.keyboard_sim'`.

- [ ] **Step 3: Write minimal implementation**

```python
# core/keyboard_sim.py
import time

import pyautogui

from core.rng import RNG

_PUNCT = set(".,;:!?)( []{}")


def key_delay(prev_char, ch) -> float:
    base = RNG.uniform(0.05, 0.13)
    if prev_char is None:
        return base
    if prev_char in _PUNCT or prev_char == " ":
        base += RNG.uniform(0.10, 0.35)  # thinking pause after punctuation/space
    return base


def type_text(text: str, typo_rate: float = 0.03) -> None:
    prev = None
    for ch in text:
        # occasional typo: type a wrong neighbor char, then correct it
        if ch.isalpha() and RNG.random() < typo_rate:
            wrong = RNG.choice("asdfghjkl")
            pyautogui.typewrite(wrong)
            time.sleep(key_delay(prev, wrong))
            pyautogui.press("backspace")
            time.sleep(RNG.uniform(0.1, 0.25))
        pyautogui.typewrite(ch)
        time.sleep(key_delay(prev, ch))
        prev = ch
        # rare mid-typing "thinking" pause
        if RNG.random() < 0.02:
            time.sleep(RNG.uniform(0.6, 1.8))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_keyboard_sim.py -v`
Expected: PASS (2 passed).

- [ ] **Step 5: Commit**

```bash
git add core/keyboard_sim.py tests/test_keyboard_sim.py
git commit -m "feat: human typing cadence with typos and thinking pauses"
```

---

### Task 7: `core/platform_mac.py` — app activation, frontmost detection, pause hotkey

**Files:**
- Create: `core/platform_mac.py`
- (No unit test — pure OS integration; verified manually in Step 4.)

**Interfaces:**
- Consumes: `subprocess`, `pyobjc` (`AppKit.NSWorkspace`), `config.Config`.
- Produces:
  - `activate_app(name: str)` — osascript `tell application ... to activate`.
  - `frontmost_app() -> str` — via `NSWorkspace.sharedWorkspace().frontmostApplication().localizedName()`.
  - `is_frontmost(name: str) -> bool`
  - `class PauseController(hotkey)` with `.paused -> bool`, started via a background listener; toggles on hotkey. Uses pyautogui hotkey polling fallback if a global listener isn't available.

- [ ] **Step 1: Write the module**

```python
# core/platform_mac.py
import subprocess
import threading
import time

from AppKit import NSWorkspace  # pyobjc


def activate_app(name: str) -> None:
    subprocess.run(["osascript", "-e", f'tell application "{name}" to activate'],
                   check=False)


def frontmost_app() -> str:
    app = NSWorkspace.sharedWorkspace().frontmostApplication()
    return app.localizedName() if app else ""


def is_frontmost(name: str) -> bool:
    return frontmost_app() == name


class PauseController:
    """Toggle-able pause flag. Polls NSWorkspace + a sentinel file for control.

    A global hotkey requires Accessibility + an event tap; to stay dependency-light
    the blackpearl also honors a sentinel file at /tmp/blackpearl_pause (create=pause, remove=resume).
    """

    SENTINEL = "/tmp/blackpearl_pause"

    def __init__(self):
        self._paused = False
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._poll, daemon=True)

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop.set()

    @property
    def paused(self) -> bool:
        return self._paused

    def _poll(self):
        import os
        while not self._stop.is_set():
            self._paused = os.path.exists(self.SENTINEL)
            time.sleep(1.0)
```

- [ ] **Step 2: Manual verification**

Run:
`uv run python -c "from core.platform_mac import frontmost_app; print(frontmost_app())"`
Expected: prints the current frontmost app name (e.g. `Code` or `Terminal`).

`uv run python -c "from core.platform_mac import activate_app; activate_app('Visual Studio Code')"`
Expected: VS Code comes to the foreground.

- [ ] **Step 3: Commit**

```bash
git add core/platform_mac.py
git commit -m "feat: macOS app activation, frontmost detection, pause controller"
```

---

### Task 8: `actions/terminal.py` — named VS Code terminals + non-blocking command runner

**Files:**
- Create: `actions/terminal.py`
- (Verified via integration in Step 3.)

**Interfaces:**
- Consumes: `pyautogui`, `core.keyboard_sim.type_text`, `core.platform_mac.activate_app`, `config.Config`.
- Produces:
  - `open_new_terminal()` — Ctrl+` then the "new terminal" chord.
  - `run_in_terminal(command: str)` — focus VS Code, ensure a terminal, `type_text(command)`, press enter. Does NOT wait (non-blocking; Metro/builds keep running).
  - `run_sequence(commands: list[str], gap=(0.5,1.5))` — types several commands with human gaps (for `cd ios && pod install && cd ..` style flows typed as separate lines).

- [ ] **Step 1: Write the module**

```python
# actions/terminal.py
import time

import pyautogui

from config import CONFIG
from core.keyboard_sim import type_text
from core.platform_mac import activate_app
from core.rng import RNG

_VSCODE = "Visual Studio Code"


def _focus_vscode():
    activate_app(_VSCODE)
    time.sleep(RNG.uniform(0.4, 0.8))


def open_new_terminal():
    _focus_vscode()
    # Ctrl+` toggles the integrated terminal; Ctrl+Shift+` opens a new one
    pyautogui.hotkey("ctrl", "shift", "`")
    time.sleep(RNG.uniform(0.6, 1.2))


def focus_terminal():
    _focus_vscode()
    pyautogui.hotkey("ctrl", "`")
    time.sleep(RNG.uniform(0.3, 0.7))


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
```

- [ ] **Step 2: Note on cross-terminal management**

Metro runs in the first terminal (opened at startup by `main.py`). Build/install/backend actions call `open_new_terminal()` first so they don't interrupt Metro, then `run_in_terminal(...)`. The backend pull opens its own terminal, `cd`s to the backend path, runs `git pull`, lingers, then returns focus to the editor via `activate_app` + `Cmd+1`.

- [ ] **Step 3: Integration check (manual, VS Code open on the project)**

Run:
`uv run python -c "from actions.terminal import run_in_terminal; run_in_terminal('echo hello-from-blackpearl')"`
Expected: VS Code terminal receives and runs the echo.

- [ ] **Step 4: Commit**

```bash
git add actions/terminal.py
git commit -m "feat: VS Code terminal runner (non-blocking) + sequences"
```

---

### Task 9: `actions/vscode.py` — open project, scroll modes, navigation, edit/revert, break/fix

**Files:**
- Create: `actions/vscode.py`
- (Verified via integration; git safety unit-tested in Task 4.)

**Interfaces:**
- Consumes: `pyautogui`, `core.mouse`, `core.keyboard_sim`, `core.platform_mac`, `core.gitsafe.GitSafe`, `config.CONFIG`.
- Produces:
  - `open_project(path)` — `code --reuse-window <path>`.
  - `open_file(path)` — quick-open (Cmd+P) + type relative path + enter.
  - `read_scroll(mode)` where mode in `{"slow","skim","dwell"}`.
  - `navigate()` — one of go-to-line / find / go-to-symbol / switch-tab / go-to-definition.
  - `edit_and_revert(gitsafe, file_abs, repo_root)` — insert a comment line, wait, Cmd+Z, then drift-check → `revert_file` fallback.
  - `break_and_fix(gitsafe, file_abs, repo_root)` — same mechanics; documented as reusing `edit_and_revert`'s revert path.

- [ ] **Step 1: Write the module**

```python
# actions/vscode.py
import os
import shutil
import subprocess
import time

import pyautogui

from config import CONFIG
from core import mouse
from core.keyboard_sim import type_text
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
    pyautogui.hotkey("command", "p")
    time.sleep(0.6)
    type_text(rel_path)
    time.sleep(0.5)
    pyautogui.press("enter")
    time.sleep(RNG.uniform(0.5, 1.0))


def _click_editor():
    _focus()
    mouse.move_bezier(pyautogui.position(), mouse.editor_point())
    pyautogui.click()
    time.sleep(RNG.uniform(0.2, 0.4))


def read_scroll(mode: str):
    _click_editor()
    if mode == "slow":
        for _ in range(RNG.randint(4, 10)):
            pyautogui.scroll(-RNG.randint(1, 2))
            time.sleep(RNG.uniform(0.6, 1.6))
            if RNG.random() < 0.15:  # occasionally scroll back up to re-read
                pyautogui.scroll(RNG.randint(1, 2))
                time.sleep(RNG.uniform(0.4, 1.0))
    elif mode == "skim":
        for _ in range(RNG.randint(3, 6)):
            pyautogui.scroll(-RNG.randint(4, 9))
            time.sleep(RNG.uniform(0.1, 0.3))
    elif mode == "dwell":
        end = time.monotonic() + RNG.uniform(90, 300)  # minutes on one file
        while time.monotonic() < end:
            mouse.micro_jitter()
            time.sleep(RNG.uniform(5, 20))


def navigate():
    _click_editor()
    choice = RNG.choice(["goto_line", "find", "symbol", "switch_tab", "definition"])
    if choice == "goto_line":
        pyautogui.hotkey("command", "g")
        time.sleep(0.5)
        type_text(str(RNG.randint(1, 200)))
        pyautogui.press("enter")
    elif choice == "find":
        pyautogui.hotkey("command", "f")
        time.sleep(0.4)
        type_text(RNG.choice(["const ", "return", "useEffect", "import ", "props"]))
        for _ in range(RNG.randint(2, 5)):
            pyautogui.press("enter")
            time.sleep(RNG.uniform(0.4, 1.0))
        pyautogui.press("escape")
    elif choice == "symbol":
        pyautogui.hotkey("command", "shift", "o")
        time.sleep(0.6)
        for _ in range(RNG.randint(0, 5)):
            pyautogui.press("down")
            time.sleep(RNG.uniform(0.15, 0.4))
        pyautogui.press("enter")
    elif choice == "switch_tab":
        if RNG.random() < 0.5:
            pyautogui.hotkey("control", "tab")
        else:
            pyautogui.hotkey("control", "shift", "tab")
    elif choice == "definition":
        pyautogui.press("f12")
        time.sleep(RNG.uniform(0.6, 1.2))


def _revert_with_fallback(gitsafe, file_abs, repo_root, undo_presses):
    """Cmd+Z primary; git drift-check + checkout fallback. Always leaves file clean."""
    _focus()
    for _ in range(undo_presses):
        pyautogui.hotkey("command", "z")
        time.sleep(RNG.uniform(0.2, 0.5))
    pyautogui.hotkey("command", "s")  # save so git sees the reverted state
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
        pyautogui.hotkey("command", "g")
        time.sleep(0.4)
        type_text(str(RNG.randint(5, 60)))
        pyautogui.press("enter")
        pyautogui.press("home")
        type_text("// note: reviewing this section\n")
        pyautogui.hotkey("command", "s")
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
        pyautogui.hotkey("command", "g")
        time.sleep(0.4)
        type_text(str(RNG.randint(5, 60)))
        pyautogui.press("enter")
        pyautogui.press("home")
        # a line that reliably fails tsc but is self-contained
        type_text("const __tmp_bad: number = 'oops'\n")
        pyautogui.hotkey("command", "s")
        time.sleep(RNG.uniform(30, 120))  # "look at" the error
    finally:
        _revert_with_fallback(gitsafe, file_abs, repo_root, undo_presses=RNG.randint(3, 6))
```

- [ ] **Step 2: Integration check (manual)**

Precondition: VS Code open on the project; working tree clean; `GitSafe` pointed at the repo.
Run a single edit/revert against a scratch commit and confirm `git status` is clean afterward:
```
uv run python -c "
from core.gitsafe import GitSafe
from actions.vscode import edit_and_revert
repo='/Users/harsh/Documents/projects/warpspeed/warp-speed-ai-app'
gs=GitSafe(repo)
edit_and_revert(gs, repo+'/src/features/home/index.ts', repo)
print('dirty?', gs.is_dirty())
"
```
Expected: after it runs, the touched file is clean (drift-check/fallback guarantees it).

- [ ] **Step 3: Commit**

```bash
git add actions/vscode.py
git commit -m "feat: vscode actions - open, scroll modes, navigate, edit/revert, break/fix"
```

---

### Task 10: `actions/apps.py` — browser excursions, backend pull, Claude extension (gated)

**Files:**
- Create: `actions/apps.py`

**Interfaces:**
- Consumes: `pyautogui`, `actions.terminal`, `core.platform_mac`, `core.gitsafe.GitSafe`, `config.CONFIG`.
- Produces:
  - `browser_excursion()` — Cmd+Tab to another app, linger, return to VS Code.
  - `backend_pull(cfg)` — open a new terminal, `cd` backend, `git pull` (best-effort), linger ≥5 min, return to editor. Uses a `GitSafe(cfg.backend_repo_path)` only to *guard* (pull is allowed; commit/add/push are not).
  - `claude_extension_browse(cfg)` — gated by `cfg.enable_claude_extension` (default False); if enabled, opens the panel WITHOUT opening individual chats (avoids surfacing this design conversation).

- [ ] **Step 1: Write the module**

```python
# actions/apps.py
import time

import pyautogui

from actions.terminal import open_new_terminal, run_in_terminal
from core.gitsafe import GitSafe
from core.platform_mac import activate_app
from core.rng import RNG

_VSCODE = "Visual Studio Code"


def browser_excursion():
    pyautogui.hotkey("command", "tab")     # to most-recent other app
    time.sleep(RNG.uniform(20, 60))
    pyautogui.hotkey("command", "tab")     # back
    activate_app(_VSCODE)


def backend_pull(cfg):
    if not cfg.enable_backend_pull:
        return
    gs = GitSafe(cfg.backend_repo_path)     # guard object (pull is allowed)
    open_new_terminal()
    run_in_terminal(f'cd "{cfg.backend_repo_path}"')
    time.sleep(RNG.uniform(0.5, 1.2))
    run_in_terminal("git pull")             # best-effort; failure is fine
    # linger in the terminal >= 5 min
    lo, hi = cfg.backend_pull_linger
    time.sleep(RNG.uniform(lo, hi))
    # return focus to the editor pane
    activate_app(_VSCODE)
    pyautogui.hotkey("command", "1")


def claude_extension_browse(cfg):
    if not cfg.enable_claude_extension:
        return
    # open the panel only; do NOT open individual conversations (avoids leaking
    # the blackpearl's own design chat into a the monitoring agent screenshot).
    activate_app(_VSCODE)
    time.sleep(RNG.uniform(0.4, 0.8))
    # command palette -> focus Claude view (label may vary by version)
    pyautogui.hotkey("command", "shift", "p")
    time.sleep(0.6)
    # deliberately just dismiss to avoid opening chats
    pyautogui.press("escape")
```

- [ ] **Step 2: Integration check (manual)**

Run: `uv run python -c "from config import CONFIG; from actions.apps import backend_pull; backend_pull(CONFIG)"`
Expected: a new VS Code terminal opens, `cd`s to the backend, runs `git pull` (may error harmlessly), lingers, returns to the editor.

- [ ] **Step 3: Commit**

```bash
git add actions/apps.py
git commit -m "feat: browser excursion, backend pull, gated claude-panel action"
```

---

### Task 11: `main.py` — session loop, gates, pause, cleanup

**Files:**
- Create: `main.py` (replaces the existing single-file demo)
- Keep the old file content available in git history (it is the reference implementation).

**Interfaces:**
- Consumes: everything above.
- Produces: `main()` entrypoint; weighted action loop; work-hours/days gate; pause handling; startup stash + shutdown cleanup.

- [ ] **Step 1: Write the module**

```python
# main.py
"""blackpearl — macOS. READ THE SPEC before changing behavior:
docs/superpowers/specs/2026-07-01-blackpearl-design.md

Transient only: every edit is reverted; never commits/pushes; leaves the repo as found.
Stop: PAUSE via `touch /tmp/blackpearl_pause` (resume: rm it), Ctrl+C, or slam a screen corner.
"""
import os
import time
from datetime import datetime

import pyautogui

from config import CONFIG, is_active_now
from core.exploration import build_project_map, ExplorationState
from core.gitsafe import GitSafe
from core.platform_mac import PauseController
from core.rhythm import IntervalTimer, EditGate
from core.rng import RNG
from actions import vscode, apps, terminal

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0


def _ios_build_sequence(cfg):
    terminal.open_new_terminal()
    terminal.run_in_terminal(f'cd "{cfg.project_path}"')
    terminal.run_sequence(["cd ios", "pod install", "cd .."])
    terminal.run_in_terminal(f'pnpm ios:device "{cfg.ios_device}"')


def _npm_install(cfg):
    terminal.open_new_terminal()
    terminal.run_in_terminal(f'cd "{cfg.project_path}"')
    terminal.run_in_terminal("npm i")          # accepted risk (pnpm repo)
    # a human would notice failure and retry with -f; blackpearl always follows up
    time.sleep(RNG.uniform(20, 60))
    terminal.run_in_terminal("npm i -f")


def main():
    cfg = CONFIG
    src_root = os.path.join(cfg.project_path, "src")
    gitsafe = GitSafe(cfg.project_path)
    pause = PauseController()
    pause.start()

    # startup: protect any pre-existing uncommitted work
    stashed = gitsafe.stash_push()

    pmap = build_project_map(src_root)
    explore = ExplorationState(pmap)

    vscode.open_project(cfg.project_path)
    terminal.run_in_terminal(f'cd "{cfg.project_path}" && pnpm start')  # Metro

    build_timer = IntervalTimer(cfg.build_interval)
    install_timer = IntervalTimer(cfg.install_interval)
    backend_timer = IntervalTimer(cfg.backend_pull_interval)
    edit_gate = EditGate(cfg)

    try:
        while True:
            if pause.paused:
                time.sleep(2.0)
                continue
            if not is_active_now(cfg, datetime.now()):
                time.sleep(60.0)
                continue

            time.sleep(RNG.uniform(*cfg.action_gap))

            # hourly-ish heavy actions
            if build_timer.due():
                _ios_build_sequence(cfg)
                build_timer.reset()
                continue
            if cfg.enable_npm_install and install_timer.due():
                _npm_install(cfg)
                install_timer.reset()
                continue
            if cfg.enable_backend_pull and backend_timer.due():
                apps.backend_pull(cfg)
                backend_timer.reset()
                continue

            # editing (transient), gated by min-gap + sampled interval
            if cfg.enable_editing and edit_gate.due():
                target = explore.next_file() or RNG.choice(pmap.all_files)
                if RNG.random() < cfg.break_fix_probability:
                    vscode.break_and_fix(gitsafe, target, cfg.project_path)
                else:
                    vscode.edit_and_revert(gitsafe, target, cfg.project_path)
                edit_gate.fired()
                continue

            # default: reading / exploration / light navigation
            roll = RNG.random()
            if roll < 0.45:
                target = explore.next_file()
                if target:
                    vscode.open_file(os.path.relpath(target, cfg.project_path))
                    explore.mark_read(target)
                    vscode.read_scroll(RNG.choice(["slow", "slow", "skim", "dwell"]))
            elif roll < 0.80:
                vscode.navigate()
            elif roll < 0.92 and cfg.enable_browser_excursions:
                apps.browser_excursion()
            else:
                vscode.read_scroll("slow")

            # foreground watcher: if focus drifted off VS Code, come back
            from core.platform_mac import is_frontmost
            if not is_frontmost("Code") and not is_frontmost("Visual Studio Code"):
                vscode._focus()

    except KeyboardInterrupt:
        print("\nStopping — reverting blackpearl edits...")
    finally:
        gitsafe.revert_all_touched()
        if stashed:
            gitsafe.stash_pop()
        pause.stop()
        print("Clean. Repo left as found.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Smoke test the wiring (no GUI)**

Run: `uv run python -c "import main; print('import ok')"`
Expected: `import ok` (all modules resolve).

- [ ] **Step 3: Commit**

```bash
git add main.py
git commit -m "feat: session loop with gates, pause, startup stash + cleanup"
```

---

### Task 12: Preflight, docs, and end-to-end dry run

**Files:**
- Modify: `pyproject.toml` (description/metadata)
- Create: `README.md` (run + safety instructions)

**Interfaces:** none new.

- [ ] **Step 1: Add a preflight to `main.py`**

Insert near the top of `main()` (after `cfg = CONFIG`):

```python
    import shutil
    if not shutil.which("code"):
        raise SystemExit("VS Code 'code' CLI not found. Run 'Shell Command: Install code command in PATH'.")
    if not os.path.isdir(os.path.join(cfg.project_path, ".git")):
        raise SystemExit(f"Project not a git repo: {cfg.project_path}")
```

- [ ] **Step 2: Write `README.md`**

```markdown
# Blackpearl (macOS)

Red-team presence-simulation blackpearl for testing the monitoring agent. Transient only:
never commits/pushes; reverts every edit; leaves the repo as found.

## Setup
- `uv sync` (Python 3.13; pyautogui + pyobjc + pytest)
- Grant **Accessibility** permission to the terminal app you launch it from
  (System Settings → Privacy & Security → Accessibility).

## Run
- Launch from a terminal that is NOT the captured VS Code window
  (separate Space / minimized): `uv run python main.py`

## Stop / pause
- Pause: `touch /tmp/blackpearl_pause`  · Resume: `rm /tmp/blackpearl_pause`
- Hard stop: Ctrl+C, or slam the mouse into a screen corner (pyautogui failsafe).

## Config
Edit `config.py` (`Config` dataclass). Notable flags:
`enable_npm_install`, `enable_editing`, `enable_backend_pull`,
`enable_claude_extension` (off by default), `work_days`, `work_start/end`.

## Tests
`uv run pytest -v` (logic modules: config, rhythm, exploration, gitsafe, mouse, keyboard).

## Known limitations
See the spec's "Detection vectors & honest limitations" section.
```

- [ ] **Step 3: Full test suite green**

Run: `uv run pytest -v`
Expected: all logic tests pass (config, rhythm, exploration, gitsafe, mouse, keyboard).

- [ ] **Step 4: Guarded end-to-end dry run**

With VS Code closed and a *clean* project tree, run `uv run python main.py` for ~2 minutes while watching, then Ctrl+C. Confirm:
- VS Code opens on the project and Metro starts.
- Mouse/scroll/navigation look human.
- After Ctrl+C: `git -C <project> status` shows no blackpearl-introduced changes.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml README.md main.py
git commit -m "chore: preflight, README, e2e dry-run instructions"
```

---

## Self-Review

**Spec coverage:**
- Signals (input/screenshots/active-app/process) → mouse/keyboard (T5,T6), scroll/read (T9), foreground watcher + terminals (T8,T11), real builds (T11). ✓
- Hourly iOS build w/ `pod install` → `_ios_build_sequence` (T11). ✓
- Hourly `npm i` → `npm i -f` → `_npm_install` (T11), flag in config (T1). ✓
- Backend pull (~2h) + linger ≥5 min → `backend_pull` (T10). ✓
- Project exploration walk + depth-first → exploration (T3), wired (T11). ✓
- Human scroll modes (slow/skim/dwell) → `read_scroll` (T9). ✓
- Edit cadence (min gap, sampled interval, bursts) → rhythm (T2), config (T1). ✓
- Edit/revert + break/fix, Cmd+Z → git fallback → vscode (T9), gitsafe (T4). ✓
- Local-only guarantee (no commit/add/push) → gitsafe guard (T4). ✓
- Startup stash / scoped cleanup → gitsafe (T4), main (T11). ✓
- Work hours + work days → config (T1), gated (T11). ✓
- Pause/yield, off-screen run → platform_mac PauseController (T7), README (T12). ✓
- Claude extension gated off + no-open-chats → apps (T10). ✓
- Detection-vectors/limitations documented → spec + README (T12). ✓

**Placeholder scan:** No TBD/TODO left in code; each code step contains full code. (`config.py` has a comment `# accepted risk`, not a placeholder.)

**Type consistency:** `GitSafe.file_is_clean/revert_file/note_touched/revert_all_touched/stash_push/stash_pop` used consistently across T4/T9/T11. `EditGate.due/fired`, `IntervalTimer.due/reset` consistent T2/T11. `ExplorationState.next_file/mark_read` consistent T3/T11. `read_scroll(mode)` values `{slow,skim,dwell}` match T9↔T11.

**Note on `_ios_build_sequence` `run_sequence`:** `cd ios && pod install && cd ..` is typed as three lines via `run_sequence` (T8) so a `pod install` failure doesn't chain-abort the `cd ..`.

---

## Increment 2 (Tasks 13–14): external apps + anti-idle dwell

Added after the core plan per user request: open the assigned Jira board in Chrome, open/focus Slack, and enforce a **minimum 2-minute dwell** on every established state with **sub-minute micro-activity** so no inactivity gap crosses the monitoring agent's ~1-minute idle threshold.

### Task 13: config additions + `core/dwell.py` (anti-idle dwell engine)

**Files:**
- Modify: `config.py` (add external-app + dwell fields to `Config`)
- Create: `core/dwell.py`
- Test: `tests/test_dwell.py`

**Interfaces:**
- Consumes: `core.rng.RNG`.
- Produces: `dwell(seconds, activity, gap_range=(30.0,50.0), sleep=time.sleep, clock=time.monotonic) -> int` — holds a state for `seconds`, invoking `activity()` on a jittered sub-minute cadence; returns the number of activity bursts. `sleep`/`clock` are injectable for tests.
- New `Config` fields: `jira_url: str`, `enable_jira: bool = True`, `enable_slack: bool = True`, `state_dwell: tuple[float,float] = (120.0, 480.0)`, `micro_activity_gap: tuple[float,float] = (30.0, 50.0)`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_dwell.py
from core.dwell import dwell


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, dt):
        self.t += dt


def test_dwell_respects_min_duration():
    clk = FakeClock()
    calls = []
    dwell(600.0, lambda: calls.append(clk()), gap_range=(30.0, 50.0),
          sleep=clk.sleep, clock=clk)
    assert clk() >= 600.0


def test_dwell_fires_activity_sub_minute():
    clk = FakeClock()
    calls = []
    dwell(600.0, lambda: calls.append(clk()), gap_range=(30.0, 50.0),
          sleep=clk.sleep, clock=clk)
    # anti-idle: every gap between input bursts must be < 60s
    gaps = [b - a for a, b in zip([0.0] + calls, calls)]
    assert gaps, "expected at least one activity burst"
    assert all(g < 60.0 for g in gaps)
    # and over 600s with <=50s gaps there must be several bursts
    assert len(calls) >= 10


def test_dwell_activity_never_exceeds_gap_ceiling():
    clk = FakeClock()
    calls = []
    dwell(300.0, lambda: calls.append(clk()), gap_range=(30.0, 50.0),
          sleep=clk.sleep, clock=clk)
    gaps = [b - a for a, b in zip([0.0] + calls, calls)]
    assert all(g <= 50.0 + 1e-9 for g in gaps)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dwell.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'core.dwell'`.

- [ ] **Step 3: Write minimal implementation**

```python
# core/dwell.py
import time as _time
from typing import Callable

from core.rng import RNG


def dwell(seconds: float,
          activity: Callable[[], None],
          gap_range=(30.0, 50.0),
          sleep: Callable[[float], None] = _time.sleep,
          clock: Callable[[], float] = _time.monotonic) -> int:
    """Hold a state for `seconds`, invoking `activity()` on a jittered sub-minute
    cadence (gap_range must stay under 60s) so no inactivity gap crosses an idle
    threshold. Returns the number of activity bursts performed."""
    end = clock() + seconds
    bursts = 0
    while clock() < end:
        remaining = end - clock()
        nap = min(RNG.uniform(*gap_range), remaining)
        sleep(nap)
        if clock() < end:
            activity()
            bursts += 1
    return bursts
```

Then add to `config.py` inside the `Config` dataclass (place after the `# feature flags` block; keep it a frozen dataclass with valid default types):

```python
    # external apps
    jira_url: str = "https://flixpremiere.atlassian.net/jira/software/projects/WS/boards/9?jql=assignee%20%3D%20712020%3A99f52d86-aac3-4f8f-86b2-fed545449c48"
    enable_jira: bool = True
    enable_slack: bool = True

    # dwell / anti-idle (seconds)
    state_dwell: tuple[float, float] = (120.0, 480.0)      # >= 2 min per state
    micro_activity_gap: tuple[float, float] = (30.0, 50.0)  # act before 60s idle
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_dwell.py -v` → 3 passed.
Run: `uv run pytest tests/ -v` → full suite (23 prior + 3 new = 26) passes.

- [ ] **Step 5: Commit**

```bash
git add core/dwell.py tests/test_dwell.py config.py
git commit -m "feat: anti-idle dwell engine + external-app/dwell config"
```

### Task 14: `actions/apps.py` Jira/Slack actions + wire dwell into `main.py`

**Files:**
- Modify: `actions/apps.py` (add `jira_board`, `open_slack`)
- Modify: `main.py` (apply `dwell` after view-establishing actions; add Jira/Slack branches)

**Interfaces:**
- Consumes: `pyautogui`, `subprocess`, `core.keyboard_sim.type_text`, `core.platform_mac.activate_app`, `core.rng.RNG`, `core.dwell.dwell`, `core.mouse.micro_jitter`, `config`.
- Produces: `jira_board(cfg)`, `open_slack(cfg)` in `actions/apps.py`.

- [ ] **Step 1: Add the two actions to `actions/apps.py`**

Add at the top with the other imports:
```python
import subprocess
from core.keyboard_sim import type_text
```
Add these module constants near `_VSCODE`:
```python
_CHROME = "Google Chrome"
_SLACK = "Slack"
```
Add the functions:
```python
def jira_board(cfg):
    """Open a new Chrome tab on the assigned Jira board (view-only)."""
    if not cfg.enable_jira:
        return
    subprocess.run(["open", "-a", _CHROME], check=False)  # launch or focus Chrome
    time.sleep(RNG.uniform(1.0, 2.0))
    pyautogui.hotkey("command", "t")                       # new tab
    time.sleep(RNG.uniform(0.4, 0.8))
    type_text(cfg.jira_url)
    time.sleep(RNG.uniform(0.2, 0.5))
    pyautogui.press("enter")
    time.sleep(RNG.uniform(1.5, 3.0))                      # let the board load


def open_slack(cfg):
    """Bring Slack to the front (launch it if it isn't running)."""
    if not cfg.enable_slack:
        return
    subprocess.run(["open", "-a", _SLACK], check=False)    # focus if running, else launch
    time.sleep(RNG.uniform(2.0, 4.0))
    activate_app(_SLACK)
    time.sleep(RNG.uniform(0.5, 1.0))
```

- [ ] **Step 2: Wire dwell + Jira/Slack into `main.py`**

Add imports near the other `core` imports at the top of `main.py`:
```python
from core.dwell import dwell
from core import mouse
```
Replace the default reading/nav/excursion branch (the block starting `roll = RNG.random()` through the `else: vscode.read_scroll("slow")`) with:
```python
            # default: reading / exploration / light navigation — every established
            # view is held for >= 2 min with sub-minute micro-activity (anti-idle).
            roll = RNG.random()
            state_dwell = lambda: dwell(RNG.uniform(*cfg.state_dwell),
                                        mouse.micro_jitter,
                                        gap_range=cfg.micro_activity_gap)
            if roll < 0.40:
                target = explore.next_file()
                if target:
                    vscode.open_file(os.path.relpath(target, cfg.project_path))
                    explore.mark_read(target)
                    vscode.read_scroll(RNG.choice(["slow", "slow", "skim"]))
                    state_dwell()
            elif roll < 0.62:
                vscode.navigate()
                state_dwell()
            elif roll < 0.72 and cfg.enable_browser_excursions:
                apps.browser_excursion()
            elif roll < 0.84 and cfg.enable_jira:
                apps.jira_board(cfg)
                state_dwell()
            elif roll < 0.96 and cfg.enable_slack:
                apps.open_slack(cfg)
                state_dwell()
            else:
                vscode.read_scroll("slow")
                state_dwell()
```
(The existing foreground watcher after this block returns focus to VS Code after Jira/Slack dwells — leave it unchanged.)

- [ ] **Step 3: Verify (no live run)**

Import smoke (must not run `main()`):
`uv run python -c "import main, actions.apps as a; assert callable(a.jira_board) and callable(a.open_slack); print('ok')"`
Full suite: `uv run pytest tests/ -v` → 26 passing (no import regressions).
Do NOT run `python main.py` (live blackpearl).

- [ ] **Step 4: Commit**

```bash
git add actions/apps.py main.py
git commit -m "feat: jira board + slack actions, anti-idle dwell wired into loop"
```

