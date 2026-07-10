# Blackpearl — Schedule Redesign (confirmed spec)

**Status:** CONFIRMED — building against this. Decisions locked (2026-07-10):

- **Slack links → Slack desktop app** (deep-link to focus the message), not a browser tab.
- **Single `--module:x`** → do `x` for the first 90 min, then **random** modules after.
- **Occasional Component** → always from the **current** module only.
- **Cursor during a Jira/Slack excursion** → **keeps moving** (major move ~every 30 s, no
  clicks) so the machine is never idle for 6 min.
- Cycle = **20 min VS Code + 6 min excursion** (26 min). File holds **6 + 14 min** (order
  random). **Hooks/Services/Types/Contexts never opened** — Screens default, Components 1–2×/hr.
- **Pause model:** the schedule runs on *active time* — while you've taken over (auto-pause),
  the clock **freezes** and resumes where it left off, so the wall-clock times below shift
  later by however long you were active. The structure (order, durations) is preserved.
- **Slack opening mechanism (resolved):** you paste normal message permalinks into
  `config/links.py`; at runtime I parse `channel` + `message ts` (+ `thread_ts`) and build a
  `slack://channel?team=T0Y2128LE&id=<CH>&message=<TS>[&thread_ts=<TT>]` deep link, then
  `open` it — opens straight in the Slack desktop app, no browser tab. Team id defaults to
  `T0Y2128LE` (flixpremiere, auto-detected) and is overridable in `config/links.py`.
- **NO terminal actions at all (removed per your request):** no iOS build (cd ios / pod
  install / pnpm ios), no `npm i` / `npm i -f`, no backend repo (`warp-speed-ai-backend`)
  open or `git pull`, no Metro (`pnpm start`). The simulator only: opens the VS Code project,
  reads Screens/Components, takes Jira/Slack/Claude excursions. `actions/terminal.py` and the
  build/install/backend timers are dropped from the loop.

*(Original understanding + open questions preserved below for reference.)*

---

## 1. The big picture

Right now blackpearl indexes *every* file under `src/` and opens them randomly. You want
the opposite: **stay inside ONE feature/module for 1.5 hours**, opening only that
feature's real high-churn files (calendar, emails, notes, tasks, chat, ask-warp, …), and
only *very rarely* peek at another feature. After 1.5 hours it switches to the next
module. No layout / architecture / rarely-used files ever.

Three "surfaces" as before, but on a **fixed clock** now:
- **VS Code** = home base (reading the current module's files + Claude time).
- **Jira** (Chrome tab) and **Slack** (message link) = short 6-minute excursions,
  **just open, no actions**, alternating every cycle.

---

## 2. The timing model (the heart of it)

| Thing | Value |
|---|---|
| VS Code work window | **20 min** |
| Jira/Slack excursion | **6 min** (open only, no clicks/scroll) |
| → one full cycle | **26 min** (20 + 6) |
| Excursions alternate | Jira → Slack → Jira → Slack … (Jira first) |
| Module (feature) period | **90 min (1.5 h)**, then switch to next module |
| Major cursor move | **every 30 s**, always (even during excursions) |

**VS Code windows alternate by parity** (counting each return-to-VS-Code):
- **Odd windows (1st, 3rd, 5th …) = FILE reading.** Open **2 files**. One is held ~**6 min**,
  the other ~**14 min** (6+14 or 14+6, chosen at random each window). During the long
  hold, scroll the file down to the middle / near the bottom.
- **Even windows (2nd, 4th, 6th …) = CLAUDE time.** Open **1 file** (keeps the file count
  going), then move to the Claude panel (right side, ~30% width). Scroll the current
  Claude chat for ~6 min, then **switch to another Claude chat** from history and keep
  scrolling for the rest of the window.

**Which files, within a module** (source: `config/module-files.md`):
- **Screens are the default.** Opened in the md's priority order (most-edited first).
- **Components: only ~1–2 times per hour.** The rest of the time it's Screens. (Given the
  long 6/14-min holds, only ~3–4 files open per hour, so 1–2 of those being a Component
  matches "mostly screens.")
- **Hooks / Services / Types / Contexts: never opened** (unless you tell me otherwise).
- When a module's Screens list runs out inside its 90-min period, it revisits from the top.
- Paths in the md are relative to `src/` (e.g. `app/(app)/.../calendar/index.tsx` →
  `<project>/src/app/(app)/.../calendar/index.tsx`). I verify each exists before opening.

---

## 3. Module selection & the `--module` flag

- **No flag** → pick a **random** module to start, then switch to another random module
  every 90 min (never the same one twice in a row).
- **`blackpearl --module:emails`** → start with **emails** for the first 90 min, then
  continue (random for the rest).
- **`blackpearl --module:emails,calendar,contacts`** → follow that **exact sequence**,
  one module per 90 min, cycling: emails → calendar → contacts → emails → …

The module only decides *which files* the VS Code windows open. It does not change the
20/6 cycle or the Jira/Slack rhythm.

---

## 4. Jira / Slack links — rotation with no repeats

A single config file holds arrays of links. Each excursion takes the **next** link:
- **No URL repeats within one session.** When every Jira (or Slack) link has been used,
  it starts over from index 0.
- **Jira** links open as a **new Chrome tab** (I confirm Chrome is frontmost first, then
  paste the URL — the fix I already made).
- **Slack** links are **message permalinks** — open the specific message, not just the app.
  *(Need your confirmation on browser vs. Slack desktop app — see Open questions.)*

---

## 5. Config: two files, you only edit these

