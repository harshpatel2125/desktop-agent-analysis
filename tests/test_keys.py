import core.keys as keys


def _record(monkeypatch):
    calls = []
    monkeypatch.setattr(keys.pyautogui, "keyDown", lambda k: calls.append(("down", k)))
    monkeypatch.setattr(keys.pyautogui, "keyUp", lambda k: calls.append(("up", k)))
    monkeypatch.setattr(keys.pyautogui, "press", lambda k: calls.append(("press", k)))
    monkeypatch.setattr(keys.time, "sleep", lambda s: None)
    return calls


def test_chord_holds_modifiers_around_key(monkeypatch):
    calls = _record(monkeypatch)
    keys.hotkey("command", "shift", "p")
    # modifiers pressed (and held) BEFORE the key, released AFTER, in reverse order
    assert calls == [
        ("down", "command"),
        ("down", "shift"),
        ("press", "p"),
        ("up", "shift"),
        ("up", "command"),
    ]


def test_single_key_just_presses(monkeypatch):
    calls = _record(monkeypatch)
    keys.hotkey("enter")
    assert calls == [("press", "enter")]


def test_two_key_chord_order(monkeypatch):
    calls = _record(monkeypatch)
    keys.hotkey("command", "z")
    assert calls == [("down", "command"), ("press", "z"), ("up", "command")]
