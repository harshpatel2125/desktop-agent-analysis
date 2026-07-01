from core.mouse import cubic_bezier, ease


def test_bezier_endpoints():
    p0, p1, p2, p3 = (0, 0), (1, 1), (2, 2), (3, 3)
    assert cubic_bezier(p0, p1, p2, p3, 0.0) == (0.0, 0.0)
    assert cubic_bezier(p0, p1, p2, p3, 1.0) == (3.0, 3.0)


def test_ease_bounds():
    assert abs(ease(0.0) - 0.0) < 1e-9
    assert abs(ease(1.0) - 1.0) < 1e-9
    assert 0.0 <= ease(0.5) <= 1.0
