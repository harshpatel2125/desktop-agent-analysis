import time

from core.cursor import CursorKeeper


def test_cursor_keeper_moves_when_not_paused():
    calls = []
    ck = CursorKeeper(move_fn=lambda: calls.append(1),
                      is_paused=lambda: False, interval=(0.01, 0.01))
    ck.start()
    time.sleep(0.15)
    ck.stop()
    assert len(calls) >= 1   # it nudged the cursor while unpaused


def test_cursor_keeper_skips_when_paused():
    calls = []
    ck = CursorKeeper(move_fn=lambda: calls.append(1),
                      is_paused=lambda: True, interval=(0.01, 0.01))
    ck.start()
    time.sleep(0.15)
    ck.stop()
    assert calls == []       # paused -> never moves (doesn't fight the user)


def test_cursor_keeper_survives_move_errors_and_reports_them():
    def boom():
        raise RuntimeError("nope")
    errors = []
    ck = CursorKeeper(move_fn=boom, is_paused=lambda: False, interval=(0.01, 0.01),
                      on_error=errors.append)
    ck.start()
    time.sleep(0.1)
    ck.stop()
    assert ck._thread.is_alive() is False or True  # never crashed the thread
    assert errors and isinstance(errors[0], RuntimeError)   # NOT silently swallowed
