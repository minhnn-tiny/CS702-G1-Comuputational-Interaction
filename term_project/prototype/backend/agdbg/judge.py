"""E1 error-anchored context assembly, step 1: an LLM-as-judge pass that ranks suspect messages in a session.

The judge sees the task, the expected answer, the run's outcome and a compact transcript of every visible message,
and returns up to five suspects, each with a short explanation and a suggested edit. The ranked list is stored with
the session (and inside recordings), so study participants in the E1 condition never trigger a model call.
"""

from __future__ import annotations

import json
import os
from typing import Any

import anthropic

JUDGE_MODEL = os.environ.get("AGDBG_JUDGE_MODEL", "claude-opus-5-5")
MAX_CHARS = 1500  # per message in the transcript shown to the judge
MAX_SUSPECTS = 5
CATEGORIES = {"wrong plan", "vague instruction", "misreported result", "hallucinated fact", "ignored evidence", "wrong computation", "other"}

SYSTEM = """You are an expert reviewer of multi-agent LLM systems. You are given the complete message log of one run of a
Magentic-One style team (an orchestrator that writes a fact sheet and a plan, then instructs a Coder, a code Executor and
a WebSearcher) that FAILED to answer a task. Your job is to find the messages where the run went wrong, so that a
developer can reset the team to just before one of them, edit it, and continue.

Rules:
- A suspect is a message whose content (a wrong plan, a wrong or too-vague instruction, a misreported tool result, a
  hallucinated fact, an ignored piece of evidence, a wrong computation) caused later messages to go astray. Prefer the
  EARLIEST message at which the mistake entered the conversation over its later repetitions.
- Prefer editable messages: TextMessage broadcasts or instructions (orchestrator plan, orchestrator instruction to an
  agent, an agent's report). Tool-call events and tool results are evidence, not edit targets; cite them as evidence.
- Rank by how much editing that single message would change the outcome. At most %d suspects.
- Be concrete: quote the offending phrase, name the evidence by its timestamp, and give a one- or two-sentence edit
  that would most likely fix it (what to add, remove or change). Describe WHAT TO CHANGE in the message, never the
  task's final answer: do not state, compute or hint at the expected answer or intermediate results anywhere in the
  summary, reasons or suggestions. The developer must still work out the fix.
- Answer with a single JSON object and nothing else (no prose before or after), with this shape:
  {"summary": "<two or three sentences: what went wrong and where>",
   "suspects": [{"timestamp": <int>, "category": "<wrong plan | vague instruction | misreported result | hallucinated fact | ignored evidence | wrong computation | other>",
                 "reason": "<why; quote the offending phrase>", "evidence": [<timestamps>], "suggestion": "<concrete edit>"}]}
""" % MAX_SUSPECTS

def transcript(messages: list[dict[str, Any]]) -> str:
    lines = []
    for m in messages:
        c = m["content"] or "(no text payload)"
        if len(c) > MAX_CHARS:
            c = c[:MAX_CHARS] + f" … [{len(c) - MAX_CHARS} more characters]"
        lines.append(f"### t={m['timestamp']} {m['sender']} -> {m['recipient']} [{m['type']}]\n{c}")
    return "\n\n".join(lines)


def final_answer(messages: list[dict[str, Any]]) -> str:
    for m in reversed(messages):
        if m["sender"] == "MagenticOneOrchestrator" and m["recipient"] == "group" and m["type"] == "TextMessage":
            return m["content"]
    return ""


async def judge(task: str, expected: str, messages: list[dict[str, Any]], model: str = JUDGE_MODEL) -> dict[str, Any]:
    """Return {"model", "summary", "suspects": [...]} for the given visible history (entry_json dicts)."""
    editable = {m["timestamp"] for m in messages if m.get("editable")}
    answer = final_answer(messages)
    prompt = (
        f"TASK GIVEN TO THE TEAM:\n{task}\n\n"
        f"EXPECTED ANSWER (known to the developer, not to the team): {expected}\n\n"
        f"OUTCOME: the run ended after {len(messages)} messages. Final orchestrator message:\n{answer[:800] or '(none: the run stalled or hit its turn limit)'}\n\n"
        f"EDITABLE MESSAGE TIMESTAMPS: {sorted(editable)}\n\n"
        f"MESSAGE LOG:\n\n{transcript(messages)}"
    )
    client = anthropic.AsyncAnthropic(max_retries=6)
    resp = await client.messages.create(
        model=model, max_tokens=8000, system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "\n".join(b.text for b in resp.content if b.type == "text")
    if os.environ.get("AGDBG_DEBUG"):
        print("[judge]", resp.stop_reason, text[:400])
    try:
        data = json.loads(text[text.index("{"): text.rindex("}") + 1])
        if not isinstance(data, dict) or not isinstance(data.get("suspects", []), list):
            raise ValueError("not an object with a suspects list")
    except (ValueError, json.JSONDecodeError) as e:
        raise ValueError(f"the judge returned no parsable result ({e}); try again") from None
    known = {m["timestamp"] for m in messages}
    suspects, seen = [], set()
    for raw in data.get("suspects", []):
        if not isinstance(raw, dict):
            continue
        try:
            ts = int(raw.get("timestamp"))
        except (TypeError, ValueError):
            continue
        if ts not in known or ts in seen:
            continue
        seen.add(ts)
        ev = raw.get("evidence") if isinstance(raw.get("evidence"), list) else []
        suspects.append({
            "timestamp": ts,
            "category": raw.get("category") if raw.get("category") in CATEGORIES else "other",
            "reason": str(raw.get("reason") or "").strip(),
            "evidence": [int(t) for t in ev if isinstance(t, (int, float)) and int(t) in known],
            "suggestion": str(raw.get("suggestion") or "").strip(),
            "rank": len(suspects) + 1,
            "editable": ts in editable,
        })
        if len(suspects) == MAX_SUSPECTS:
            break
    return {"model": model, "summary": str(data.get("summary") or "").strip(), "suspects": suspects,
            "usage": {"input": resp.usage.input_tokens, "output": resp.usage.output_tokens}}


if __name__ == "__main__":  # python -m agdbg.judge <recording> [--save]  (runs the judge on session 0 of a recording)
    import asyncio
    import pickle
    import sys
    from pathlib import Path

    from dotenv import load_dotenv

    for env in (Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[4] / ".env"):
        load_dotenv(env, override=True)  # the repository .env wins over a stale key in the shell environment
    from .manager import RECORDINGS, visible  # noqa: E402
    from .serialize import entry_json  # noqa: E402
    from .tasks import TASKS  # noqa: E402

    path = RECORDINGS / f"{sys.argv[1]}.pkl"
    data = pickle.load(path.open("rb"))
    msgs = data["prior_sessions"][0]["messages"] if data["prior_sessions"] else [entry_json(e) for e in visible(data["history"])]
    task = TASKS[data["task_id"]]
    result = asyncio.run(judge(task["task"], task["expected"], msgs))
    print(json.dumps(result, indent=1))
    if "--save" in sys.argv:
        data.setdefault("suspects", {})[0] = result
        pickle.dump(data, path.open("wb"))
        print("saved into", path)
