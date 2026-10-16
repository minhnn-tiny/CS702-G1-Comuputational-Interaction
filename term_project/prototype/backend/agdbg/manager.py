"""Session manager: owns the team runtime, history, checkpoints, forks and recordings."""

from __future__ import annotations

import asyncio
import copy
import os
import pickle
import shutil
import uuid
from pathlib import Path
from typing import Any

from autogen_agentchat.base import Response
from autogen_agentchat.messages import TextMessage
from autogen_agentchat.teams._group_chat._events import (
    GroupChatAgentResponse,
    GroupChatRequestPublish,
    GroupChatStart,
)
from autogen_core import AgentId, TopicId
from autogen_core._queue import Queue

from .recorder import Entry, Recorder
from .serialize import entry_json, envelope_json, inner_text, is_text, with_content
from .tasks import TASKS
from .team import make_team

ROOT = Path(__file__).resolve().parents[2]
RECORDINGS = ROOT / "recordings"
WORKDIR = Path(os.environ.get("AGDBG_WORKDIR", ROOT / "workdir"))


FACTS_MARK = "Here is an initial fact sheet to consider:"
PLAN_MARK = "Here is the plan to follow as best as possible:"


def _rewrite(obj: Any, old: str, new: str) -> Any:
    """Replace every message content equal to `old` inside a saved runtime state. If the edited message is the
    Magentic-One orchestrator's task-ledger broadcast, its stored facts and plan are updated from the new text too."""
    if isinstance(obj, dict):
        if obj.get("content") == old:
            obj["content"] = new
        if "facts" in obj and "plan" in obj and FACTS_MARK in new and PLAN_MARK in new and obj["plan"].strip() and obj["plan"].strip() in old:
            facts, plan = new.split(FACTS_MARK, 1)[1].split(PLAN_MARK, 1)
            obj["facts"], obj["plan"] = facts.strip(), plan.strip()
        for v in obj.values():
            _rewrite(v, old, new)
    elif isinstance(obj, list):
        for v in obj:
            _rewrite(v, old, new)
    return obj


