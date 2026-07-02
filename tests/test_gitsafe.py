import subprocess
import pytest
from core.gitsafe import GitSafe, ForbiddenGitOp


def _init_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "t@t.t"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=repo, check=True)
    f = repo / "a.txt"
    f.write_text("original\n")
    subprocess.run(["git", "add", "a.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "init"], cwd=repo, check=True)
    return repo, f


def test_commit_and_push_forbidden(tmp_path):
    repo, _ = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    for bad in (["commit", "-m", "x"], ["push"]):
        with pytest.raises(ForbiddenGitOp):
            gs.run(bad)


def test_add_is_allowed(tmp_path):
    # staging is local-only and is the baseline mechanism — it must NOT raise
    repo, f = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    f.write_text("changed\n")
    gs.run(["add", "-A"])  # should not raise
    # confirmed staged: an unstaged diff is now empty, a staged diff is not
    assert gs.run(["diff", "--", "a.txt"]).stdout.strip() == ""
    assert gs.run(["diff", "--cached", "--", "a.txt"]).stdout.strip() != ""


def test_file_is_clean_detects_unstaged_change(tmp_path):
    repo, f = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    assert gs.file_is_clean("a.txt") is True
    f.write_text("changed\n")
    assert gs.file_is_clean("a.txt") is False


def test_stage_all_makes_file_clean_vs_baseline(tmp_path):
    repo, f = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    f.write_text("user-work\n")
    assert gs.file_is_clean("a.txt") is False   # unstaged change present
    gs.stage_all()
    assert gs.file_is_clean("a.txt") is True     # working tree now matches the index


def test_revert_restores_to_staged_baseline_not_head(tmp_path):
    # THE KEY new-model behavior: the user's staged work is the floor, not HEAD.
    repo, f = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    f.write_text("user-work\n")
    gs.stage_all()                 # baseline = "user-work" in the index
    f.write_text("blackpearl-edit\n")  # blackpearl edits on top (unstaged)
    gs.revert_file("a.txt")
    assert f.read_text() == "user-work\n"   # restored to the user's staged work, NOT "original"
    assert gs.file_is_clean("a.txt") is True


def test_revert_file_restores_when_nothing_staged(tmp_path):
    repo, f = _init_repo(tmp_path)
    gs = GitSafe(str(repo))
    f.write_text("blackpearl-edit\n")   # unstaged, nothing staged -> index == HEAD
    gs.revert_file("a.txt")
    assert f.read_text() == "original\n"


def test_revert_all_touched_only_touches_tracked(tmp_path):
    repo, f = _init_repo(tmp_path)
    other = repo / "b.txt"
    other.write_text("original-b\n")
    subprocess.run(["git", "add", "b.txt"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-qm", "b"], cwd=repo, check=True)
    gs = GitSafe(str(repo))
    f.write_text("blackpearl-edit\n")
    other.write_text("user-edit-b\n")   # NOT tracked by the blackpearl
    gs.note_touched("a.txt")
    gs.revert_all_touched()
    assert f.read_text() == "original\n"          # reverted
    assert other.read_text() == "user-edit-b\n"   # left alone
