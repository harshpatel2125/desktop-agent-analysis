import random

from core.file_picker import FilePicker

GROUPS = {"screens": ["s0", "s1", "s2"], "components": ["c0", "c1"]}


def test_screens_by_default_in_order():
    # component_prob=0 -> always screens, in priority order, wrapping
    p = FilePicker(random.Random(0), component_prob=0.0)
    kinds = [p.next(GROUPS) for _ in range(4)]
    assert kinds == [("s0", "screen"), ("s1", "screen"), ("s2", "screen"), ("s0", "screen")]


def test_components_occasionally_and_in_order():
    p = FilePicker(random.Random(1), component_prob=1.0)  # force components
    got = [p.next(GROUPS) for _ in range(3)]
    assert got == [("c0", "component"), ("c1", "component"), ("c0", "component")]


def test_start_module_resets_to_top():
    p = FilePicker(random.Random(0), component_prob=0.0)
    p.next(GROUPS)
    p.next(GROUPS)
    p.start_module()
    assert p.next(GROUPS) == ("s0", "screen")   # back to most-used file


def test_no_screens_falls_back_to_components():
    p = FilePicker(random.Random(0), component_prob=0.0)
    only_comps = {"screens": [], "components": ["c0"]}
    assert p.next(only_comps) == ("c0", "component")


def test_empty_module_returns_none():
    p = FilePicker(random.Random(0))
    assert p.next({"screens": [], "components": []}) == (None, None)


def test_mixed_rate_is_mostly_screens():
    p = FilePicker(random.Random(3), component_prob=0.30)
    kinds = [p.next(GROUPS)[1] for _ in range(200)]
    comps = kinds.count("component")
    assert 40 <= comps <= 80          # ~30%, mostly screens
