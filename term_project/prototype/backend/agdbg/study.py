"""Study instrumentation: one JSON-lines log per participant, written by the API and by the UI."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOGS = Path(__file__).resolve().parents[2] / "logs"
CONDITIONS = ("reduced", "full", "e1")


class StudyLog:
    def __init__(self) -> None:
        self.participant = "anon"
        self.condition = "e1"
        self.trial = ""
        self.t0 = time.monotonic()

    def set(self, participant: str | None, condition: str | None, trial: str | None = None) -> None:
        """Called when a study URL is opened: this is the trial's t=0 (the facilitator starts the clock here too)."""
        if participant:
            self.participant = "".join(ch for ch in participant if ch.isalnum() or ch in "-_")[:32] or "anon"
        if condition in CONDITIONS:
            self.condition = condition
        self.trial = "".join(ch for ch in (trial or "") if ch.isalnum() or ch in "-_")[:16]
        self.t0 = time.monotonic()
        self.log("trial_start", participant=self.participant, condition=self.condition, trial=self.trial)

    def log(self, event: str, **data: Any) -> None:
        LOGS.mkdir(exist_ok=True)
        rec = {"time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"), "elapsed": round(time.monotonic() - self.t0, 3),
               "participant": self.participant, "condition": self.condition, "trial": self.trial, "event": event, **data}
        with (LOGS / f"{self.participant}.jsonl").open("a") as f:
            f.write(json.dumps(rec, default=str) + "\n")
