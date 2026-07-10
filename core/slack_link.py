"""Convert a Slack message permalink into a `slack://` desktop-app deep link.

A permalink like
    https://flixpremiere.slack.com/archives/C09EE5PPLTX/p1783083953761199?thread_ts=1783080152.799599
carries the channel id (`C09EE5PPLTX`) and the message ts encoded as `p<digits>`
(`p1783083953761199` -> `1783083953.761199`), plus an optional `thread_ts`. The desktop
app opens a specific message via
    slack://channel?team=<TEAM_ID>&id=<CHANNEL>&message=<TS>[&thread_ts=<TT>]
which `open`-ing launches straight in Slack with no browser tab. The team id is not in the
permalink, so it's supplied by config (default auto-detected).
"""
import re

_ARCHIVE = re.compile(r"/archives/([A-Z0-9]+)/p(\d+)")
_THREAD = re.compile(r"[?&]thread_ts=([0-9.]+)")


def permalink_to_deeplink(url: str, team_id: str):
    """Return a `slack://channel?...` deep link, or None if `url` isn't a recognizable
    message permalink. An already-`slack://` url is returned unchanged."""
    if url.startswith("slack://"):
        return url
    m = _ARCHIVE.search(url)
    if not m:
        return None
    channel, p = m.group(1), m.group(2)
    if len(p) <= 6:
        return None
    ts = f"{p[:-6]}.{p[-6:]}"                 # p1783083953761199 -> 1783083953.761199
    deep = f"slack://channel?team={team_id}&id={channel}&message={ts}"
    thread = _THREAD.search(url)
    if thread:
        deep += f"&thread_ts={thread.group(1)}"
    return deep
