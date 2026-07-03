from core.rhythm import IntervalTimer


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
