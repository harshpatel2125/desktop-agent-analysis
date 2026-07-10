"""macOS clipboard get/set via pbcopy/pbpaste — used to PASTE exact text (file paths,
URLs) instead of typing it, so shifted characters like `(` `)` `[` `]` can never be
mangled by fast synthetic keystrokes."""
import subprocess


def set_clipboard(text: str) -> None:
    subprocess.run(["pbcopy"], input=text, text=True, check=False)


def get_clipboard() -> str:
    return subprocess.run(["pbpaste"], capture_output=True, text=True, check=False).stdout
