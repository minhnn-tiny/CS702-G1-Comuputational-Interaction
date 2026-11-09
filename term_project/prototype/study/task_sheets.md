# Task sheets

Participant-facing sheets are the boxed parts; everything under **Facilitator** stays with the facilitator. Each
sheet mirrors what the paper gave its participants: the task, the expected output, the incorrect output.

The three Part 1 recordings are natural failures of the same Claude Haiku team, 224–233 runtime messages each
(119–134 visible cards). Tasks A and B are two runs of the same corpus question; Task C is a live-Wikipedia question.
Because A and B share a question, the schedule below never gives a participant A and B in consecutive positions with
the same condition, and the analysis reports condition × task cells and position effects.

## Assignment schedule (Part 1, n = 6)

Every condition meets every task twice; every condition appears in every position twice; A and B are separated by C
for four of six participants.

| Participant | Position 1 | Position 2 | Position 3 |
|---|---|---|---|
| P01 | reduced / A | full / C | e1 / B |
| P02 | full / B | e1 / A | reduced / C |
| P03 | e1 / C | reduced / B | full / A |
| P04 | reduced / B | e1 / C | full / A |
| P05 | full / C | reduced / A | e1 / B |
| P06 | e1 / A | full / B | reduced / C |

Enter the same strings in `data/participants.csv` (`condition_order`, `task_order`), e.g. `reduced,full,e1` and
`A,C,B` for P01. URLs: `?p=P01&cond=reduced&trial=A`, then `?p=P01&cond=full&trial=C`, then `?p=P01&cond=e1&trial=B`.
Opening the URL is the trial's t = 0 in the log; start the stopwatch at the same moment.

---

> ## Task A
>
> **The agents were asked:** Using the Lumen Valley Observatory's own figures, compute the number of visitors admitted
> in its financial year 2024/25 divided by the number of instruments it operated on the last day of that financial
> year. Reply with the result rounded to one decimal place.
>
> **Correct answer:** 6651.7
>
> **What the agents produced:** after 228 messages the orchestrator wrote that no number could be produced and that
> "no source was actually checked".
>
> **Your job (15 minutes):** find where this run went wrong. Flag every message you consider an error (⚑ on the card,
> short note) and tell us, thinking aloud, what the error is. You do not need to fix anything.

**Facilitator:** recording `t13_fy_ratio_FAIL`. Ground truth: `ground_truth/t13_fy_ratio_FAIL.json` (primary errors
t=23 searcher reports the monthly tables as unusable; t=25 orchestrator forbids calendar-year figures). The answer
comes from summing the twelve monthly figures in the two Annual Visitor Reports and dividing by the six instruments on
the Facilities page.

---

> ## Task B
>
> **The agents were asked:** Using the Lumen Valley Observatory's own figures, compute the number of visitors admitted
> in its financial year 2024/25 divided by the number of instruments it operated on the last day of that financial
> year. Reply with the result rounded to one decimal place.
>
> **Correct answer:** 6651.7
>
> **What the agents produced:** after 233 messages the orchestrator wrote that the figure could not be determined from
> the observatory's own data. This is a different run of the team from any you may have seen: read it on its own.
>
> **Your job (15 minutes):** find where this run went wrong. Flag every message you consider an error (⚑ on the card,
> short note) and tell us, thinking aloud, what the error is. You do not need to fix anything.

**Facilitator:** recording `t13_fy_ratio_FAIL_2`. Ground truth: `ground_truth/t13_fy_ratio_FAIL_2.json` (primary
errors t=36 orchestrator rejects a correct derivation; t=47 orchestrator tells the Coder not to present 6651.7).

---

> ## Task C
>
> **The agents were asked:** In the English Wikipedia article 'List of countries and dependencies by area', what rank
> is Mongolia given? Reply with just the number.
>
> **Correct answer:** 18
>
> **What the agents produced:** after 224 messages the orchestrator answered "my best estimate from memory is 19".
>
> **Your job (15 minutes):** find where this run went wrong. Flag every message you consider an error (⚑ on the card,
> short note) and tell us, thinking aloud, what the error is. You do not need to fix anything.

**Facilitator:** recording `wt2_mongolia_rank_FAIL`. Ground truth: `ground_truth/wt2_mongolia_rank_FAIL.json`. Do not
tell the participant that the fetch tool returns article text without tables, or that the Mongolia article states
"18th-largest"; both are things to discover from the messages (t=15 shows table-less text, t=34 shows the Mongolia
article). If asked what the tools can do, answer only "what you can see in their results".

---

> ## Part 2 · Steering task
>
> **The agents were asked:** Using the Lumen Valley Observatory's own figures, compute the number of visitors admitted
> in its financial year 2024/25 divided by the number of instruments it operated on the last day of that financial
> year. Reply with the result rounded to one decimal place.
>
> **Correct answer:** 6651.7
>
> **What the agents produced:** no answer after 228 messages.
>
> **Summary of errors found in Part 1 (given to you, as in the paper's protocol):** the searcher reported the monthly
> visitor tables as unusable; the orchestrator then forbade using calendar-year figures, chased annual accounts that do
> not exist, and re-planned without instructing any agent.
>
> **Your job (30 minutes):** steer the team so that *the agents themselves* answer 6651.7. You may edit any message
> and revert to it, send new messages, step or run the queue, and use the suspect panel. Each run continues live (the
> agents call a real model), so a branch takes one to several minutes to finish. Think aloud: say what you expect
> before you press Run. Typing the answer into a message yourself does not count.

**Facilitator:** recording `t13_fy_ratio_FAIL`, URL `?p=P1x&cond=e1&trial=S`. Success = the orchestrator's final
message in a branch states 6651.7 (hedged wording still counts, as in our harness grader) and the participant did not
write the figure into any message. Hard stop at 30:00: a branch still running at 30:00 is recorded as *unfinished*
(let it run while the questionnaire starts and note its eventual outcome separately).
