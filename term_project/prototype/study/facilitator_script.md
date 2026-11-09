# Facilitator script

Two facilitators per session where possible: one runs the session, one takes notes (timestamps of spoken error
localisations, quotes). Record the screen and audio with QuickTime or OBS from the start of the demo.

## Setup (5 min before the participant arrives)

1. `cd term_project/prototype && ./run.sh`; confirm `http://127.0.0.1:8000` loads.
2. Look up the participant row in `data/participants.csv` (id, part, condition order, task order).
3. Open the first condition URL, e.g. `http://127.0.0.1:8000/?p=P03&cond=reduced`, and **Load recording…** the first
   task's recording. Keep a second tab on the plain URL for the demo.
4. Print the task sheets for the assigned tasks and one consent form.

## Welcome (5 min)

"Thanks for coming. We are evaluating a tool for debugging teams of AI agents. Please read and sign this form; you can
stop at any time." Collect the form. Ask the pre-study questions (questionnaires.md) and note the answers in
`data/participants.csv`.

## Demo (6 min, same words and the same features for every participant)

The demo always shows the **full set of features in the `e1` condition**, whatever the participant's first condition,
so that training is equal across orders. Use recording `t1_telescopes` (a short, passing run) at
`?p=<id>&cond=e1&trial=demo`:

- "An agent team is an orchestrator that plans, and three workers: a Coder, an Executor that runs code, and a
  WebSearcher with search and fetch tools. They talk by messages. Each card in the middle is one message: who sent it,
  to whom, its type and its content. Tool calls and results are messages too."
- "The flag button on a card records that you think this message is an error; type a short note."
- "The right-hand overview shows the whole run: one square per message, coloured by type, sender or recipient. Hover
  previews, click jumps. Each column is one session; editing a message forks a new column."
- "Edit & revert rewinds every agent to just before that message, applies your edit and continues in a new session.
  Reset here does the same without changes. The queue on the left shows what the agents will process next: Run, Step
  one message, or Drop it. You can also send your own message to the group or to one agent."
- "The error context panel lists up to five suspect messages ranked by a judge model, with a reason. Click one to see
  who said what to that agent, the tool calls before it, warnings, and a suggested edit. Edit this message & revert
  opens the editor there."
- "In some of your tasks only part of these features will be available; the sheet tells you which."
- Let the participant try each control once (flag, overview click, Edit & revert then Cancel, open a suspect). Answer
  questions about the interface, not about the tasks.

## Part 1 (3 × 15 min + 5 min questions)

Use the schedule in `task_sheets.md`. For each position:

1. Open the trial URL with the participant id, condition and task letter, e.g. `?p=P01&cond=reduced&trial=A`. The
   server logs `trial_start`; **start the stopwatch at the same moment**. Load the task's recording, hand over the
   sheet.
2. "You have 15 minutes. Find where this run went wrong. Flag the messages you consider errors and tell me, as you go,
   what the error is. Think aloud."
3. Note-taker: write down every spoken localisation with the stopwatch time and the message timestamp if stated; the
   flags are in the log already. Do not help; if asked whether something is an error, say "tell me what you think and
   why".
4. At 15:00 stop. Ask the three post-condition questions; write answers in `data/part1_localisation.csv`: one row per
   distinct error the participant *named but did not flag* (with the matched ground-truth id or `none`), plus one row
   per trial carrying the confidence and read-amount answers (ground_truth_id empty). Flagged messages are scored from
   the log automatically.
5. Next position: new URL (new `trial_start`), new recording, new sheet. Never reuse a tab from an earlier trial.

Matching rule for spoken localisations: a statement matches a ground-truth error when it names the same message
(timestamp) or the same mistake in the same agent's turn (e.g. "the searcher said the tables were useless" matches
E1 of Task A even without a timestamp); a statement that names a consequence only ("it kept re-planning") matches the
stall-loop error; a statement can match at most one error, the earliest it fits; repeated mentions count once.

After the third position ask the preference questions; record in `data/participants.csv` (`preference`, `ranking`).

## Part 2 (60 min)

1. Open `?p=P1x&cond=e1&trial=S`, load `t13_fy_ratio_FAIL`, hand over the Part 2 task sheet (with the error summary).
   Stopwatch starts when the URL opens.
2. "You have 30 minutes to steer the team so that the agents themselves answer 6651.7. Use anything in the tool. Say
   what you expect before each Run. A branch takes one to several minutes; you can keep reading while it runs."
3. Note-taker: for every edit, sent message or reset write the stopwatch time and a one-line description, and whether
   the participant opened the suspect panel first. The server log stores the full old and new text of every edit,
   queue edit and sent message, so coding can be done from the log.
4. Interruptions: if a model-error banner appears, say "that message was lost; use Reset here on it and Run again";
   the time keeps running. If the backend crashes, restart it, reload the recording, and record the trial as
   *interrupted* in `data/ratings.csv` notes; do not restart the clock.
5. Hard stop at 30:00. Outcome: *correct* if a branch's final orchestrator message states 6651.7 and the participant
   never typed the figure into a message; *incorrect* if the branch finished with another answer; *unfinished*
   otherwise (a branch still running at 30:00 may complete while the questionnaire starts; note its eventual result in
   the notes column, it does not change the outcome).
6. Before loading anything else, **Save recording** as `P1x_part2` so the participant's branches are kept.
7. Questionnaire (items 4–10), then the exit interview (6 questions). Record audio; transcribe the answers to
   `data/ratings.csv` and the notes file.

Edit coding (both authors independently, from the log): code each *message edit* as add / simplify / modify using the
scheme in `questionnaires.md`; a mixed edit takes the code of its dominant change (most characters changed), noted as
mixed; sends and queue edits are logged as their own kinds and not coded; plain resets are counted separately. Keep
both coders' labels in `data/part2_edits.csv` (add a column per coder) and report the number of disagreements before
adjudication.

## Closing

Thank the participant. Save the screen recording as `recordings_study/P<id>.mov` (not in git). Check that
`logs/P<id>.jsonl` exists and ends with the last action. Fill the data CSVs the same day.