class Manager:
    def __init__(self) -> None:
        self.team_id: str | None = None
        self.task_id: str | None = None
        self.recording: str | None = None
        self.checkpoints: dict[int, Any] = {}
        self.prior_sessions: list[dict[str, Any]] = []
        self.reset_from: int | None = None
        self.recorder = Recorder(self._checkpoint)
        self.lock = asyncio.Lock()
        self.busy = False

    # --- lifecycle -------------------------------------------------------
    async def start(self, task_id: str | None = None, team_id: str | None = None, web: str | None = None) -> None:
        if getattr(self, "team", None) is not None and self.running:
            await self.runtime.stop()
        self.team_id = team_id or str(uuid.uuid4())
        self.task_id = task_id
        self.recording = None
        self.checkpoints = {}
        self.prior_sessions = []
        self.reset_from = None
        self.recorder = Recorder(self._checkpoint)
        shutil.rmtree(WORKDIR, ignore_errors=True)
        WORKDIR.mkdir(parents=True)
        for name, content in (TASKS[task_id]["files"] if task_id else {}).items():
            (WORKDIR / name).write_text(content)
        self.web = web or (TASKS[task_id].get("web", "corpus") if task_id else "corpus")
        self.team = make_team(WORKDIR, self.team_id, self.web)
        self.runtime = self.team._runtime
        # AgentChat's runtime re-raises a failed handler on the next step and shuts the queue; keep it debuggable
        self.runtime._ignore_unhandled_handler_exceptions = True
        await self.team._init(self.runtime)
        self.runtime._intervention_handlers = [self.recorder]
        if task_id:
            await self.start_task(TASKS[task_id]["task"])

    @property
    def running(self) -> bool:
        return self.runtime._run_context is not None

    @property
    def queue(self) -> list[Any]:
        return list(self.runtime._message_queue._queue)  # type: ignore[attr-defined]

    @property
    def agents(self) -> list[str]:
        return ["MagenticOneOrchestrator", *self.team._participant_names]

    @property
    def topics(self) -> dict[str, str]:
        t = self.team
        return {
            "group": t._group_topic_type,
            "output": t._output_topic_type,
            "MagenticOneOrchestrator": t._group_chat_manager_topic_type,
            **dict(zip(t._participant_names, t._participant_topic_types)),
        }

    async def _checkpoint(self, timestamp: int) -> None:
        self.checkpoints[timestamp] = await self.runtime.save_state()

    # --- execution control ------------------------------------------------
    def run(self) -> None:
        if not self.running:
            self.runtime.start()

    async def stop(self) -> None:
        if self.running:
            await self.runtime.stop()

    async def step(self) -> None:
        if self.running or not self.queue:
            return
        self.busy = True
        try:
            await self.runtime.process_next()
            for _ in range(2400):  # wait for the handler (and its model call) to finish, max 2 min
                if not self.runtime._background_tasks:
                    break
                await asyncio.sleep(0.05)
        finally:
            self.busy = False

    async def drop(self) -> None:
        if self.running or not self.queue:
            return
        self.recorder.drop_next = True
        await self.runtime.process_next()

    # --- sending ----------------------------------------------------------
    def _bg(self, coro: Any) -> None:
        async def wait() -> None:
            try:
                await coro
            except Exception as e:  # response errors surface in the history, not the server log
                print("[send]", e)

        asyncio.create_task(wait())

    async def start_task(self, text: str) -> None:
        msg = GroupChatStart(messages=[TextMessage(content=text, source="user")])
        self._bg(self.runtime.send_message(msg, AgentId(self.team._group_chat_manager_topic_type, self.team_id)))
        await asyncio.sleep(0)

    async def send(self, type_: str, target: str, content: str, source: str = "user") -> None:
        """Compose panel: `target` is an agent name or 'group'."""
        topic = TopicId(self.topics[target], self.team_id)
        if type_ == "GroupChatStart":
            await self.start_task(content)
        elif type_ == "GroupChatMessage":
            # GroupChatMessage is only AutoGen's UI log event; agents receive broadcasts as AgentResponse, like the orchestrator's
            text = TextMessage(content=content, source=source)
            self._bg(self.runtime.publish_message(GroupChatAgentResponse(response=Response(chat_message=text), name=source), topic))
        elif type_ == "GroupChatRequestPublish":
            self._bg(self.runtime.publish_message(GroupChatRequestPublish(), topic))
        else:
            raise ValueError(f"unsupported type {type_}")
        await asyncio.sleep(0)

    # --- reset and edit ---------------------------------------------------
    async def edit_and_revert(self, timestamp: int, new_content: str | None) -> None:
        entry = self.recorder.at(timestamp)
        if entry is None:
            raise ValueError(f"no message at timestamp {timestamp}")
        if entry.kind == "response":
            raise ValueError("responses cannot be replayed")
        await self.stop()
        # The checkpoint at `timestamp` was taken when that message was dequeued, i.e. after the handler that
        # produced it had already queued its whole burst (e.g. the orchestrator's instruction + the follow-up
        # request-to-speak). Replay the burst so the branch continues exactly as the original did.
        burst = [entry]
        for e in self.recorder.history[self.recorder.history.index(entry) + 1:]:
            if e.kind == "response" or e.sender != entry.sender:
                break
            burst.append(e)
        self.runtime._message_queue = Queue()  # pending work belongs to the abandoned branch
        self.prior_sessions.append(self._session_json(len(self.prior_sessions)))
        self.reset_from = timestamp
        self.recorder.truncate(timestamp)
        checkpoint = self.checkpoints[timestamp]
        if new_content is not None:
            # The sender's own memory of the message (e.g. the orchestrator's message thread, already written when
            # the checkpoint was taken) must carry the edit too, or the sender keeps acting on the original text.
            checkpoint = _rewrite(copy.deepcopy(checkpoint), inner_text(entry.message), new_content)
        await self.runtime.load_state(checkpoint)
        for e in burst:
            message = e.message if new_content is None or e is not entry else with_content(e.message, new_content)
            if e.kind == "publish":
                self._bg(self.runtime.publish_message(message, e.topic_id, sender=e.sender))
            else:
                self._bg(self.runtime.send_message(message, e.recipient, sender=e.sender))
            await asyncio.sleep(0)

    # --- views ------------------------------------------------------------
    def _session_json(self, sid: int) -> dict[str, Any]:
        return {"id": sid, "reset_from": self.reset_from, "messages": [entry_json(e) for e in self._visible()]}

    def _visible(self) -> list[Entry]:
        """History minus runtime noise: empty RPC acks, and the text copies relayed to AutoGen's UI output topic."""
        h = self.recorder.history
        out = []
        for i, e in enumerate(h):
            if e.kind == "response" and e.message is None:
                continue
            if (e.kind == "publish" and e.topic_id is not None and e.topic_id.type.startswith("output_topic")
                    and is_text(e.message)):
                continue
            out.append(e)
        return out

    def state(self) -> dict[str, Any]:
        sessions = [*self.prior_sessions, self._session_json(len(self.prior_sessions))]
        return {
            "agents": self.agents,
            "targets": ["group", *self.team._participant_names],
            "task_id": self.task_id,
            "task": TASKS[self.task_id]["task"] if self.task_id else None,
            "web": self.web,
            "recording": self.recording,
            "running": self.running,
            "busy": self.busy,
            "queue": [envelope_json(e) for e in self.queue],
            "sessions": sessions,
            "current_session": len(self.prior_sessions),
        }

    # --- recordings -------------------------------------------------------
    def save_recording(self, name: str) -> Path:
        RECORDINGS.mkdir(exist_ok=True)
        path = RECORDINGS / f"{name}.pkl"
        with path.open("wb") as f:
            pickle.dump(
                {
                    "team_id": self.team_id,
                    "task_id": self.task_id,
                    "web": self.web,
                    "history": self.recorder.history,
                    "next_ts": self.recorder.next_ts,
                    "checkpoints": self.checkpoints,
                    "prior_sessions": self.prior_sessions,
                    "reset_from": self.reset_from,
                },
                f,
            )
        return path

    async def load_recording(self, name: str) -> None:
        with (RECORDINGS / f"{name}.pkl").open("rb") as f:
            data = pickle.load(f)
        await self.start(None, team_id=data["team_id"], web=data.get("web", "corpus"))
        self.task_id = data["task_id"]
        self.recording = name
        for k, v in TASKS[self.task_id]["files"].items():
            (WORKDIR / k).write_text(v)
        self.recorder.history = data["history"]
        self.recorder.next_ts = data["next_ts"]
        self.checkpoints = data["checkpoints"]
        self.prior_sessions = data["prior_sessions"]
        self.reset_from = data["reset_from"]
        if self.checkpoints:
            await self.runtime.load_state(self.checkpoints[max(self.checkpoints)])

    @staticmethod
    def recordings() -> list[str]:
        return sorted(p.stem for p in RECORDINGS.glob("*.pkl"))
