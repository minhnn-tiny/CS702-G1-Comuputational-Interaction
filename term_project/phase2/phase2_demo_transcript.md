# Phase 2 demo video — transcript and narration script

`phase2_demo.mp4`, 3:12, silent. Every line below is a burned-in caption or title card, in order, with the time it appears. Use it as the voice-over script; captions can be read almost verbatim.

## 0:00 — Title and problem (title cards, 53 s)

- **[0:00 title card]** CS702 Computational Interaction · Term project · Phase 2 prototype. *Interactive Debugging and Steering of Multi-Agent AI Systems* — re-implementation of AGDebugger (Epperson, Bansal, Dibia, Fourney, Gerrits, Zhu and Amershi, CHI 2025, doi:10.1145/3706598.3713581). Team: Nguyen Nhat Minh, Do Duc Anh.
- **[0:09 title card] The problem.** Teams of LLM agents (an orchestrator, a coder, a code executor, a web searcher…) solve tasks by exchanging dozens of messages. One wrong step cascades, and a run of 50–90 messages ends with a wrong answer or no answer. Ordinary chat logs and print statements do not tell the developer *where* it went wrong, or let them try a fix without starting over.
- **[0:20 title card] Target users, goal and tasks.** Users: developers building and tuning multi-agent systems. Goal: find the message that derailed a run and steer the team to the correct result. Tasks: browse a long message history and step the runtime; send new messages to agents; reset the whole team to an earlier point, edit the offending message and continue; keep an overview of long runs and of the branches created by edits.
- **[0:31 title card] Prototype: three components from the paper.** C1 Message history, sending and execution control (Run / Step / Drop). C2 Reset-and-edit with session forking, on real per-message checkpoints. C3 Overview visualisation of sessions, forks and message types. Own implementation on AutoGen 0.7.5 (Python/FastAPI) + React/TypeScript. Team under debug: Magentic-One orchestrator, Coder, Executor, WebSearcher over a cached web corpus. Model under debug: Claude Haiku 5.5 (low reasoning effort); runs harvested across models and effort levels.

## 0:53 — C1 · Message history (35 s)

- Recorded failing run loaded (`t13_fy_ratio_FAIL`) — replayed from the saved history and checkpoints, no model calls.
- C1 · Message history: every runtime message as a card — sender → recipient/topic, message type, payload. Tool calls and results included.
- *(scrolling through the run)* Long payloads expand in place. Colour of the left bar = sending agent.
- After 228 messages the run ends without the answer. Expected: 6651.7 (39,910 visitors in FY 2024/25 ÷ 6 instruments).

## 1:28 — C1 · Sending and execution control (16 s)

- C1 · Sending: compose a broadcast (group topic) or a direct message to one agent; it lands in the runtime queue.
- *(typed into the compose box)* "Reminder to all agents: visitor statistics are published per calendar year with monthly tables; sum the months to get a financial-year figure." → Send to queue.
- C1 · Execution control: Run processes the queue continuously, Step processes exactly one message, Drop discards the next one.
- *(Drop clicked)* Dropped — the queue is empty again and the agents never saw the message.

## 1:44 — C3 · Overview (23 s)

- C3 · Overview: one column per session, one rectangle per message in order. Legend buttons filter.
- Colour by sender: orchestrator / Coder / Executor / WebSearcher / user.
- Colour by recipient topic or agent.
- Colour by message type — tool calls stand out from text.
- *(hovering three rectangles)* Hover shows the message; click scrolls the history to it.
- *(a rectangle clicked; history scrolls and highlights the card)*
- Legend filter dims every other message type.

## 2:07 — C2 · Reset-and-edit (24 s)

