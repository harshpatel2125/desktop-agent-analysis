from core.platform_mac import PauseController


def _controller(auto_pause=True, resume_after=120.0):
    # idle_fn is irrelevant here; we call _decide_paused directly
    return PauseController(auto_pause=auto_pause, resume_after=resume_after,
                           idle_fn=lambda: 0.0)


def test_sentinel_always_pauses():
    c = _controller(auto_pause=False)
    assert c._decide_paused(idle_seconds=9999.0, sentinel_exists=True) is True


def test_recent_human_input_pauses():
    c = _controller(resume_after=120.0)
    # human touched the machine 5s ago -> pause
    assert c._decide_paused(idle_seconds=5.0, sentinel_exists=False) is True


def test_resumes_after_idle_threshold():
    c = _controller(resume_after=120.0)
    # no real input for 130s -> resume (not paused)
    assert c._decide_paused(idle_seconds=130.0, sentinel_exists=False) is False


def test_boundary_at_threshold_resumes():
    c = _controller(resume_after=120.0)
    assert c._decide_paused(idle_seconds=120.0, sentinel_exists=False) is False
    assert c._decide_paused(idle_seconds=119.9, sentinel_exists=False) is True


def test_auto_pause_off_ignores_human():
    c = _controller(auto_pause=False)
    assert c._decide_paused(idle_seconds=1.0, sentinel_exists=False) is False
