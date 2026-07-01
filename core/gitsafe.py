import subprocess

# commit/push are barred (they reach shared history / the remote). `add` (staging)
# is ALLOWED — it is local-only and is the harness's baseline mechanism: the user's
# work is staged once at startup, and harness edits are reverted back to that staged
# baseline. Nothing is ever committed or pushed.
_FORBIDDEN = {"commit", "push"}


class ForbiddenGitOp(Exception):
    pass


class GitSafe:
    def __init__(self, repo_path: str):
        self.repo = repo_path
        self._touched: set[str] = set()

    def run(self, args: list[str]) -> subprocess.CompletedProcess:
        if args and args[0] in _FORBIDDEN:
            raise ForbiddenGitOp(f"git {args[0]} is not permitted by the harness")
        return subprocess.run(
            ["git", *args], cwd=self.repo,
            capture_output=True, text=True, check=False,
        )

    def is_dirty(self) -> bool:
        out = self.run(["status", "--porcelain"]).stdout
        return bool(out.strip())

    def stage_all(self) -> None:
        """Stage every current change (`git add -A`) as the baseline the harness edits
        against. The user's work then lives in the index; reverting a harness edit
        restores the file to this staged baseline rather than to HEAD."""
        self.run(["add", "-A"])

    def file_is_clean(self, path: str) -> bool:
        """True if the working-tree file has NO unstaged changes, i.e. it matches the
        staged baseline. (Used after Cmd+Z to decide whether a git revert is needed.)"""
        out = self.run(["diff", "--", path]).stdout
        return not out.strip()

    def revert_file(self, path: str) -> subprocess.CompletedProcess:
        """Restore the working-tree file from the index (the staged baseline), undoing
        any harness edit while preserving the user's staged work for that file."""
        return self.run(["checkout", "--", path])

    def note_touched(self, path: str) -> None:
        self._touched.add(path)

    def revert_all_touched(self) -> None:
        for path in sorted(self._touched):
            self.revert_file(path)
        self._touched.clear()
