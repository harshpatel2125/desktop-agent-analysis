from core.module_map import module_key, parse_module_files, rotation_keys

SAMPLE = """
# Module File Map

## 1. Calendar

**Screens**
- `app/(app)/(drawer)/(tabs)/calendar/index.tsx` (153)
- `app/(app)/(drawer)/(tabs)/calendar/[calendarId]/create.tsx` (109)

**Components**
- `components/calendar/CalendarSideMenu.tsx` (42)

**Hooks**
- `hooks/api/calendar.ts` (34)

## 7. Ask Warp / AI Assistant

**Screens**
- `app/(app)/ai-assistant.tsx` (46)

**Components**
- `components/chat-ai/index.tsx` (111)

## 12. Shared / Common Components

### UI Elements (`components/ui/`)

| Commits | Component | Purpose |
|---------|-----------|---------|
| 22 | `ui/layout/CollapsibleHeader.tsx` | header |
"""


def test_module_key_slugs():
    assert module_key("Calendar") == "calendar"
    assert module_key("Ask Warp / AI Assistant") == "ask-warp"
    assert module_key("User Centre / Settings") == "user-centre"
    assert module_key("Home (Dashboard)") == "home"
    assert module_key("Chat / Messenger") == "chat"


def test_parse_extracts_only_screens_and_components():
    parsed = parse_module_files(SAMPLE)
    assert parsed["calendar"]["screens"] == [
        "app/(app)/(drawer)/(tabs)/calendar/index.tsx",
        "app/(app)/(drawer)/(tabs)/calendar/[calendarId]/create.tsx",
    ]
    assert parsed["calendar"]["components"] == ["components/calendar/CalendarSideMenu.tsx"]
    # Hooks are ignored entirely
    assert all("hooks/" not in p for p in parsed["calendar"]["components"])
    assert parsed["ask-warp"]["screens"] == ["app/(app)/ai-assistant.tsx"]


def test_shared_section_has_no_bullet_screens():
    parsed = parse_module_files(SAMPLE)
    # the table-based Shared section yields no screen/component bullets
    assert parsed["shared"] == {"screens": [], "components": []}


def test_rotation_keys_needs_screens():
    m = {"a": {"screens": ["x"], "components": []},
         "b": {"screens": [], "components": ["y"]}}
    assert rotation_keys(m) == ["a"]
