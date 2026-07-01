import os
from dataclasses import dataclass, field

from core.rng import RNG

_EXCLUDE_SUFFIXES = (".spec.ts", ".test.ts", ".stories.tsx")
_INCLUDE_SUFFIXES = (".ts", ".tsx", ".js", ".jsx")


def _module_name(src_root: str, path: str) -> str:
    rel = os.path.relpath(path, src_root)
    parts = rel.split(os.sep)
    # group by first two path components when present (e.g. features/home)
    if len(parts) >= 3:
        return os.path.join(parts[0], parts[1])
    return parts[0]


@dataclass
class ProjectMap:
    modules: dict = field(default_factory=dict)
    all_files: list = field(default_factory=list)


def build_project_map(src_root: str) -> ProjectMap:
    pmap = ProjectMap()
    for dirpath, dirnames, filenames in os.walk(src_root):
        if "node_modules" in dirpath.split(os.sep):
            continue
        for name in filenames:
            if name.endswith(_EXCLUDE_SUFFIXES):
                continue
            if not name.endswith(_INCLUDE_SUFFIXES):
                continue
            full = os.path.join(dirpath, name)
            pmap.all_files.append(full)
            mod = _module_name(src_root, full)
            pmap.modules.setdefault(mod, []).append(full)
    return pmap


class ExplorationState:
    """Depth-first: exhaust one module's files before moving to another."""

    def __init__(self, pmap: ProjectMap):
        self._pmap = pmap
        self._read: set = set()
        self._current_module: str | None = None

    def _module_of(self, path: str) -> str:
        for m, files in self._pmap.modules.items():
            if path in files:
                return m
        return ""

    def _unread_in(self, module: str):
        return [p for p in self._pmap.modules.get(module, []) if p not in self._read]

    def next_file(self):
        # stay in the current module while it has unread files
        if self._current_module and self._unread_in(self._current_module):
            return RNG.choice(self._unread_in(self._current_module))
        # otherwise pick a new module that still has unread files
        candidates = [m for m in self._pmap.modules if self._unread_in(m)]
        if not candidates:
            return None
        self._current_module = RNG.choice(candidates)
        return RNG.choice(self._unread_in(self._current_module))

    def mark_read(self, path: str) -> None:
        self._read.add(path)
        self._current_module = self._module_of(path)
