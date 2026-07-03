from core.pacing import paced_sleep


class FakeClock:
    def __init__(self):
        self.t = 0.0

    def __call__(self):
        return self.t

    def sleep(self, dt):
        self.t += dt


def test_paced_sleep_completes_full_duration_when_never_paused():
    clk = FakeClock()
    ok = paced_sleep(10.0, is_paused=lambda: False, chunk_range=(1.0, 2.0),
                     sleep=clk.sleep, clock=clk)
    assert ok is True
    assert clk() >= 10.0


def test_paced_sleep_cuts_short_when_paused():
    clk = FakeClock()
    checks = {"n": 0}

    def is_paused():
        checks["n"] += 1
        return checks["n"] > 2   # becomes paused after a couple checks

    ok = paced_sleep(6000.0, is_paused=is_paused, chunk_range=(1.0, 2.0),
                     sleep=clk.sleep, clock=clk)
    assert ok is False
    assert clk() < 6000.0   # did NOT grind through the full duration


def test_paced_sleep_never_naps_longer_than_chunk_max():
    clk = FakeClock()
    naps = []
    real_sleep = clk.sleep

    def tracking_sleep(dt):
        naps.append(dt)
        real_sleep(dt)

    paced_sleep(5.0, is_paused=lambda: False, chunk_range=(1.0, 2.0),
               sleep=tracking_sleep, clock=clk)
    assert all(n <= 2.0 + 1e-9 for n in naps)
