"""Run every task N times with the full team and report which runs failed.

    python -m agdbg.harvest [--seeds 2] [--jobs 4] [task_id ...]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .manager import RECORDINGS
from .tasks import TASKS

LOGS = RECORDINGS / "harvest_logs"


def run_one(task_id: str, seed: int, prefix: str = "") -> tuple[str, str, int, str]:
    name = f"{prefix}{task_id}_r{seed}"
    LOGS.mkdir(parents=True, exist_ok=True)
    log = LOGS / f"{name}.log"
    with log.open("w") as f:
        subprocess.run(
            [sys.executable, "-m", "agdbg.record", task_id, name],
            cwd=Path(__file__).resolve().parents[1],
            env={**__import__("os").environ, "AGDBG_WORKDIR": str(RECORDINGS.parent / f"workdir-{name}")},
            stdout=f, stderr=subprocess.STDOUT, timeout=1800,
        )
    text = log.read_text()
    m = re.search(r"messages: (\d+) RESULT: (\w+)", text)
    a = re.search(r"^answer: (.*)$", text, re.M)
    return name, (m.group(2) if m else "ERROR"), int(m.group(1)) if m else 0, (a.group(1)[:120] if a else "")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("tasks", nargs="*", default=list(TASKS))
    ap.add_argument("--seeds", type=int, default=2)
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--prefix", default="", help="recording name prefix, e.g. haiku_")
    ap.add_argument("--first-seed", type=int, default=1)
    args = ap.parse_args()
    jobs = [(t, s) for t in args.tasks for s in range(args.first_seed, args.first_seed + args.seeds)]
    with ThreadPoolExecutor(args.jobs) as pool:
        results = list(pool.map(lambda j: run_one(*j, args.prefix), jobs))
    for name, res, n, ans in results:
        print(f"{res:<6} {n:>3} msgs  {name:<28} {ans}")
    fails = [r for r in results if r[1] != "PASS"]
    print(f"\n{len(fails)}/{len(results)} runs failed")


if __name__ == "__main__":
    main()
