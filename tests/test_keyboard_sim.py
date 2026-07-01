from core.keyboard_sim import key_delay


def test_delay_positive():
    assert key_delay(None, "a") > 0


def test_pause_longer_after_punctuation_on_average():
    import statistics
    after_punct = statistics.mean(key_delay(".", "x") for _ in range(500))
    within_word = statistics.mean(key_delay("a", "b") for _ in range(500))
    assert after_punct > within_word
