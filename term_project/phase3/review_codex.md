**Verdict: the slides cover the required topics, but the presentation is over time and the scripted demo contains failures that need correction.** The “all complete” and robust-error-handling claims are stronger than the implementation supports.

This was a static source review plus video metadata inspection. I did not run the app, execute tests, or modify files.

**1. Presentation requirements and timing**

The introduction identifies the paper, target developers, their goals, and C1–C3/E1. Architecture and implementation receive adequate time. The problem is the total:

| Segment | Speaker-note timing |
|---|---:|
| Introduction | 1:50 |
| Technical implementation, including E1 | 2:20 |
| Demo | 4:20 |
| Subtotal | **8:30** |
| Optional evaluation | Another 0:30 |
| Closing/transitions | Additional time |

The demo explicitly ends at 8:30 in [build_slides.py:166](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/phase3/slides/build_slides.py:166). This exceeds the 7–8-minute requirement before evaluation or closing.

Concrete fixes:

- Target **1:00 introduction + 2:00 technical explanation + 4:30 demo + 0:15 transitions = 7:45**.
- Move evaluation and status slides to an appendix. Retain one sentence stating that participant evaluation has not started.
- Shorten the paper’s study statistics and SDK troubleshooting details. Spend that time explaining how inspection, contextual evidence, and branching help a developer test a suspected cause.
- Simplify the dense 14–17-point text, especially slides 2, 5, and 6. Source inspection cannot establish projector readability or clipping.
- Replace “all complete” with a bounded description of the supported workflow and remaining limitations.

**2. Live-demo runbook risks**

- **The two-tab setup does not preserve two conditions.** Opening Tab B with `cond=e1` changes the shared backend condition; Tab A then also renders E1. The prescribed setup at [demo_runbook.md:14](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/phase3/demo_runbook.md:14) cannot reliably demonstrate full versus E1.
- **One Step will not produce the promised tool calls.** The edited t=25 message is a broadcast; t=26 is the request-to-speak. The first Step buffers the instruction. A subsequent Step invokes the WebSearcher, potentially making several model calls. Correct both [runbook line 32](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/phase3/demo_runbook.md:32) and the backup narration. Use observed queue/message milestones instead of “exactly one model call.”
- **The named backup is silent and longer than advertised.** Metadata shows `phase3_demo_backup.mp4` contains video only and lasts **5:35.6**. `phase3_demo_backup_narrated.mp4` contains audio. The runbook calls the former “narrated, 4 min.” Prepare a correctly named, trimmed backup that fits the remaining presentation time.
- **The recovery instructions are unreliable.** “Run/Step again” does not replay a failed envelope. A two-minute Step timeout can also leave work running while the UI reports idle; loading a fallback then risks interference.
- **A stale build can be presented.** [run.sh:9](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/run.sh:9) rebuilds only when `dist` is missing or `--build` is supplied. Explicitly build and rehearse the exact artifact on the presentation machine.

**3. Code findings, ranked by severity**

**High — core functionality or study validity**

1. **Study conditions share global state and leak E1 answers into baseline conditions.**  
   [app.py:22](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/app.py:22), [study.py:21](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/study.py:21), [App.tsx:100](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/frontend/src/App.tsx:100).  
   Another tab changes everyone’s participant/condition. Separately, suspect data is passed to History and Overview regardless of condition: `full` and even `reduced` can show suspect badges from precomputed recordings. **Scenario:** a baseline participant receives error-localisation hints, invalidating the comparison. Scope participant/condition per client or trial, and gate every E1 cue.

2. **Stop destroys pending work instead of providing resumable execution control.**  
   [manager.py:142](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/manager.py:142).  
   This delegates directly to AutoGen 0.7.5’s `runtime.stop()`, which discards pending envelopes and replaces the queue. **Scenario:** Run → Stop → Step loses the pending request-to-speak and cannot resume the branch. Implement a pause that preserves the queue, or clearly expose destructive stopping and recovery.

3. **A judge result can be attached to the wrong recording.**  
   [manager.py:186](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/manager.py:186), [App.tsx:73](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/frontend/src/App.tsx:73).  
   `judge()` captures messages, awaits the network, then writes to `self.suspects[sid]`. Loading another recording remains enabled during judging. **Scenario:** judge A, load B, receive A’s suspects on B’s session 0. Validate a recording/session generation identifier before accepting the result.

4. **Step can report completion while its handler is still running.**  
   [manager.py:146](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/manager.py:146), [app.py:118](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/app.py:118).  
   After 120 seconds, `busy` becomes false without cancelling or completing background work. Run also bypasses the manager lock. **Scenario:** a slow/retried call survives the timeout; the user loads a recording or resets while the old handler continues mutating state. Keep execution ownership until cancellation/completion and serialize runtime mutations.

