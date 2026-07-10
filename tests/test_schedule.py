import random

from core.schedule import ActiveClock, ModuleScheduler, parse_module_flag

KEYS = ["calendar", "chat", "emails", "notes", "tasks"]


def test_parse_module_flag_single_and_multi():
    assert parse_module_flag(["--module:emails"], KEYS) == ["emails"]
    assert parse_module_flag(["--module:emails,calendar"], KEYS) == ["emails", "calendar"]
    # unknown keys dropped
    assert parse_module_flag(["--module:emails,bogus"], KEYS) == ["emails"]
    # all unknown -> None
    assert parse_module_flag(["--module:bogus"], KEYS) is None
    # absent -> None
    assert parse_module_flag(["main.py"], KEYS) is None


def test_sequence_cycles_strictly():
    s = ModuleScheduler(KEYS, sequence=["emails", "calendar", "tasks"])
    got = [s.module_for_period(i) for i in range(7)]
    assert got == ["emails", "calendar", "tasks", "emails", "calendar", "tasks", "emails"]


def test_single_module_then_random():
    s = ModuleScheduler(KEYS, sequence=["emails"], rng=random.Random(1))
    assert s.module_for_period(0) == "emails"          # first period fixed
    later = [s.module_for_period(i) for i in range(1, 6)]
    assert all(m in KEYS for m in later)
    # memoized: same period -> same answer
    assert s.module_for_period(1) == later[0]


def test_random_never_repeats_consecutively():
    s = ModuleScheduler(KEYS, sequence=None, rng=random.Random(7))
    chain = [s.module_for_period(i) for i in range(20)]
    assert all(a != b for a, b in zip(chain, chain[1:]))


def test_active_clock_freezes_while_paused():
    now = {"t": 0.0}
    paused = {"v": False}
    clk = ActiveClock(is_paused=lambda: paused["v"], clock=lambda: now["t"], tick=0.1)
    # 10s unpaused -> 10s active
    for _ in range(10):
        now["t"] += 1.0
        clk._pump()
    assert clk.elapsed() == 10.0
    # 5s paused -> no advance
    paused["v"] = True
    for _ in range(5):
        now["t"] += 1.0
        clk._pump()
    assert clk.elapsed() == 10.0
    # resume 3s -> 13s
    paused["v"] = False
    for _ in range(3):
        now["t"] += 1.0
        clk._pump()
    assert clk.elapsed() == 13.0
