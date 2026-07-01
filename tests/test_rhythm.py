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


def test_interval_timer_reset_redraws(monkeypatch):
    import core.rhythm as rhythm
    clk = FakeClock()
    # controlled draws: 10.0 at construction, 50.0 at reset()
    seq = iter([10.0, 50.0])
    monkeypatch.setattr(rhythm.RNG, "uniform", lambda a, b: next(seq))
    timer = rhythm.IntervalTimer((1.0, 100.0), clock=clk)  # _sampled = 10.0
    clk.advance(10.0)
    assert timer.due() is True                 # 10 >= 10
    timer.reset()                              # must redraw -> _sampled = 50.0
    clk.advance(10.0)                          # clk=20, elapsed since reset = 10
    assert timer.due() is False                # 10 >= 50 is False (would be True if stale 10.0)
    clk.advance(41.0)                          # elapsed since reset = 51
    assert timer.due() is True                 # 51 >= 50


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
