from core.rotation import Rotator


def test_cycles_without_repeat_then_restarts():
    r = Rotator(["a", "b", "c"])
    got = [r.next() for _ in range(7)]
    assert got == ["a", "b", "c", "a", "b", "c", "a"]
    # no URL repeats before the whole list is exhausted
    assert got[:3] == ["a", "b", "c"]


def test_single_item_repeats():
    r = Rotator(["only"])
    assert [r.next() for _ in range(3)] == ["only", "only", "only"]


def test_empty_returns_none():
    r = Rotator([])
    assert r.next() is None
    assert len(r) == 0
