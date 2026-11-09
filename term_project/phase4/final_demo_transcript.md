# Final demo video — transcript

`final_demo.mp4`, 1:57. On-screen captions, spoken narration and this transcript are the same text; times are when each line appears.

- **0:00** Agent Team Debugger: a re-implementation of AGDebugger, CHI 2025, with error-anchored context. Nguyen Nhat Minh and Do Duc Anh.
- **0:10** A developer opens a failing run: the team was asked for an observatory's financial-year visitors per instrument, and after 228 runtime messages gave no answer.
- **0:21** Scrolling to the end: the orchestrator re-planned twenty-two times and gave up.
- **0:28** The overview maps the whole session: one rectangle per message, coloured by type, sender or recipient; a click jumps the history to it.
- **0:39** Rather than read everything, the developer opens the error context panel: a judge pass over the session, run once and stored with the recording.
- **0:48** Five ranked suspects appear in the panel, the overview and on the cards, each with a reason.
- **0:54** Selecting one assembles its context: who said what to that agent, the tool calls before it, warnings, cited evidence, and a suggested edit.
- **1:04** One click opens the editor on that message, pre-filled with the original text and the suggestion.
- **1:10** The developer rewrites the instruction: read both monthly visitor reports and the facilities page; do not look for annual accounts.
- **1:20** Save edit and revert restores all agents to the checkpoint before this message and forks a new session, which then continues live.
- **1:33** The finished branch, saved from a live continuation of this edit: the same team sums the monthly tables and answers 6651.7. Both sessions stay side by side, the failing one with its suspect markers.
- **1:49** Agent Team Debugger: history, reset-and-edit, overview and error-anchored context on AutoGen and React.
