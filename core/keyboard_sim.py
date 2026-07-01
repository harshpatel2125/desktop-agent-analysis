import time

import pyautogui

from core.rng import RNG

_PUNCT = set(".,;:!?)( []{}")


def key_delay(prev_char, ch) -> float:
    base = RNG.uniform(0.05, 0.13)
    if prev_char is None:
        return base
    if prev_char in _PUNCT or prev_char == " ":
        base += RNG.uniform(0.10, 0.35)  # thinking pause after punctuation/space
    return base


def type_text(text: str, typo_rate: float = 0.03) -> None:
    prev = None
    for ch in text:
        # occasional typo: type a wrong neighbor char, then correct it
        if ch.isalpha() and RNG.random() < typo_rate:
            wrong = RNG.choice("asdfghjkl")
            pyautogui.typewrite(wrong)
            time.sleep(key_delay(prev, wrong))
            pyautogui.press("backspace")
            time.sleep(RNG.uniform(0.1, 0.25))
        pyautogui.typewrite(ch)
        time.sleep(key_delay(prev, ch))
        prev = ch
        # rare mid-typing "thinking" pause
        if RNG.random() < 0.02:
            time.sleep(RNG.uniform(0.6, 1.8))
