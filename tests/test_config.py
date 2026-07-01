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
