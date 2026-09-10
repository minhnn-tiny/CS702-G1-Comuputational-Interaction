---
title: "Term Project Proposal: Interactive Debugging and Steering of Multi-Agent AI Systems"
subtitle: "CS702 Computational Interaction, AY2026-27 Term 1 — Phase 1"
---

## 1. Team members

| Name | Email |
|---|---|
| Nguyen Nhat Minh | nm.nguyen.2026@phdcs.smu.edu.sg |
| Do Duc Anh | doducanh.2026@phdcs.smu.edu.sg |

## 2. Selected paper

Will Epperson, Gagan Bansal, Victor C. Dibia, Adam Fourney, Jack Gerrits, Erkang Zhu, and Saleema Amershi. 2025. *Interactive Debugging and Steering of Multi-Agent AI Systems*. In Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems (CHI '25), Yokohama, Japan. ACM. https://doi.org/10.1145/3706598.3713581. Reference code: github.com/microsoft/agdebugger (MIT licence).

## 3. Core contribution

Teams of LLM agents fail in ways single-prompt tools cannot expose: a run produces 70–90 messages and one mistake cascades. From interviews with five agent developers the authors derive four design goals and build AGDEBUGGER, an interactive debugger with three features: (1) browsing the message history, sending new messages and stepping the queue; (2) **resetting the whole agent team to an earlier checkpoint and editing the message that caused the failure**, which forks a new session; and (3) an overview visualisation for navigating long conversations and their edits. In a two-part study with 14 participants, reset-and-edit was the highest-rated feature (4.9/5) and three steering strategies emerged: adding specific instructions, simplifying them, and modifying the agents' plan.

## 4. Architecture of the system

- **Instrumented runtime with checkpoints (substrate).** A handler on the AutoGen runtime intercepts every message, records it, and serialises every agent's state before the message is processed; execution can run, step one message, or drop one.
- **Message history and sending interface (feature 1).** Message cards with sender, recipient, type and payload; a compose panel for broadcast or direct messages; a queue panel with run and step controls.
- **Reset-and-edit (feature 2).** Editing or resetting any past message restores the checkpoint at that timestamp, forks a new session, and re-publishes the (edited) message so execution continues on a new branch.
- **Conversation overview visualisation (feature 3).** Each message is a small rectangle in one column per session, coloured by type, sender or recipient, with fork points, hover details and click-to-scroll.

A secondary agent-configuration panel went unused in the study and is read-only in the release.

## 5. Implementation scope

**Reuse policy.** We will write our own implementation of the three features (a Python backend on AutoGen pinned at 0.7.5, its last release, and a React and D3 frontend), consulting the reference code only for details the paper leaves open.

**Agent team.** Instead of the full Magentic-One team with its multimodal web surfer, we run an Orchestrator, a Coder, a sandboxed Executor and a search agent with cached results, on a low-cost hosted model at temperature 0.

- **C1. Message history, sending and execution control.** History and queue panels, broadcast and direct send, run and step, and the runtime handler that checkpoints every message.
- **C2. Reset-and-edit with session forking.** Inline edit-and-revert and the session model that keeps earlier branches viewable.
- **C3. Overview visualisation.** The linear session layout with fork markers, three colour encodings, hover details and click-to-navigate.

**Supporting infrastructure.** Four to five recorded failing runs (GAIA Level-1 style questions plus one coding task) with saved checkpoints. Error-identification tasks replay them without model calls; steering tasks restore a checkpoint and continue live.

**Enhancement E1. Error-anchored context assembly**, aligned with the paper's "automatic error identification" future work. Participants spent about ten of fifteen minutes reading before editing. One LLM-as-judge pass returns ranked suspect messages with explanations. The overview marks the suspects; clicking one assembles a context panel (the flagged message, its sender-recipient chain, and the preceding tool calls and warnings) and pre-fills the edit box at that timestamp.

**Stretch E2**, only if E1 lands by Week 11: re-run a forked session three times from one checkpoint and report pass or fail per run, answering the paper's open question "did my edit work?".

**Timeline.** Weeks 5–7: C1 and C2 end to end, a basic C3, and the harness recordings. Week 9: prototype video showing C1–C3. Weeks 10–11: E1 and polish. Week 12: pilot, then start the study. Week 13: presentation. Weeks 14–15: remaining sessions and analysis. Week 16: report.

**Risks.** Model cost (small model, recorded runs); irreversible agent actions (local, sandboxed tools); non-determinism (temperature 0, fixed recordings); a two-person team (E1 is mandatory; if time runs short we drop E2 first, then reduce E1 to its ranked-suspect markers, and trim C3 to one colour encoding).

## 6. Evaluation plan

The authors ran a two-part study with 14 developers. Part 1 (n=6, within-subjects, counterbalanced) had each participant identify errors in two recorded failing runs, one with full AGDEBUGGER and one with a reduced version lacking reset and the overview, 15 minutes each, then state a preference. Part 2 (n=8, one-hour sessions with 30 minutes of debugging) asked participants to steer a failing run to the correct answer while thinking aloud, then rate the system and each feature on five-point Likert scales; every edit was qualitatively coded.

We replicate this design with 14 SMU computing students who have used LLMs, reusing the paper's Appendix A and B instruments, with written consent; only screen recordings are collected. **Part 1 (n=6)** adds our enhancement as a third condition: reduced, full, and full plus E1, each on a different recorded failure of matched length, orders following a Latin square, 15 minutes each. Measures: errors localised against a ground-truth list we code in advance, time to the first correct localisation, and preference. **Part 2 (n=8)** replicates the steering task with all features enabled. Measures: whether the correct answer was reached (paper: two of eight), number and type of edits coded as add, simplify or modify (paper: 14/5/5), Likert ratings against the published means (helpful 4.4, backtrack-and-edit 4.9), and time before the first edit. If E2 is built, Part 2 participants may trigger it after each edit; we log its use and note in think-aloud coding whether its result changed the next edit. Comparisons with the paper are descriptive. If we cannot recruit 14, we run one 12-participant within-subjects study covering both tasks; if E1 is not ready, Part 1 reverts to the original two conditions.