5. **Failed edits can partially destroy the current branch.**  
   [manager.py:247](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/manager.py:247).  
   Queue clearing, session append, and history truncation happen before checkpoint restoration and text-edit validation finish. **Scenario:** `/api/edit` targets a tool event with replacement text; `with_content()` eventually raises, the API returns 400, but the session has already changed. Validate first and commit the fork atomically.

**Medium — robustness and misleading interaction**

6. **The retry banner promises recovery that is not implemented.**  
   [manager.py:106](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/manager.py:106), [App.tsx:92](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/frontend/src/App.tsx:92).  
   Handler exceptions are ignored after recording the model error; the failed envelope is not requeued. **Scenario:** WebSearcher fails after SDK retries; another Step processes subsequent events rather than retrying that request. Provide checkpoint-based retry or tell users to reset explicitly.

7. **Judge output is insufficiently validated.**  
   [judge.py:76](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/judge.py:76), [Overview.tsx:101](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/frontend/src/components/Overview.tsx:101).  
   Valid JSON with malformed suspects can raise backend exceptions or reach UI code expecting strings and arrays. Missing `reason`, for example, breaks hover rendering. Invalid JSON silently becomes a successful empty result. Validate a typed response schema, reject malformed output visibly, and deduplicate timestamps. Also stop assuming every judged session failed.

8. **Queue removal bypasses queue accounting and RPC completion.**  
   [manager.py:174](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/manager.py:174).  
   Removing a non-head envelope with `del q[index]` neither calls `task_done()` nor resolves/cancels its future. **Scenario:** removing a queued RPC strands its caller and leaves unfinished-task accounting incorrect. Use envelope-aware removal; identify messages with stable IDs rather than mutable indices.

9. **Fork geometry is wrong because child histories retain their prefix.**  
   [Overview.tsx:16](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/frontend/src/components/Overview.tsx:16), [recorder.py:50](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/recorder.py:50).  
   The child retains messages before the reset point, but Overview offsets its entire history to the fork row. **Scenario:** after editing t=25, the connector aligns with the child’s first retained message rather than the replacement. Render branch suffixes or align shared prefixes consistently.

10. **Context assembly misses the actual broadcast conversation.**  
    [context.ts:14](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/frontend/src/context.ts:14).  
    The chain checks literal sender/recipient equality and misses messages delivered through `group`. **Scenario:** selecting WebSearcher t=23 omits the orchestrator’s preceding group instruction; selecting orchestrator t=25 omits WebSearcher’s t=23 group report. Include broadcast delivery relationships or explicit causal links.

11. **Card state survives across unrelated recordings.**  
    [History.tsx:12](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/frontend/src/components/History.tsx:12), [History.tsx:101](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/frontend/src/components/History.tsx:101).  
    Cards are keyed only by timestamp. **Scenario:** leave t=25 editing, then load another recording containing t=25; the old draft or flagged state can survive on the new message. Key state by recording/run, session, and timestamp; clear pending edit requests on load.

12. **Logs do not support the claimed reconstruction of actions.**  
    [app.py:156](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/app.py:156), [app.py:182](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/app.py:182).  
    Edits/sends record character counts, not exact text; queue actions are logged before success without an outcome. **Scenario:** a rejected queue edit appears as an action, while the actual participant instruction cannot be reconstructed. Log successful outcomes, stable message/trial identifiers, and the content needed for edit coding.

**4. Other grading-point risks**

- **The answer-leakage defence is contradicted by the artifact.** Speaker notes say the judge “does not solve the task,” but its stored summary and suggestions contain the complete calculation and answer: [dump:132](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/recordings/harvest_logs/_dump_t13_fy_ratio_FAIL.txt:132). Disclose that E1 supplies diagnosis and solution guidance; it is not an isolated test of navigation/context assembly.
- **“Sandboxed executor” overstates isolation.** [team.py:124](/Users/minh/Documents/courses/CS702-G1-Comuputational-Interaction/term_project/prototype/backend/agdbg/team.py:124) uses a local subprocess executor. Agent checkpoints also do not restore filesystem effects. Bound the reset claim accordingly.
- Distinguish **228 runtime messages from 125 visible cards**; the current narration conflates them.
- Label the finished branch explicitly as a **previously recorded continuation**, since it does not establish that the current live branch succeeded.
- No participant results is permissible because evaluation is optional. However, “pilot in Week 12” on a Week-13 presentation looks stale. State actual recruitment/pilot status.
- I found no regression tests for these debugger features. Harness answer checks do not verify queue, branching, condition isolation, or failure recovery.

**5. Top five actions**

1. Cut the presentation to 7:45 and prepare the correct, shortened narrated backup.
2. Repair condition isolation and remove E1 cues from full/reduced conditions.
3. Correct the Step demonstration and replace Stop/retry behaviour with reliable execution control.
4. Make reset atomic and reject stale judge results; validate judge output.
5. Fix branch/context displays and align claims about answer guidance, sandboxing, logging, and evaluation status with the implementation.