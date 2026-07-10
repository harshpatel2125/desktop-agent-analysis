"""Choose which file to open next within the current module.

Screens are the default, opened in priority order (most-edited first). A Component is
chosen only occasionally (`component_prob`) and always from the CURRENT module. Indices
reset when a new module period starts, so each module opens its most-used file first;
when a list is exhausted it wraps around.
"""


class FilePicker:
    def __init__(self, rng, component_prob: float = 0.30):
        self._rng = rng
        self._cp = component_prob
        self._screen_idx = 0
        self._comp_idx = 0

    def start_module(self):
        """Call when entering a new module period — restart at the most-used file."""
        self._screen_idx = 0
        self._comp_idx = 0

    def next(self, groups):
        """Return (abs_path, kind) where kind is 'screen' or 'component'. (None, None)
        if the module has no openable files."""
        screens = groups.get("screens") or []
        comps = groups.get("components") or []
        want_component = bool(comps) and (not screens or self._rng.random() < self._cp)
        if want_component:
            path = comps[self._comp_idx % len(comps)]
            self._comp_idx += 1
            return path, "component"
        if screens:
            path = screens[self._screen_idx % len(screens)]
            self._screen_idx += 1
            return path, "screen"
        return None, None
