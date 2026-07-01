import math
import time

import pyautogui

from core.rng import RNG


def cubic_bezier(p0, p1, p2, p3, t):
    mt = 1 - t
    x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
    y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
    return x, y


def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * t)


def move_bezier(start, end, duration=0.6, steps=80):
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    dist = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / dist, dx / dist
    bow = dist * RNG.uniform(0.05, 0.2) * RNG.choice([-1, 1])
    c1 = (sx + dx * 0.3 + nx * bow, sy + dy * 0.3 + ny * bow)
    c2 = (sx + dx * 0.7 + nx * bow * RNG.uniform(0.3, 1.0),
          sy + dy * 0.7 + ny * bow * RNG.uniform(0.3, 1.0))
    # duration scales mildly with distance (Fitts-ish)
    duration = duration * (0.6 + min(dist / 1200.0, 1.4))
    for i in range(1, steps + 1):
        t = ease(i / steps)
        x, y = cubic_bezier(start, c1, c2, end, t)
        pyautogui.moveTo(x, y)
        time.sleep(duration / steps)


def micro_jitter(radius=3, moves=None):
    """Small movements as if resting the hand while reading."""
    moves = moves if moves is not None else RNG.randint(1, 3)
    x, y = pyautogui.position()
    for _ in range(moves):
        pyautogui.moveTo(x + RNG.randint(-radius, radius), y + RNG.randint(-radius, radius))
        time.sleep(RNG.uniform(0.2, 0.8))


def editor_point(x_range=(0.35, 0.92), y_range=(0.22, 0.78)):
    """A random point inside the editor area. Ranges are screen fractions — keep them
    clear of the right-docked Claude panel and the bottom-docked terminal."""
    w, h = pyautogui.size()
    x = RNG.randint(int(w * x_range[0]), int(w * x_range[1]))
    y = RNG.randint(int(h * y_range[0]), int(h * y_range[1]))
    return x, y
