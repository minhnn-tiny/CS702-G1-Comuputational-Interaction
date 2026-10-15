"""Run one task live to completion and save it as a recording: python -m agdbg.record <task_id> [name]"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

for env in (Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[4] / ".env"):
    load_dotenv(env)

from .manager import Manager  # noqa: E402
from .serialize import entry_json  # noqa: E402
from .tasks import TASKS  # noqa: E402


def final_answer(m: Manager) -> str:
    """Last text the orchestrator broadcast to the group (its final answer, if the run finished)."""
    for e in reversed(m.recorder.history):
        j = entry_json(e)
        if j["sender"] == "MagenticOneOrchestrator" and j["recipient"] == "group" and j["type"] == "TextMessage":
            return j["content"]
    return ""


_WORDS = {w: str(i) for i, w in enumerate("zero one two three four five six seven eight nine ten eleven twelve".split())}


def passed(answer: str, expected: str) -> bool:
    import re
    a = re.sub(r"\b(" + "|".join(_WORDS) + r")\b", lambda m: _WORDS[m.group(1).lower()], answer.replace(",", ""), flags=re.I)
    return all(re.search(rf"(?<![\d.]){re.escape(part)}(?![\d.])", a, re.I) for part in expected.split("|"))


async def main(task_id: str, name: str) -> None:
    m = Manager()
    await m.start(task_id)
    m.run()
    try:
        await asyncio.wait_for(m.runtime.stop_when_idle(), timeout=1500)
    except Exception as e:  # keep whatever was recorded, a crashed run is still a failing run
        print("run ended with error:", repr(e)[:200])
    for e in m.recorder.history:
        j = entry_json(e)
        print(f"[{j['timestamp']:>3}] {j['kind']:<8} {j['sender']:<24} -> {str(j['recipient']):<24} {j['type']:<26} {j['content'][:90]!r}")
    ans = final_answer(m)
    ok = passed(ans, TASKS[task_id]["expected"])
    print("expected:", TASKS[task_id]["expected"])
    print("answer:", ans[:300].replace("\n", " "))
    print("messages:", len(m.recorder.history), "RESULT:", "PASS" if ok else "FAIL")
    print("saved:", m.save_recording(name))


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else sys.argv[1]))
