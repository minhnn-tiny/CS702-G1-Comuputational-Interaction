# User study kit

Materials for the two-part evaluation (replicating Epperson et al., CHI 2025, Section 6, with E1 as a third condition
in Part 1). Everything a facilitator needs is in this folder; the app itself is started with `../run.sh`.

| File | Purpose |
|---|---|
| `consent_form.md` | Information sheet and consent (one copy per participant, signed before the session) |
| `facilitator_script.md` | Word-for-word session script for Part 1 (3 × 15 min) and Part 2 (60 min), including the demo |
| `task_sheets.md` | What the participant sees for each task: question, expected answer, incorrect output; which recording to load |
| `questionnaires.md` | Pre-study questions, Part 1 preference questions, Part 2 Likert items and interview questions (paper's Appendix B) |
| `ground_truth/*.json` | Coded ground-truth error lists per failing recording (used to score Part 1 localisations) |
| `data/*.csv` | Data entry templates, one row per participant-task or per edit (headers only until sessions run) |
| `analyze.py` | Scores the logs and CSVs, writes `results/results.md` and figures for the final report |

## Running a session

```bash
cd term_project/prototype && ./run.sh            # backend + UI on http://127.0.0.1:8000
```

Open the UI with the participant id, condition and trial letter in the URL — opening it writes `trial_start` to
the log and is the trial's t = 0:

```
http://127.0.0.1:8000/?p=P03&cond=reduced&trial=A   # no reset/edit, no overview, no E1 cues
http://127.0.0.1:8000/?p=P03&cond=full&trial=C      # the paper's full AGDebugger feature set
http://127.0.0.1:8000/?p=P03&cond=e1&trial=B        # full + error context panel (suspects stored in the recording)
```

The condition shown is the one in the tab's URL; suspect badges, markers and the panel exist only in `e1`.

Then **Load recording…** → the recording named on the task sheet. Every API action (load, run, step, drop, send, edit,
reset, queue edit, judge) and UI event (flag, overview click/filter, suspect opened, edit-from-context, session view)
is appended to `../logs/<participant>.jsonl` with wall-clock time and seconds since the condition was set.

Participants mark an error by pressing the **⚑ flag** on a message card and typing a short note; flags are scored
automatically against the ground truth by message timestamp. Spoken localisations that were not flagged go into
`data/part1_localisation.csv`. Edits, queue edits and sent messages are logged with their full old and new text.

## After the sessions

1. Fill `data/participants.csv` (one row per participant; `condition_order` and `task_order` define the Part 1
   trials, so a trial where nothing was found still counts), `data/part1_localisation.csv` (spoken-only
   localisations and the per-trial confidence answers), `data/part2_edits.csv` (edit coding) and `data/ratings.csv`.
2. `../.venv/bin/python analyze.py` → `results/results.md` (tables used verbatim in the final report), `results/*.png`.
3. `python analyze.py --selftest` checks the pipeline on synthetic in-memory rows without writing any data files.