- C2 · The mistake starts at t=9: the orchestrator's own plan assumes a published "annual report or financial statements" with a financial-year total, and tells the searcher not to estimate. The observatory only publishes calendar-year monthly tables — every later instruction inherits this wrong plan.
- *(Edit & revert clicked on the t=9 plan message; the fact sheet and plan are replaced)* Edit the message in place …
- *(Save edit & revert)* Reset-and-edit: every agent's state is restored from the checkpoint taken before t=9, the edited message is re-published, and a new session (S1) forks off — the old branch stays viewable.
- *(Step clicked)* Step: the runtime processes just this one message (live model call) …

Text written into the plan message (replaces everything from "Here is an initial fact sheet to consider:" onward):

```
Here is an initial fact sheet to consider:

**1. GIVEN OR VERIFIED FACTS**

- The Lumen Valley Observatory's website is lumenvalleyobservatory.org.
- Its governance page (https://www.lumenvalleyobservatory.org/about/governance) says the financial year runs 1 April to 31 March, so FY 2024/25 is 1 April 2024 to 31 March 2025.
- Visitor statistics are published per calendar year with a monthly breakdown, in the Annual Visitor Report 2024 (https://www.lumenvalleyobservatory.org/reports/visitors-2024) and 2025 (https://www.lumenvalleyobservatory.org/reports/visitors-2025). The observatory publishes no financial-year total: the FY 2024/25 figure is the sum of the twelve monthly figures from April 2024 to March 2025, and that sum counts as the observatory's own figures.
- The Facilities page (https://www.lumenvalleyobservatory.org/facilities) lists every instrument with its commissioning year; the instruments operated on 31 March 2025 are those commissioned by then.

**2. FACTS TO LOOK UP**

- The twelve monthly visitor figures (April 2024 to March 2025) from the two reports; read each page completely, using the offset parameter.
- The instrument list with commissioning years from the Facilities page.

**3. FACTS TO DERIVE**

- FY 2024/25 visitors = sum of the twelve monthly figures.
- Instrument count on 31 March 2025 = instruments commissioned on or before that date.
- Ratio = visitors divided by instruments, rounded to one decimal place.


Here is the plan to follow as best as possible:

- **WebSearcher:** Fetch https://www.lumenvalleyobservatory.org/reports/visitors-2024 and https://www.lumenvalleyobservatory.org/reports/visitors-2025 completely and report the twelve monthly figures for April 2024 to March 2025, quoting them exactly. Then fetch https://www.lumenvalleyobservatory.org/facilities and list the instruments with their commissioning years.
- **Coder:** Write a short Python script that sums the twelve monthly figures, counts the instruments commissioned on or before 31 March 2025, divides, and rounds to one decimal place.
- **Executor:** Run the script.
- **Coder:** Report the number as the final answer, citing the two reports and the Facilities page. Do not look for an annual report or financial statements: none exists, and the monthly sum is the required figure.
```

## 2:31 — C2 · After the step (10 s)

- Step processed the edited broadcast; the orchestrator's request-to-speak now waits in the queue. Run continues the branch to completion.
- *(Run clicked; the team works live for a few minutes — cut)*

## 2:41 — C2 · Result (21 s)

- Steered branch finished. With the plan rewritten, the same team sums the monthly figures and reaches 6651.7 (expected) instead of giving up after 228 messages — the paper's "modify the plan" steering strategy.
- *(overview coloured by sender)* Overview now shows both sessions; the amber marker is the fork point. Session tabs switch between branches.
- *(session 0 tab)* The original failing branch is still browsable for comparison.

## 3:02 — Status (title card, 10 s)

- **Fully working:** instrumented runtime with per-message checkpoints, C1, C2, recordings that replay without model calls.
- **Basic:** C3 overview (plain SVG, three colour encodings, fork markers, hover, click-to-scroll).
- **Harness:** 29 tasks over a cached corpus and live Wikipedia; 97/97 Opus 5.5 runs succeeded, natural failures come from the Haiku 5.5 team.
- **Next:** more failing runs, E1 error-anchored context assembly, study instruments, pilot (Weeks 10–12).
