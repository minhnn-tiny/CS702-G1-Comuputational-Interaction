"""Headless steering run: load a recording, edit one message, let the team continue, report PASS/FAIL and save.

    python -m agdbg.steer <recording> <timestamp> <edit_file|-> [name] [--repeat N]

The edit file holds the new message text ('-' keeps the original: a plain reset-and-retry). With --repeat the same
edit is replayed N times from the same checkpoint and each outcome is reported (the paper's "did my edit work?").
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv

for env in (Path(__file__).resolve().parents[2] / ".env", Path(__file__).resolve().parents[4] / ".env"):
    load_dotenv(env, override=True)  # the repository .env wins over a stale key in the shell environment

from .manager import Manager  # noqa: E402
from .record import final_answer, passed  # noqa: E402
from .tasks import TASKS  # noqa: E402


async def once(recording: str, timestamp: int, text: str | None, name: str | None) -> tuple[bool, int, str]:
    m = Manager()
    await m.load_recording(recording)
    await m.edit_and_revert(timestamp, text)
    m.run()
    try:
        await asyncio.wait_for(m.runtime.stop_when_idle(), timeout=1500)
    except Exception as e:
        print("run ended with error:", repr(e)[:200])
    ans = final_answer(m)
    ok = passed(ans, TASKS[m.task_id]["expected"])
    n = len(m.recorder.history)
    print(f"branch: {n} messages, answer: {ans[:200]!r}, RESULT: {'PASS' if ok else 'FAIL'}")
    if name:
        print("saved:", m.save_recording(name))
    return ok, n, ans


async def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    repeat = int(sys.argv[sys.argv.index("--repeat") + 1]) if "--repeat" in sys.argv else 1
    recording, ts, edit = args[0], int(args[1]), args[2]
    name = args[3] if len(args) > 3 else None
    text = None if edit == "-" else Path(edit).read_text()
    results = []
    for i in range(repeat):
        results.append(await once(recording, ts, text, f"{name}_{i + 1}" if name and repeat > 1 else name))
    if repeat > 1:
        print(f"{sum(r[0] for r in results)}/{repeat} runs passed")


if __name__ == "__main__":
    asyncio.run(main())
