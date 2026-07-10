"""Cycle through a list with no repeat until the whole list is used, then restart at 0.

Used for the Jira / Slack link pools: every excursion takes the next link; the same URL
never repeats within a session until every other link has been used, then it starts over
from the top (per the spec).
"""


class Rotator:
    def __init__(self, items):
        self._items = list(items)
        self._i = 0

    def __len__(self):
        return len(self._items)

    def next(self):
        """Next item in order; wraps back to index 0 after the last. None if empty."""
        if not self._items:
            return None
        item = self._items[self._i % len(self._items)]
        self._i += 1
        return item
