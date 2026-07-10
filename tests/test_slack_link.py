from core.slack_link import permalink_to_deeplink

TEAM = "T0Y2128LE"


def test_permalink_with_thread():
    url = ("https://flixpremiere.slack.com/archives/C09EE5PPLTX/p1783083953761199"
           "?thread_ts=1783080152.799599&cid=C09EE5PPLTX")
    assert permalink_to_deeplink(url, TEAM) == (
        "slack://channel?team=T0Y2128LE&id=C09EE5PPLTX"
        "&message=1783083953.761199&thread_ts=1783080152.799599")


def test_permalink_without_thread():
    url = "https://flixpremiere.slack.com/archives/C09EE5PPLTX/p1783671201721089"
    assert permalink_to_deeplink(url, TEAM) == (
        "slack://channel?team=T0Y2128LE&id=C09EE5PPLTX&message=1783671201.721089")


def test_already_deeplink_passthrough():
    deep = "slack://channel?team=T0Y2128LE&id=C1&message=1.2"
    assert permalink_to_deeplink(deep, TEAM) == deep


def test_unrecognized_returns_none():
    assert permalink_to_deeplink("https://example.com/whatever", TEAM) is None
