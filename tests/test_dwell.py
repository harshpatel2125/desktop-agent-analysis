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


def test_dwell_stops_immediately_when_paused():
    clk = FakeClock()
    calls = []
    # paused from the very start -> no activity fires, returns at once
    dwell(600.0, lambda: calls.append(clk()), gap_range=(30.0, 50.0),
          sleep=clk.sleep, clock=clk, is_paused=lambda: True)
    assert calls == []


def test_dwell_stops_when_pause_flips_mid_hold():
    clk = FakeClock()
    calls = []
    checks = {"n": 0}

    def is_paused():
        checks["n"] += 1
        return checks["n"] > 3   # becomes paused after a few checks

    dwell(6000.0, lambda: calls.append(clk()), gap_range=(30.0, 50.0),
          sleep=clk.sleep, clock=clk, is_paused=is_paused)
    # stopped early instead of running the full 6000s of bursts
    assert 0 < len(calls) < 20
