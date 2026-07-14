"""The scroll never runs past the file's content into the blank void below the last line.

This is pure-logic: GUI helpers (_move_over_editor, _wheel, is_vscode_frontmost) are
stubbed, so we assert only the position math — the part that was scrolling short files
into the empty area past their end."""
import random

import actions.vscode as v

_SCREEN = v._LINES_PER_SCREEN


def _target_for(monkeypatch, total_lines, seed=0):
    """Run _scroll_down_past_imports with GUI stubbed; return the lines it scrolled."""
    captured = {}
    monkeypatch.setattr(v, "is_vscode_frontmost", lambda: True)
    monkeypatch.setattr(v, "_move_over_editor", lambda: None)
    monkeypatch.setattr(v, "count_lines", lambda p: total_lines)
    monkeypatch.setattr(v, "_wheel", lambda lines, up=False, step=4: captured.update(lines=lines, up=up))
    monkeypatch.setattr(v.RNG, "uniform", random.Random(seed).uniform)
    return _run(v._scroll_down_past_imports, "x.tsx"), captured


def _run(fn, *a):
    return fn(*a)


def test_short_file_never_scrolls_past_content(monkeypatch):
    for total in (50, 80, 100, 150):
        pos, cap_info = _target_for(monkeypatch, total)
        max_ok = max(0, total - _SCREEN)
        assert pos <= max_ok, f"{total}-line file scrolled {pos} > cap {max_ok} (into void)"


def test_file_fitting_on_screen_does_not_scroll(monkeypatch):
    pos, cap = _target_for(monkeypatch, _SCREEN)      # exactly one screen
    assert pos == 0 and cap == {}                     # no scroll issued at all


def test_long_file_scrolls_at_least_min(monkeypatch):
    pos, _ = _target_for(monkeypatch, 1200)
    assert pos >= v._MIN_SCROLL_LINES                 # long files still go well past imports
    assert pos <= 1200 - _SCREEN                      # but never into the void


def test_reader_never_exceeds_bounds_over_many_steps(monkeypatch):
    monkeypatch.setattr(v, "is_vscode_frontmost", lambda: True)
    monkeypatch.setattr(v, "_move_over_editor", lambda: None)
    monkeypatch.setattr(v, "_wheel", lambda lines, up=False, step=4: None)  # don't really scroll
    monkeypatch.setattr(v, "count_lines", lambda p: 150)
    monkeypatch.setattr(v.RNG, "randint", random.Random(1).randint)
    monkeypatch.setattr(v.RNG, "random", random.Random(2).random)

    reader = v.FileReader("x.tsx", start_pos=120)
    cap = max(0, 150 - _SCREEN)
    reader.reset(999)                                 # even a bogus start clamps into range
    assert 0 <= reader.pos <= cap
    for _ in range(200):
        reader.step()
        assert 0 <= reader.pos <= cap, f"reader.pos={reader.pos} escaped [0,{cap}]"
