import random

RNG = random.Random()  # unseeded: real entropy, no reproducible signature


def jitter(base: float, frac: float) -> float:
    """Return base +/- (frac * base), uniformly."""
    delta = base * frac
    return base + RNG.uniform(-delta, delta)


def weighted_choice(pairs):
    """pairs: iterable of (value, weight). Returns a chosen value."""
    values = [v for v, _ in pairs]
    weights = [w for _, w in pairs]
    return RNG.choices(values, weights=weights, k=1)[0]
