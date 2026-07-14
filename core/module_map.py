"""Parse `config/module-files.md` into a per-module Screens/Components file map.

The md is the single source of truth the user maintains: sections like `## 1. Calendar`,
each with a `**Screens**` bullet list and a `**Components**` bullet list of
`` - `path` (count) `` lines. Paths are relative to the project's `src/`.

We read the md directly (no code generation) so editing the md is all the user ever does.
Only Screens and Components are extracted — Hooks/Services/Types/Contexts/Features are
deliberately ignored (the harness never opens those).
"""
import os
import re

# a module heading: "## 7. Ask Warp / AI Assistant"
_HEADING = re.compile(r"^##\s+\d+\.\s+(.*)$")
# a subsection label: "**Screens**", "**Components**", "**Hooks**", ...
_SUBSECTION = re.compile(r"^\*\*(.+?)\*\*\s*$")
# a file bullet: "- `app/(app)/.../index.tsx` (153)"
_FILE_BULLET = re.compile(r"^\s*-\s+`([^`]+)`")

# Module 12 is cross-cutting shared components — not a feature to rotate into.
_EXCLUDED_KEYS = {"shared"}

# Files shorter than this are skipped — they're re-export/stub files (e.g. a 1-line
# `chat-export.tsx`) that aren't worth "reading". Real screens/components are much longer.
_MIN_FILE_LINES = 15


def _long_enough(path: str) -> bool:
    """True if the file has at least _MIN_FILE_LINES lines (skips trivial stubs)."""
    try:
        with open(path, "r", errors="ignore") as f:
            for i, _ in enumerate(f, 1):
                if i >= _MIN_FILE_LINES:
                    return True
        return False
    except OSError:
        return False


def module_key(heading_title: str) -> str:
    """'Ask Warp / AI Assistant' -> 'ask-warp'; 'Home (Dashboard)' -> 'home'."""
    title = heading_title.split("/")[0]      # drop '/ Messenger', '/ Settings', ...
    title = title.split("(")[0]              # drop '(Dashboard)'
    return "-".join(title.strip().lower().split())


def parse_module_files(md_text: str) -> dict:
    """md text -> {key: {"screens": [rel...], "components": [rel...]}} in file order.

    Only the Screens and Components subsections are captured; any other subsection
    (Hooks, Services, Contexts, Features, tables) is skipped.
    """
    modules: dict = {}
    key = None
    bucket = None                             # "screens" | "components" | None
    for line in md_text.splitlines():
        h = _HEADING.match(line)
        if h:
            key = module_key(h.group(1))
            modules.setdefault(key, {"screens": [], "components": []})
            bucket = None
            continue
        if key is None:
            continue
        sub = _SUBSECTION.match(line)
        if sub:
            label = sub.group(1).strip().lower()
            bucket = label if label in ("screens", "components") else None
            continue
        if bucket:
            m = _FILE_BULLET.match(line)
            if m:
                modules[key][bucket].append(m.group(1).strip())
    return modules


def build_module_map(md_path: str, project_path: str) -> dict:
    """Parse the md and resolve every path to an ABSOLUTE file under `<project>/src`,
    keeping only files that actually exist. Empty and excluded (shared) modules are
    dropped. Returns {key: {"screens": [abs...], "components": [abs...]}}.
    """
    with open(md_path, "r", errors="ignore") as f:
        parsed = parse_module_files(f.read())

    src = os.path.join(project_path, "src")
    result: dict = {}
    for key, groups in parsed.items():
        if key in _EXCLUDED_KEYS:
            continue
        resolved = {"screens": [], "components": []}
        for group in ("screens", "components"):
            for rel in groups[group]:
                full = os.path.join(src, rel)
                if os.path.isfile(full) and _long_enough(full):
                    resolved[group].append(full)
        if resolved["screens"] or resolved["components"]:
            result[key] = resolved
    return result


def rotation_keys(module_map: dict) -> list:
    """Modules eligible for the 90-minute rotation: those with at least one Screen."""
    return [k for k, g in module_map.items() if g["screens"]]
