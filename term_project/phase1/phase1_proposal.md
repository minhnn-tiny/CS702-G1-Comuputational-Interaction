---
title: "Term Project Proposal: Interactive Debugging and Steering of Multi-Agent AI Systems"
subtitle: "CS702 Computational Interaction, AY2026-27 Term 1 — Phase 1"
---

## 1. Team members

| Name | Email |
|---|---|
| Nguyen Nhat Minh | nm.nguyen.2026@smu.edu.sg |
| Koti Sampath | <email> |
| Do Duc Anh | <email> |

## 2. Selected paper

Will Epperson, Gagan Bansal, Victor C. Dibia, Adam Fourney, Jack Gerrits, Erkang Zhu, and Saleema Amershi. 2025. *Interactive Debugging and Steering of Multi-Agent AI Systems*. In Proceedings of the 2025 CHI Conference on Human Factors in Computing Systems (CHI '25), Yokohama, Japan. ACM, 15 pages. https://doi.org/10.1145/3706598.3713581. Source code: `github.com/microsoft/agdebugger` (MIT licence).

## 3. Core contribution

Teams of LLM agents fail in ways that single-prompt tools cannot expose: errors are buried in 70–90 message conversations and one agent's mistake cascades into another's. From interviews with five agent developers the authors derive four design goals and build AGDEBUGGER, an interactive debugger that lets a developer pause and step the agent message queue, inject messages, **reset the whole agent team to a checkpoint and edit the message that caused a failure**, and navigate the history through an overview visualisation. A two-part study with 14 participants found reset-and-edit the most valued feature (4.9/5) and identified three recurring steering strategies: adding more specific instructions, simplifying instructions, and modifying the agents' plan.

## 4. Architecture of the system

- **Instrumented agent runtime.** An intervention handler wrapped around the AutoGen single-threaded runtime intercepts every message, timestamps it into a history, and exposes queue control (run, step one message, drop).
- **Checkpoint and session forking.** Each agent serialises its state before every message is processed; a reset restores that checkpoint, forks a new "session", and re-publishes the (optionally edited) message so execution continues on a new branch.
- **Message history and sending interface.** Browsable message cards with sender, recipient, type and payload; inline edit-and-revert on any past message; a compose panel for broadcast or direct messages.
- **Conversation overview visualisation.** Every message is a small rectangle in a vertical column, one column per session, coloured by type, sender or recipient, with fork points marked, hover details, and click-to-scroll into the history.
- **Agent configuration panel.** Cards exposing each agent's state and configuration. In the released code this panel is read-only, so design goal G4 (change agent configurations) is only partly realised.

## 5. Implementation scope

We will replicate the three components the paper actually evaluates, and run them against a smaller, cheaper agent team of our own (an Orchestrator, a Coder, an Executor and a search agent) instead of reproducing the full Magentic-One team with its multimodal web surfer.

- **R1. Message-level execution control and reset-and-edit.** Re-implement the instrumented runtime, per-message checkpointing, session forking, and the message history and queue panels, including inline edit-and-revert.
- **R2. Conversation overview visualisation.** Rebuild the linear session visualisation in D3 with the fork layout, the three colour encodings, hover details and click-to-navigate.
- **R3. Reproducible failure harness.** Four to five tasks (GAIA-style level-1 questions plus one coding task) with recorded conversations and pickled checkpoints, so a debugging session can be replayed offline without live model calls. This is also what makes our user study repeatable across participants.

**Enhancement (aligned with the paper's own future work).**

- **E1. Error-anchored context assembly.** A backend endpoint runs a single LLM-as-judge pass over the conversation and returns ranked suspicion spans with short explanations (the paper's code declares such types but never populates them). The overview marks the suspect messages; clicking one assembles a context panel — the flagged span, the messages in the same sender-recipient chain, and the preceding tool calls and warnings — and pre-fills the edit box at that timestamp. This targets the paper's "automatic error identification" direction and its finding that participants spent roughly ten of fifteen minutes just reading before they could edit.
- **E2 (stretch, only if E1 lands early).** Repeat-run fix verification: re-execute a forked session three times from the same checkpoint and report pass or fail per run, answering the paper's open question "did my edit actually work?" using the existing checkpoint machinery and its unused scoring hook.

**Timeline.** Weeks 5–7 build R1 and R3; Week 9 prototype video covering R1–R3; Weeks 10–12 finish R2 and E1; Weeks 12–13 run the study. **Risks:** the repository pins AutoGen 0.4 and was last updated in March 2025 (we freeze the environment); model cost (small models, replayed transcripts); irreversible agent actions (we keep tools local and read-only); non-determinism (temperature 0 and recorded logs).

## 6. Evaluation plan

The authors ran a two-part study with 14 participants. Part 1 (n=6, within-subjects, counterbalanced) compared error identification with full AGDEBUGGER against a reduced version lacking reset and the overview, measuring the errors described, time taken and stated preference. Part 2 (n=8, one-hour sessions with 30 minutes of debugging) asked participants to steer a failing run to the correct answer with think-aloud, five-point Likert ratings of the system and of each feature, and qualitative coding of every edit.

We will replicate this design with 12–14 participants recruited from SMU computing students who have used LLMs, split 6 for Part 1 and 8 for Part 2, and reuse the paper's Appendix A and B instruments. All participants debug the same recorded failures from R3. Measures: errors correctly localised and time to first localisation; whether the correct output was reached; the number and type of edits, coded as add, simplify or modify and compared with the paper's 14/5/5 split; and Likert ratings compared with the published means (helpful 4.4, backtrack-and-edit 4.9). For E1 we add a within-subjects contrast of time-to-localisation and edit count with the error-anchor panel enabled versus disabled. Participants give written consent; we collect no personal data beyond consented screen recordings. If recruiting 14 proves hard we will run a single 12-participant within-subjects study covering both tasks.
