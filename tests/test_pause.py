import time

from core.platform_mac import PauseController


def _controller(auto_pause=True, resume_after=120.0, human_idle_fn=lambda: 999.0):
    # human_idle_fn is irrelevant when we call _decide_paused directly; supplying it
    # (and NOT None) keeps the controller from spinning up a real event-tap monitor.
    return PauseController(auto_pause=auto_pause, resume_after=resume_after,
                           human_idle_fn=human_idle_fn)


def test_sentinel_always_pauses():
    c = _controller(auto_pause=False)
    assert c._decide_paused(human_idle_seconds=9999.0, sentinel_exists=True) is True


def test_recent_human_input_pauses():
    c = _controller(resume_after=120.0)
    # human touched the machine 5s ago -> pause
    assert c._decide_paused(human_idle_seconds=5.0, sentinel_exists=False) is True


def test_resumes_after_idle_threshold():
    c = _controller(resume_after=120.0)
    # no real human input for 130s -> resume (not paused)
    assert c._decide_paused(human_idle_seconds=130.0, sentinel_exists=False) is False


def test_boundary_at_threshold_resumes():
    c = _controller(resume_after=120.0)
    assert c._decide_paused(human_idle_seconds=120.0, sentinel_exists=False) is False
    assert c._decide_paused(human_idle_seconds=119.9, sentinel_exists=False) is True


def test_auto_pause_off_ignores_human():
    c = _controller(auto_pause=False)
    assert c._decide_paused(human_idle_seconds=1.0, sentinel_exists=False) is False


def test_own_synthetic_input_never_pauses():
    # The whole point of the event-tap rewrite: the harness's OWN input is excluded at
    # the source (by PID) before it ever reaches human_idle_fn, so a busy harness reads
    # a LARGE human-idle value and does not pause on itself.
    c = _controller(resume_after=120.0, human_idle_fn=lambda: 10_000.0)
    idle = c._human_idle_fn()
    assert c._decide_paused(human_idle_seconds=idle, sentinel_exists=False) is False


def test_sentinel_wins_even_when_not_idle():
    c = _controller(resume_after=120.0)
    assert c._decide_paused(human_idle_seconds=0.0, sentinel_exists=True) is True


def test_poll_reflects_human_idle_fn(monkeypatch, tmp_path):
    # End-to-end through the poll thread: a small human-idle reading flips paused True;
    # a large one flips it back. No real event tap is created (human_idle_fn supplied).
    monkeypatch.setattr(PauseController, "SENTINEL", str(tmp_path / "nope"))
    idle = {"v": 5.0}
    c = PauseController(auto_pause=True, resume_after=120.0,
                        human_idle_fn=lambda: idle["v"], poll=0.01)
    c.start()
    time.sleep(0.05)
    assert c.paused is True            # human active 5s ago
    idle["v"] = 999.0
    time.sleep(0.05)
    assert c.paused is False           # long idle -> resume
    c.stop()


def test_poll_survives_human_idle_fn_exception():
    # a broken idle fn must not silently kill the poll thread (which would freeze
    # `paused` forever and look exactly like "auto-pause stopped working").
    errors = []
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return 999.0

    c = PauseController(auto_pause=True, resume_after=120.0, human_idle_fn=flaky,
                        poll=0.01, on_error=errors.append)
    c.start()
    time.sleep(0.1)
    c.stop()
    assert errors and isinstance(errors[0], RuntimeError)
    assert calls["n"] >= 2   # kept polling after the exception
