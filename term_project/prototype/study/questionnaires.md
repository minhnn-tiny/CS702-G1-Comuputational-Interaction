# Questionnaires and interview guides

Items marked (paper) are taken verbatim from Appendix B of Epperson et al. (CHI 2025) so that means can be compared.

## Pre-study (all participants)

1. How much experience do you have developing AI agents? (5-point: 1 none … 5 extensive) (paper)
2. Do you have prior experience using AutoGen or AgentChat? (Yes / No) (paper, "autogen or agnext")
3. Do you have prior experience with the GAIA benchmark? (Yes / No) (paper)
4. How often do you use LLM chat tools? (daily / weekly / monthly / rarely)
5. Programme and year (e.g. MSc CS, year 1)

## Part 1 — after each condition (15-minute task)

Recorded by the facilitator from the participant's spoken summary; the participant also flags messages in the tool.

1. Where did the run go wrong? List the messages (by timestamp) and say what the error was. (open)
2. How confident are you that you found the main cause? (1 not at all … 5 very confident)
3. How much of the run did you feel you had to read? (1 almost none … 5 all of it)

## Part 1 — after all three conditions

1. Which version did you prefer for finding errors: reduced, full, or full with suspects? Why? (paper: preference between full and reduced)
2. Rank the three versions from most to least helpful.
3. (full with suspects only) Did the suspects help, mislead, or make no difference? Give an example.

## Part 2 — post-task survey (paper, Appendix B; 5-point Likert, 1 strongly disagree … 5 strongly agree)

4. I found this system helpful.
5. I found this system easy to use.
6. I would like to use this system again in the future.
7. Rate how much you found this feature helpful: Sending new messages.
8. Rate how much you found this feature helpful: Backtracking to previously sent messages and editing.
9. Rate how much you found this feature helpful: Conversation overview visualization.
10. Rate how much you found this feature helpful: Error context panel (suspects and context). *(our addition)*

Paper means for comparison: helpful 4.4, easy to use 4.0, use again 4.6, send 4.1, backtrack-and-edit 4.9, overview 4.1.

## Part 2 — exit interview (paper, Appendix B)

1. (If did not steer to right answer) Given more time, do you think you would have been able to steer the models to output the correct answer?
2. Can you describe your approach to the task, how did you try to intervene?
3. After intervention, how has your opinion about which issues are the most actionable changed?
4. How did you feel that having the ability to edit messages and configuration influenced your understanding of the agents' errors?
5. What other ways would you have liked to steer the models?
6. *(ours)* Did the suspect list change where you made your first edit? Did you ever disagree with it?

## Edit coding scheme (Part 2, applied by both researchers independently, disagreements resolved by discussion)

| Code | Definition (paper, Section 6.4) | Example |
|---|---|---|
| add | adds more specific instructions or makes an instruction more concrete | "fetch both reports completely, use the offset parameter" |
| simplify | removes text, narrows the instruction to a sub-task | drops the second half of a compound instruction |
| modify | changes the goal or the plan itself | "use code to sum the monthly table instead of searching for a total" |

Also recorded per edit: timestamp edited, sender of the edited message, whether it was a judge suspect, session
outcome (correct / incorrect / unfinished at 30 min). A mixed edit takes the code of its dominant change and is marked
mixed; sends and queue edits are not coded; plain resets are counted separately.

## Interview coding

Open-response answers are transcribed and coded inductively by both authors: first pass independently (one label per
statement, labels proposed freely), then a merged codebook, then a second pass with the merged codebook; disagreements
are resolved by discussion and counted. Themes reported in the paper (counterfactual testing, "did my edit work",
over-complex instructions) are used as seed codes so that overlap and differences with the paper can be stated.
