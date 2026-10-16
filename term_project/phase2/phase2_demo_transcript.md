# Phase 2 demo video — transcript

`phase2_demo.mp4`, 3:19. On-screen captions, spoken narration and this transcript are the same text; times are when each line appears.

- **0:00** CS702 phase two prototype. Interactive Debugging and Steering of Multi-Agent AI Systems: re-implementing AGDebugger from CHI 2025. Team: Nguyen Nhat Minh and Do Duc Anh.
- **0:12** The problem: teams of LLM agents exchange dozens of messages to solve a task. One wrong step cascades, and a long run ends with a wrong answer or none. Logs do not show where it went wrong, or let the developer try a fix without starting over.
- **0:25** Target users: developers building and tuning multi-agent systems. Goal: find the message that derailed a run and steer the team to the correct result. Tasks: browse and step a long history, send messages, reset to an earlier point and edit the offending message, and keep an overview of the branches.
- **0:42** Our prototype re-implements the paper's three components: C1, message history with sending and execution control; C2, reset-and-edit with session forking on real checkpoints; and C3, an overview visualisation. Own implementation on AutoGen 0.7.5 and React. The team under debug: a Magentic-One orchestrator, Coder, Executor and WebSearcher on Claude Haiku 5.5.
- **1:06** A recorded failing run is loaded, replayed from saved history and checkpoints, with no model calls.
- **1:12** C1, message history: every runtime message is a card with sender, recipient, type and payload, tool calls included.
- **1:20** Long payloads expand in place. The coloured bar marks the sending agent.
- **1:25** After 228 messages the run ends without an answer. Expected: 6651.7, financial-year visitors divided by six instruments.
- **1:35** Sending: a broadcast to the group or a direct message to one agent lands in the runtime queue.
- **1:41** Run processes the queue continuously, Step processes one message, Drop discards the next.
- **1:46** Dropped. The queue is empty again and the agents never saw the message.
- **1:50** C3, the overview: one column per session, one rectangle per message. Legend buttons filter.
- **1:57** Colour by sender: orchestrator, Coder, Executor, WebSearcher and user.
- **2:02** Colour by recipient topic or agent.
- **2:04** Colour by message type. Tool calls stand out from text.
- **2:08** Hover shows the message. A click scrolls the history to it.
- **2:12** The legend filter dims every other message type.
- **2:15** C2. The mistake starts at message nine: the orchestrator's plan assumes a published financial-year report and forbids estimating. The observatory only publishes monthly tables, so every later instruction inherits the wrong plan.
- **2:28** We edit the plan in place: the fact sheet and plan now point at the two monthly visitor reports, the financial-year definition and the facilities page.
- **2:36** Reset-and-edit restores every agent from the checkpoint before message nine, re-publishes the edited plan and forks a new session. The old branch stays viewable.
- **2:45** Step: the runtime processes just this one message.
- **2:49** The edited broadcast is processed; the orchestrator's request-to-speak waits in the queue. Run continues the branch.
- **2:56** The steered branch finished: with the plan rewritten, the same team sums the monthly figures and reaches 6651.7 instead of giving up after 228 messages. The paper's modify-the-plan strategy.
- **3:08** The overview now shows both sessions. The amber marker is the fork point, and the session tabs switch between branches.
- **3:15** The original failing branch is still browsable for comparison.