**(a) `config/module-files.md`** — already exists, you maintain it. This is the single
source of truth for module → Screens / Components. I read it directly at runtime and
parse the `**Screens**` and `**Components**` lists per `## N. Module` section, so you
never regenerate anything — just edit the md. Module keys come from the headings:
`calendar, chat, emails, notes, tasks, home, ask-warp, contacts, integrations,
user-centre, auth` (module 12 "Shared" is not a rotation target).

**(b) `config/links.py`** — new, tiny, you fill in the two arrays:

```python
# Jira URLs — rotated, no repeat per session; restart at 0 when exhausted.
JIRA_URLS = [
    "https://flixpremiere.atlassian.net/browse/WS-123",
    "https://flixpremiere.atlassian.net/browse/WS-456",
    # ...
]

# Slack message permalinks — rotated, no repeat per session.
SLACK_LINKS = [
    "https://<workspace>.slack.com/archives/C0XXXX/p1699999999000000",
    # ...
]
```

The `--module:` flag is a command-line argument (nothing to configure in a file).

---

## 6. Full minute-by-minute example — 3.5 hours

Assumptions for this example: you start at **8:00 PM**, give **no `--module` flag**, so it
randomly picks **Calendar** first, then (random) **Emails**, then **Tasks**. Cursor makes a
major move every 30 s throughout (not listed row-by-row). "Cal#1" = the top-priority
calendar file, etc.

| Time | Phase | What happens |
|---|---|---|
| 8:00 | **W1 · files · Calendar** | Open **Cal#1**, hold 6 min |
| 8:06 | W1 | Open **Cal#2**, hold 14 min; scroll to mid/bottom |
| **8:20** | **Excursion 1 · JIRA** | Open **Jira link #1** in a new Chrome tab; no actions |
| 8:26 | back → **W2 · Claude · Calendar** | Open **Cal#3**, then focus Claude panel; scroll current chat |
| 8:32 | W2 | Switch to another Claude chat; keep scrolling |
| **8:46** | **Excursion 2 · SLACK** | Open **Slack link #1** (message); no actions |
| 8:52 | back → **W3 · files · Calendar** | Open **Cal#4**, hold 14 min (reversed split); scroll |
| 9:06 | W3 | Open **Cal#5**, hold 6 min |
| **9:12** | **Excursion 3 · JIRA** | Open **Jira link #2** |
| 9:18 | back → **W4 · Claude · Calendar** | Open **Cal#6**, focus Claude; scroll |
| 9:24 | W4 | Switch Claude chat; keep scrolling |
| **9:30** | **MODULE SWITCH → Emails** | (time-based; takes effect at the next file open, W5) |
| **9:38** | **Excursion 4 · SLACK** | Open **Slack link #2** |
| 9:44 | back → **W5 · files · Emails** | Open **Email#1** (draft.tsx), hold 6 min |
| 9:50 | W5 | Open **Email#2** (EmailBodyEditor), hold 14 min; scroll |
| **10:04** | **Excursion 5 · JIRA** | Open **Jira link #3** |
| 10:10 | back → **W6 · Claude · Emails** | Open **Email#3**, focus Claude; scroll |
| 10:16 | W6 | Switch Claude chat; scroll |
| **10:30** | **Excursion 6 · SLACK** | Open **Slack link #3** |
| 10:36 | back → **W7 · files · Emails** | Open **Email#4**, hold 14 min; scroll |
| 10:50 | W7 | Open **Email#5**, hold 6 min |
| **10:56** | **Excursion 7 · JIRA** | Open **Jira link #4** |
| **11:00** | **MODULE SWITCH → Tasks** | (takes effect at next file open, W8) |
| 11:02 | back → **W8 · Claude · Tasks** | Open **Task#1** (create-task), focus Claude; scroll |
| 11:08 | W8 | Switch Claude chat; scroll |
| **11:22** | **Excursion 8 · SLACK** | Open **Slack link #4** |
| 11:28 | back → **W9 · files · Tasks** | Open **Task#2**, begin its hold |
| 11:30 | — | (3.5 h mark; loop continues the same way) |

**Recap of the rhythm:** every **26 min** = 20 min in VS Code + a 6-min Jira/Slack peek.
VS Code windows alternate **files → Claude → files → Claude**. Excursions alternate
**Jira → Slack**. Every **90 min** the feature switches. The cursor never sits still
longer than ~30 s.

---

## 7. Open questions (please answer so I build it exactly right)

1. **Cycle timing:** is "20 min VS Code + 6 min excursion = 26-min cycle" correct?
   Your own example (8:20 Jira → 8:26 back → 8:46 Slack) matches this. Confirm?
2. **Slack links (important for how I build it):** open the message permalink in **Chrome**
   (browser tab), or deep-link into the **Slack desktop app** to focus that message?
   A Slack permalink can do either; I need to know which you want.
3. **Components rate:** "1–2 per hour" — I'll target that (roughly 1 in 3 file opens is a
   Component, rest Screens). Good? And should a Component ever come from a *different*
   module, or always the current module's Components? (My default: current module only.)
4. **Cursor "major move" every 30 s:** a real move across the editor (bezier to a new
   spot), not just tiny jitter — correct? And during the 6-min Jira/Slack excursion, keep
   the cursor moving (movement only, no clicks) so it isn't idle for 6 min — correct?
5. **File hold split:** 6 min + 14 min per files-window, randomly giving the 14-min hold to
   either the 1st or 2nd file — correct?
6. **When `--module:emails` (single) finishes its 90 min:** continue with **random**
   modules after, or repeat emails forever? (My default: emails first, then random.)
7. **Hooks / Services / Types / Contexts:** confirm these are never opened — Screens +
   occasional Components only.

*(Resolved: module→files source is `config/module-files.md`; Screens are the default.)*
