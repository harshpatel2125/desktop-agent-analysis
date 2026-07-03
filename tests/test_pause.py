from core.platform_mac import PauseController


def _controller(auto_pause=True, resume_after=120.0, own_input_grace=1.5):
    # idle_fn is irrelevant here; we call _decide_paused directly.
    return PauseController(auto_pause=auto_pause, resume_after=resume_after,
                           idle_fn=lambda: 0.0, own_input_recency_fn=lambda: 999.0,
                           own_input_grace=own_input_grace)


def test_sentinel_always_pauses():
    c = _controller(auto_pause=False)
    assert c._decide_paused(idle_seconds=9999.0, sentinel_exists=True,
                            own_input_recent=False) is True


def test_recent_human_input_pauses():
    c = _controller(resume_after=120.0)
    # human touched the machine 5s ago -> pause
    assert c._decide_paused(idle_seconds=5.0, sentinel_exists=False,
                            own_input_recent=False) is True


def test_resumes_after_idle_threshold():
    c = _controller(resume_after=120.0)
    # no real input for 130s -> resume (not paused)
    assert c._decide_paused(idle_seconds=130.0, sentinel_exists=False,
                            own_input_recent=False) is False


def test_boundary_at_threshold_resumes():
    c = _controller(resume_after=120.0)
    assert c._decide_paused(idle_seconds=120.0, sentinel_exists=False,
                            own_input_recent=False) is False
    assert c._decide_paused(idle_seconds=119.9, sentinel_exists=False,
                            own_input_recent=False) is True


def test_auto_pause_off_ignores_human():
    c = _controller(auto_pause=False)
    assert c._decide_paused(idle_seconds=1.0, sentinel_exists=False,
                            own_input_recent=False) is False


def test_own_recent_input_does_not_falsely_pause():
    # idle looks tiny (0s) but it's OUR OWN action that just posted it, not a human —
    # must NOT be treated as "a human is here".
    c = _controller(resume_after=120.0)
    assert c._decide_paused(idle_seconds=0.0, sentinel_exists=False,
                            own_input_recent=True) is False


def test_sentinel_wins_even_during_own_input_grace():
    c = _controller(resume_after=120.0)
    assert c._decide_paused(idle_seconds=0.0, sentinel_exists=True,
                            own_input_recent=True) is True


def test_poll_survives_idle_fn_exception(monkeypatch):
    # a broken idle_fn must not silently kill the poll thread (which would freeze
    # `paused` forever and look exactly like "auto-pause stopped working").
    errors = []
    calls = {"n": 0}

    def flaky_idle():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return 999.0  # plenty idle on subsequent calls

    c = PauseController(auto_pause=True, resume_after=120.0, idle_fn=flaky_idle,
                        own_input_recency_fn=lambda: 999.0, poll=0.01,
                        on_error=errors.append)
    c.start()
    import time
    time.sleep(0.1)
    c.stop()
    assert errors and isinstance(errors[0], RuntimeError)
    assert calls["n"] >= 2   # kept polling after the exception
