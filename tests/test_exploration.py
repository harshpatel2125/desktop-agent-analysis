import os
from core.exploration import build_project_map, ExplorationState


# Ensure os module is available for the guard test
assert os


def _touch(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("// x\n")


def test_build_map_groups_by_module_and_excludes(tmp_path):
    root = str(tmp_path / "src")
    _touch(os.path.join(root, "features", "home", "index.ts"))
    _touch(os.path.join(root, "features", "home", "components", "Card.tsx"))
    _touch(os.path.join(root, "features", "home", "utils.test.ts"))   # excluded
    _touch(os.path.join(root, "features", "home", "Card.stories.tsx"))  # excluded
    _touch(os.path.join(root, "features", "profile", "index.ts"))
    _touch(os.path.join(root, "node_modules", "junk", "a.ts"))         # excluded

    pmap = build_project_map(root)

    assert set(pmap.modules.keys()) >= {"features/home", "features/profile"}
    home = pmap.modules["features/home"]
    assert any(p.endswith("index.ts") for p in home)
    assert any(p.endswith("Card.tsx") for p in home)
    assert not any(os.path.basename(p).endswith(".test.ts") or os.path.basename(p).endswith(".stories.tsx") for p in pmap.all_files)
    assert not any("node_modules" in p for p in pmap.all_files)


def test_exploration_depth_first_finishes_module_before_next(tmp_path):
    from core.rng import RNG
    RNG.seed(42)  # Seed for deterministic ordering in this test

    root = str(tmp_path / "src")
    _touch(os.path.join(root, "features", "home", "index.ts"))
    _touch(os.path.join(root, "features", "home", "a.tsx"))
    _touch(os.path.join(root, "features", "profile", "index.ts"))
    pmap = build_project_map(root)

    state = ExplorationState(pmap)
    first = state.next_file()
    state.mark_read(first)
    second = state.next_file()
    # first two files should be from the same module
    mod_of = {p: m for m, ps in pmap.modules.items() for p in ps}
    assert mod_of[first] == mod_of[second]


def test_next_file_returns_none_when_exhausted(tmp_path):
    root = str(tmp_path / "src")
    _touch(os.path.join(root, "features", "home", "index.ts"))
    pmap = build_project_map(root)
    state = ExplorationState(pmap)
    p = state.next_file()
    state.mark_read(p)
    assert state.next_file() is None


def test_build_map_returns_absolute_paths(tmp_path):
    root = str(tmp_path / "src")   # tmp_path is absolute
    _touch(os.path.join(root, "features", "home", "index.ts"))
    pmap = build_project_map(root)
    assert pmap.all_files, "expected at least one file"
    assert all(os.path.isabs(p) for p in pmap.all_files)
    for files in pmap.modules.values():
        assert all(os.path.isabs(p) for p in files)
