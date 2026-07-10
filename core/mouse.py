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


def move_bezier(start, end, duration=0.22, steps=28):
    sx, sy = start
    ex, ey = end
    dx, dy = ex - sx, ey - sy
    dist = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / dist, dx / dist
    bow = dist * RNG.uniform(0.05, 0.2) * RNG.choice([-1, 1])
    c1 = (sx + dx * 0.3 + nx * bow, sy + dy * 0.3 + ny * bow)
    c2 = (sx + dx * 0.7 + nx * bow * RNG.uniform(0.3, 1.0),
          sy + dy * 0.7 + ny * bow * RNG.uniform(0.3, 1.0))
    # duration scales mildly with distance (Fitts-ish), but kept SNAPPY — a slow crawl
    # across the screen looked laggy. Total move ≈ 0.15-0.35s.
    duration = duration * (0.5 + min(dist / 1600.0, 0.9))
    per = duration / steps
    for i in range(1, steps + 1):
        t = ease(i / steps)
        x, y = cubic_bezier(start, c1, c2, end, t)
        pyautogui.moveTo(x, y)
        time.sleep(per)


def micro_jitter(radius=6, moves=None):
    """Small movements as if resting the hand while reading.

    A bounded random walk from the CURRENT position (not tiny hops around one fixed
    point): each step is a real displacement so it reliably registers as mouse movement
    to a presence monitor, but total drift is capped so the cursor stays put-ish and
    never wanders off across the screen. Clamped to the display bounds."""
    moves = moves if moves is not None else RNG.randint(2, 4)
    w, h = pyautogui.size()
    ox, oy = pyautogui.position()               # anchor; keep the walk near here
    x, y = ox, oy
    for _ in range(moves):
        x += RNG.randint(-radius, radius)
        y += RNG.randint(-radius, radius)
        x = min(max(x, ox - 2 * radius), ox + 2 * radius)   # cap total drift
        y = min(max(y, oy - 2 * radius), oy + 2 * radius)
        x = min(max(x, 1), w - 2)                            # stay on-screen
        y = min(max(y, 1), h - 2)
        pyautogui.moveTo(x, y)
        time.sleep(RNG.uniform(0.2, 0.8))


def editor_point(x_range=(0.35, 0.92), y_range=(0.22, 0.78)):
    """A random point inside the editor area. Ranges are screen fractions — keep them
    clear of the right-docked Claude panel and the bottom-docked terminal."""
    w, h = pyautogui.size()
    x = RNG.randint(int(w * x_range[0]), int(w * x_range[1]))
    y = RNG.randint(int(h * y_range[0]), int(h * y_range[1]))
    return x, y
