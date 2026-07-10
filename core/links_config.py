"""Load the user-editable link pools from `config/links.json`.

Kept as JSON (not a .py) because the `config/` directory can't be a Python package
without shadowing the top-level `config.py`. A missing or malformed file degrades to
empty pools rather than crashing the harness.
"""
import json
import os

_DEFAULT_TEAM_ID = "T0Y2128LE"


class LinksConfig:
    def __init__(self, slack_team_id: str, jira_urls: list, slack_links: list):
        self.slack_team_id = slack_team_id
        self.jira_urls = jira_urls
        self.slack_links = slack_links


def load_links(path: str) -> LinksConfig:
    try:
        with open(path, "r", errors="ignore") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return LinksConfig(_DEFAULT_TEAM_ID, [], [])
    return LinksConfig(
        slack_team_id=data.get("slack_team_id") or _DEFAULT_TEAM_ID,
        jira_urls=[u for u in data.get("jira_urls", []) if isinstance(u, str) and u.strip()],
        slack_links=[u for u in data.get("slack_links", []) if isinstance(u, str) and u.strip()],
    )
