# Phase 3 live demo — runbook (4–5 minutes)

Rehearse once on the presentation machine the day before. The whole demo uses one recorded failing run
(`t13_fy_ratio_FAIL`, 228 runtime messages, 125 shown as cards, Claude Haiku team) and makes live model calls only in
the Step scene after the edit (needs API credits; the fallback below needs none).

## Before class

```bash
cd term_project/prototype
./run.sh --build             # rebuild the UI from source, then serve http://127.0.0.1:8000
```

- Check `ANTHROPIC_API_KEY` is in the repo-root `.env` and that the account has credits (only the Step scene needs
  them; everything else is offline). Test one Step the day before.
- Open two browser tabs, 1600 px wide or wider, browser zoom 110–125 % for the projector:
  - Tab A: `http://127.0.0.1:8000/?cond=full`
  - Tab B: `http://127.0.0.1:8000/?cond=e1`
  The condition is read from each tab's URL, so the two tabs show different feature sets of the same backend state.
- In Tab A choose **Load recording… → t13_fy_ratio_FAIL**. Tab B shows the same recording.
- Backup: `phase3_demo_backup_narrated.mp4` (5 min, narrated) in this folder; play it if the backend is down.
- Fallback for the live Step (no network or no credits): skip it and load `t13_fy_ratio_STEERED_E1` to show the
  finished branch, saying that it was saved from a live continuation of this same edit.

## Script

| Time | Tab | Do | Say |
|---|---|---|---|
| 0:00 | A | Point at the task line and the session tab "session 0 (live), 125 messages". | The team was asked for financial-year visitors divided by instruments. Expected 6651.7. After 228 runtime messages, 125 of them shown here, it gave up. |
| 0:20 | A | Scroll the history slowly; expand one tool-call card with *show more*. | C1: every runtime message is a card — sender, recipient, type, payload, tool calls. Reading 228 of these is the paper's problem. |
| 0:45 | A | Compose: type *Text message*, To *group*, content "Reminder: visitor statistics are monthly tables; sum the months." → **Send to queue**. Click **✎** on the queued item, append a sentence, **Save**. Then **Drop**. | Sending and execution control: Run, Step, Drop. New since the prototype: edit or remove a queued message before the agents see it. |
| 1:20 | A | Overview: switch colour to *sender*, then *type*; hover three rectangles; click one near the middle; click a legend entry to filter and unfilter. | C3: one column per session, one rectangle per message. Click navigates the history. |
| 1:50 | B | Show the **Error context** panel with the five suspects already listed (precomputed). Hover suspect #1 in the panel; point at the `#1…#5` markers in the overview and the red badges on cards. | E1: one judge pass ranks up to five suspect messages with reasons. In the paper participants spent ten of fifteen minutes reading before editing; this is the shortcut. |
| 2:20 | B | Click suspect **#2 (t=25, wrong plan)**. Scroll the panel: chain, tool calls, warnings, evidence, suggested edit. | Context assembly: who told this agent what, what it did, what went wrong, and what to change. |
| 2:50 | B | Click **✎ Edit this message & revert**. Replace the text with the prepared instruction (`prototype/recordings/harvest_logs/_edit25.txt`, or paste from the slide notes). **Save edit & revert**. | C2: restore every agent from the checkpoint before t=25, re-publish the edited instruction, fork session 1. The old branch stays. |
| 3:30 | B | Click **Step** twice: the first processes the edited broadcast (instant), the second the orchestrator's request-to-speak, which calls the model (~10–20 s). Show the new tool calls in session 1. | Two queued messages, one live model call: the WebSearcher now follows the edited instruction. |
| 4:00 | B | **Load recording… → t13_fy_ratio_STEERED_E1**. Scroll to the end: 6651.7. Overview: two columns, fork marker. Click *session 0*. | The finished branch, saved from a live continuation of this edit. Same team, one edit, correct answer. |
| 4:30 | B | Change the URL to `?p=P1&cond=reduced` → no overview, no edit buttons. | Study mode: three conditions from the URL, every action logged per participant. |

## Prepared edit text (t=25)

Please fetch https://www.lumenvalleyobservatory.org/reports/visitors-2024 and
https://www.lumenvalleyobservatory.org/reports/visitors-2025 completely (keep calling fetch_page with the offset given
at the end of each chunk until the page ends) and report the twelve monthly visitor figures for April 2024 to March 2025
exactly as printed, with the URL each came from. Then fetch https://www.lumenvalleyobservatory.org/facilities and list
every instrument with its commissioning year. The observatory publishes no financial-year total: do not look for annual
accounts or financial statements; the monthly tables are the observatory's own figures and summing them is the required
method.

## If something breaks

- Model-error banner (e.g. credits exhausted) → the message that failed was consumed; say so, skip to the fallback
  recording. Do not retry on stage.
- Nothing happens after the first **Step** → expected: that step only delivered the broadcast; press **Step** again.
- **Stop** keeps the queue: after Stop, Step or Run resumes the same branch.
- Browser shows "Backend not reachable" → restart `./run.sh`; the recordings are on disk, nothing is lost.
