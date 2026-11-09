"""Build the Phase 3 presentation (PPTX with speaker notes).  python3 build_slides.py  -> Phase3_Slides_Group_Nguyen_Do.pptx"""
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
FIG = HERE.parent / "figures"
OUT = HERE / "Phase3_Slides_Group_Nguyen_Do.pptx"
NAVY, INDIGO, GREY, ROSE = RGBColor(0x0F, 0x17, 0x2A), RGBColor(0x43, 0x38, 0xCA), RGBColor(0x47, 0x55, 0x69), RGBColor(0xE1, 0x1D, 0x48)

prs = Presentation()
prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
BLANK = prs.slide_layouts[6]
W, H = prs.slide_width, prs.slide_height


def text(slide, x, y, w, h, s, size=18, bold=False, color=NAVY, align=PP_ALIGN.LEFT, font="Helvetica"):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run()
    r.text = s
    r.font.size, r.font.bold, r.font.color.rgb, r.font.name = Pt(size), bold, color, font
    return tb


def bullets(slide, x, y, w, h, items, size=18, color=NAVY):
    tb = slide.shapes.add_textbox(x, y, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    first = True
    for it in items:
        level, s = (it if isinstance(it, tuple) else (0, it))
        p = tf.paragraphs[0] if first else tf.add_paragraph()
        first = False
        p.level = level
        p.space_after = Pt(6)
        r = p.add_run()
        r.text = ("•  " if level == 0 else "–  ") + s
        r.font.size, r.font.color.rgb, r.font.name = Pt(size - 2 * level), color, "Helvetica"
    return tb


def header(slide, title, n):
    bar = slide.shapes.add_shape(1, 0, 0, W, Inches(1.0))
    bar.fill.solid(); bar.fill.fore_color.rgb = NAVY; bar.line.fill.background()
    text(slide, Inches(0.5), Inches(0.18), Inches(11.5), Inches(0.7), title, 28, True, RGBColor(0xFF, 0xFF, 0xFF))
    text(slide, Inches(12.2), Inches(0.3), Inches(0.9), Inches(0.5), str(n), 14, False, RGBColor(0xCB, 0xD5, 0xE1), PP_ALIGN.RIGHT)
    text(slide, Inches(0.5), Inches(7.05), Inches(10), Inches(0.35), "CS702 Computational Interaction · Term project · Phase 3 · Nguyen Nhat Minh, Do Duc Anh", 10, False, GREY)


def notes(slide, s):
    slide.notes_slide.notes_text_frame.text = s


def picture(slide, path, x, y, w=None, h=None):
    return slide.shapes.add_picture(str(path), x, y, width=w, height=h)


n = 0
# 1 title ---------------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(1, 0, 0, W, H); bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
text(s, Inches(0.8), Inches(1.6), Inches(11.5), Inches(1.6), "Interactive Debugging and Steering of Multi-Agent AI Systems", 40, True, RGBColor(0xFF, 0xFF, 0xFF))
text(s, Inches(0.8), Inches(3.2), Inches(11.5), Inches(0.8), "Re-implementing AGDebugger (Epperson et al., CHI 2025) with error-anchored context assembly", 22, False, RGBColor(0xCB, 0xD5, 0xE1))
text(s, Inches(0.8), Inches(4.6), Inches(11.5), Inches(0.6), "Nguyen Nhat Minh  ·  Do Duc Anh", 22, True, RGBColor(0xFF, 0xFF, 0xFF))
text(s, Inches(0.8), Inches(5.2), Inches(11.5), Inches(0.6), "CS702 Computational Interaction, AY2026-27 Term 1 · Phase 3 presentation · Week 13", 16, False, RGBColor(0x94, 0xA3, 0xB8))
text(s, Inches(0.8), Inches(6.3), Inches(11.5), Inches(0.6), "Paper: https://doi.org/10.1145/3706598.3713581   ·   Reference code: github.com/microsoft/agdebugger (consulted only for its runtime hook)", 12, False, RGBColor(0x94, 0xA3, 0xB8))
notes(s, "0:00–0:15. Good afternoon. We replicated AGDebugger, a CHI 2025 interactive debugger for teams of LLM agents, and extended it with automatic error localisation. Speaker split: Minh slides 1–6 and 8–10, Anh the live demo (slide 7); swap if you prefer, the notes carry the timing either way.")

# 2 paper ---------------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); header(s, "The paper: AGDebugger (CHI 2025)", n)
bullets(s, Inches(0.5), Inches(1.2), Inches(7.6), Inches(5.6), [
    "Problem: a multi-agent run is 70–90+ messages; one wrong step cascades and the run ends with a wrong answer or none. Logs cannot show where, or let you test a fix without starting over.",
    "Formative interviews with 5 agent developers → 4 design goals (G1 understand messages, G2 send messages, G3 reset & edit, G4 configure agents).",
    "Three features:",
    (1, "Message history + sending + run/step execution control"),
    (1, "Reset-and-edit: restore every agent to a checkpoint, edit the message, fork a session"),
    (1, "Overview visualisation: one column per session, one rectangle per message"),
    "Study with 14 developers: reset-and-edit rated 4.9/5; 2 of 8 steered a failing run to the right answer; 24 edits coded as add (14), simplify (5), modify plan (5).",
    "Open future work named in the paper: automatic error identification — the gap our extension E1 targets.",
], 17)
picture(s, FIG / "paper_fig3.png" if (FIG / "paper_fig3.png").exists() else HERE.parent.parent / "phase2" / "figures" / "ui.png", Inches(8.3), Inches(1.3), w=Inches(4.7))
text(s, Inches(8.3), Inches(4.3), Inches(4.7), Inches(0.5), "Our Phase 2 prototype of the same three panels", 11, False, GREY)
notes(s, "0:15–0:50 (keep to 35 s: paper, three features, one study number, the future-work gap). The paper's core contribution is interactive debugging for agent teams: see every message, send new ones, and above all reset the whole team to a checkpoint and edit the message that went wrong. The overview visualisation makes the long histories navigable. Their study found reset-and-edit the most valued feature, but also that participants spent two thirds of their time reading before editing, and the paper lists automatic error identification as future work. That is what we add.")

# 3 users + scope -------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); header(s, "Target users, their goal and tasks — and our scope", n)
text(s, Inches(0.5), Inches(1.2), Inches(6), Inches(0.5), "Users, goal, tasks", 20, True, INDIGO)
bullets(s, Inches(0.5), Inches(1.7), Inches(6), Inches(4.8), [
    "Developers building and tuning multi-agent LLM systems",
    "Goal: find the message that derailed a run and steer the team to the correct answer",
    "Tasks: browse and step a long history · send messages · reset to an earlier point and edit · keep an overview of branches · (E1) find the suspects fast",
], 17)
text(s, Inches(6.9), Inches(1.2), Inches(6), Inches(0.5), "Implemented scope (all complete)", 20, True, INDIGO)
bullets(s, Inches(6.9), Inches(1.7), Inches(6), Inches(4.8), [
    "C1  Message history, sending, Run/Step/Drop, queue editing",
    "C2  Reset-and-edit with session forking on real checkpoints",
    "C3  Overview visualisation (3 encodings, fork markers, hover, click, filter)",
    "E1  Error-anchored context assembly: judge → ranked suspects → context panel → pre-filled edit",
    "Harness: 29 tasks (13 cached corpus, 16 live Wikipedia), recorded natural failures, study logging and three study conditions",
    "Own code on AutoGen 0.7.5 + React 19; team under debug = Magentic-One orchestrator, Coder, Executor, WebSearcher on Claude Haiku 5.5",
], 16)
notes(s, "0:50–1:15. The users are developers of agent teams. Their goal is to localise the failure and steer the team to the right answer. We implemented the three features of the paper as C1 to C3, and E1, our extension. Everything runs on real AutoGen checkpoints and live model calls, not Wizard-of-Oz.")

# 4 architecture --------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); header(s, "Architecture", n)
picture(s, FIG / "architecture.png", Inches(0.4), Inches(1.15), w=Inches(12.5))
notes(s, "1:15–2:00. Three layers. The browser polls the backend state every 0.7 seconds and posts actions. The backend owns a session manager over an AutoGen single-threaded runtime. The Recorder is an AutoGen InterventionHandler: it intercepts every send, publish and response, gives it a global timestamp and calls runtime.save_state before the message is processed, so any timestamp can be restored. Reset-and-edit loads that checkpoint, rewrites the edited text into the sender's own saved state, re-publishes the message with the rest of its burst and forks a new session. The judge is a separate one-pass call to Claude Opus over a session's JSON; its result is stored with the session and inside recordings, so study participants never wait for it. Every API action and UI event is appended to a per-participant JSON-lines log.")

# 5 implementation details ---------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); header(s, "Implementation: what the paper leaves open", n)
bullets(s, Inches(0.5), Inches(1.2), Inches(6.2), Inches(5.6), [
    "Checkpoints: save_state() on every message (not only on a reset); recordings keep history + checkpoints + sessions + suspects (pickle).",
    "Reset-and-edit semantics we had to add:",
    (1, "Replay the sender's whole burst (instruction + follow-up request-to-speak), or the branch stalls."),
    (1, "Write the edit into the sender's saved state (orchestrator message thread, facts and plan) — otherwise the orchestrator keeps acting on the text it remembers."),
    "Queue editing: change or remove a queued envelope before it is processed.",
    "Error handling: model calls retried (6×), failures surfaced as a banner + toast, the step is skipped and the run stays debuggable; all API failures return readable JSON.",
], 16)
bullets(s, Inches(6.9), Inches(1.2), Inches(6), Inches(5.6), [
    "Own Anthropic ChatCompletionClient (AutoGen's crashed on the current SDK): replays reasoning blocks with tool calls; asks the API to drop stale blocks after a reset changes the prefix; renders tool history as text in reflection turns.",
    "Two web modes per task: a 30-page fictional corpus (reproducible) and live Wikipedia via the MediaWiki API (GAIA-style).",
    "Harness: Claude Opus 5.5 was correct in 97/97 runs — nothing to debug. Claude Haiku 5.5 (low effort) fails naturally: 5 of 158 runs over two harvests (4/84, then 1/74), all on the long financial-year and table tasks; 3 kept as study recordings (t13 ×2, wt2).",
    "Code: ~1,300 lines Python, ~800 lines TypeScript.",
], 16)
notes(s, "2:00–2:40. Two technical findings. First, reset-and-edit only works if you replay the whole burst the original handler emitted, and if the edit is also written into the sender's own saved state. Second, a strong model never failed our 29 tasks in 97 runs, so the team under debug runs on Haiku, where natural failures appear; the paper had the same situation with GPT-4o being the current model. All failures we use are natural: full team, no weakening.")

# 6 E1 ------------------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); header(s, "E1: error-anchored context assembly", n)
picture(s, FIG / "ui_e1_context.png", Inches(0.4), Inches(1.15), w=Inches(8.4))
bullets(s, Inches(9.0), Inches(1.2), Inches(4.1), Inches(5.6), [
    "Motivation: in the paper, ~10 of 15 min went to reading before the first edit.",
    "1. Judge: one Claude Opus pass over the session → ≤5 ranked suspects, category, reason, cited evidence, suggested edit (JSON).",
    "2. Markers: suspects outlined in the overview and badged on the cards.",
    "3. Context panel (no model call): flagged message · who said what to that agent · preceding tool calls · warnings · evidence.",
    "4. Edit this message & revert: opens the editor on that card, pre-filled with the original text and the suggestion.",
    "Precomputed for study recordings; live on demand for new runs. The judge reads the expected answer (as the paper's participants did) but is instructed to describe the edit, never the answer; in the study, E1 is evaluated as the whole package.",
], 14)
notes(s, "2:40–3:10. E1 in one slide. The judge call is the only new model use, and it is cached. The context assembly itself is a pure function of the history. The result lands exactly where the paper's participants ended up anyway: the edit box at the suspect message.")

# 7 demo ----------------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); header(s, "Live demo (4–4.5 min)", n)
bullets(s, Inches(0.5), Inches(1.2), Inches(7.2), Inches(5.6), [
    "Failing run t13: FY 2024/25 visitors ÷ instruments, expected 6651.7 — 228 messages, no answer",
    "C1  history cards · compose · queue: edit a queued message, Drop",
    "C3  overview: colour by sender/type, hover, click, filter",
    "E1  five suspects → context for #2 (orchestrator instruction, t=25) → Edit this message & revert",
    "C2  Save edit & revert → fork · Step twice (broadcast, then the request that makes the live model call) · finished steered branch from a saved live continuation: 6651.7",
    "Study mode: ?cond=reduced | full | e1, per-participant log",
    "Backup: phase3_demo_backup_narrated.mp4 (5 min, narrated)",
], 18)
picture(s, FIG / "ui_e1_edit.png", Inches(7.9), Inches(1.3), w=Inches(5.2))
notes(s, "3:10–7:30. Switch to the browser (runbook: term_project/phase3/demo_runbook.md). Tab A on ?cond=full, Tab B on ?cond=e1 (the condition is read from each tab's URL). The live Step needs API credits: press Step twice (the edited broadcast, then the request-to-speak that calls the model); if it fails or credits are out, load t13_fy_ratio_STEERED_E1 and continue.")

# 8 evaluation ----------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); header(s, "Evaluation plan and preliminary results", n)
bullets(s, Inches(0.5), Inches(1.2), Inches(6.2), Inches(5.6), [
    "Replicates the paper's two-part study with 14 SMU computing students (consent, screen recording + logs).",
    "Part 1 (n=6, within-subjects, Latin square): identify errors in a recorded failing run under three conditions — reduced (no reset, no overview), full, full + E1 — 15 min each.",
    (1, "Measures: errors localised vs our coded ground truth (flag button + think-aloud), time to first correct localisation, preference."),
    "Part 2 (n=8): steer one failing run live for 30 min with all features; Appendix-B Likert items; edits coded add / simplify / modify.",
    (1, "Compared descriptively with the paper: helpful 4.4, reset-and-edit 4.9, 2/8 correct, 14/5/5 edit types."),
    "Fallback: one 12-participant study covering both tasks.",
], 15)
bullets(s, Inches(6.9), Inches(1.2), Inches(6), Inches(5.6), [
    "Preliminary (harness, no participants yet):",
    (1, "Opus 5.5: 97/97 correct (60 corpus, 37 Wikipedia)."),
    (1, "Haiku 5.5: 5/158 natural failures; failure mode = orchestrator re-plans without dispatching (stall at 224–235 msgs)."),
    (1, "Repeat check: the t=25 edit replayed 3× reaches 6651.7 3/3 (two late, after 219–229 msgs); a plain reset at t=25 reaches it 0/3."),
    (1, "Judge on t13: the top-2 suspects are the searcher's 'tables unusable' report and the orchestrator's 'do not estimate' instruction — editing #2 steered the team to 6651.7 in one branch."),
    "Instruments ready: consent form, facilitator script, task sheets, questionnaires, data templates, analysis script (prototype/study/).",
    "Recruitment under way; pilot and first sessions Week 13, remaining sessions Weeks 14–15.",
], 15)
notes(s, "7:30–7:50. One breath: the study design is the proposal's: Part 1 adds our E1 as a third condition; Part 2 replicates the steering task. We have no participant data yet; the harness numbers and the judge's output on the demo run are the preliminary results.")

# 9 status --------------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK); header(s, "Status, timeline, risks", n)
bullets(s, Inches(0.5), Inches(1.2), Inches(12.3), Inches(5.6), [
    "Done: C1, C2, C3, E1 integrated end to end; queue editing; study conditions and logging; harness with 29 tasks, 158 Haiku runs and 3 coded failing recordings; demo videos and runbook.",
    "Week 13: pilot (2 sessions), fix wording of task sheets; code one more failing recording from the harvest as a spare for Part 1.",
    "Weeks 13–15: 14 sessions (or 12 in the fallback design); Week 16: analysis, final report (ACM format), demo video, source release (due 4 Dec).",
    "Risks: recruitment (fallback design); model non-determinism in Part 2 (same checkpoint, same edit can diverge; outcome logged per run, headless repeat-run check available); irreversible actions (local subprocess executor in a scratch directory, cached corpus; checkpoints restore agent state, not files).",
    "Not pursued: agent-configuration panel (unused in the paper's study, read-only in the reference release).",
], 17)
notes(s, "7:50–8:00. Closing. Everything the proposal promised for Phase 3 is implemented; the remaining work is the study and the report.")

# 10 thanks -------------------------------------------------------------
n += 1
s = prs.slides.add_slide(BLANK)
bg = s.shapes.add_shape(1, 0, 0, W, H); bg.fill.solid(); bg.fill.fore_color.rgb = NAVY; bg.line.fill.background()
text(s, Inches(0.8), Inches(2.4), Inches(11.5), Inches(1.2), "Thank you — questions?", 40, True, RGBColor(0xFF, 0xFF, 0xFF))
text(s, Inches(0.8), Inches(3.8), Inches(11.5), Inches(1.5), "Agent Team Debugger · term_project/prototype (./run.sh)\nBackup video: term_project/phase3/phase3_demo_backup.mp4\nEpperson et al. 2025, Interactive Debugging and Steering of Multi-Agent AI Systems, CHI '25, doi:10.1145/3706598.3713581", 16, False, RGBColor(0xCB, 0xD5, 0xE1))
notes(s, "Q&A. Likely questions: why Haiku (Opus never failed); does the judge leak the answer (it knows the expected answer, like the paper's participants did, but its prompt forbids stating or deriving it; E1 is evaluated as a package and participants still make the edit themselves); irreversible actions (local subprocess executor in a scratch directory, cached corpus; files are not checkpointed).")

prs.save(OUT)
print("wrote", OUT, "slides:", len(prs.slides))
