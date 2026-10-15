"""Intervention handler: timestamps every runtime message and checkpoints the team before it is processed."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Literal

from autogen_core import AgentId, DropMessage, InterventionHandler, MessageContext, TopicId


@dataclass
class Entry:
    timestamp: int
    kind: Literal["publish", "send", "response"]
    message: Any
    sender: AgentId | None
    recipient: AgentId | None = None
    topic_id: TopicId | None = None


class Recorder(InterventionHandler):
    def __init__(self, checkpoint: Callable[[int], Awaitable[None]]) -> None:
        self.history: list[Entry] = []
        self.next_ts = 0
        self.drop_next = False
        self._checkpoint = checkpoint

    async def _record(self, entry: Entry, message: Any) -> Any:
        if self.drop_next:
            self.drop_next = False
            return DropMessage
        entry.timestamp = self.next_ts
        await self._checkpoint(entry.timestamp)
        self.history.append(entry)
        self.next_ts += 1
        return message

    async def on_send(self, message: Any, *, message_context: MessageContext, recipient: AgentId) -> Any:
        return await self._record(Entry(0, "send", message, message_context.sender, recipient=recipient), message)

    async def on_publish(self, message: Any, *, message_context: MessageContext) -> Any:
        return await self._record(Entry(0, "publish", message, message_context.sender, topic_id=message_context.topic_id), message)

    async def on_response(self, message: Any, *, sender: AgentId, recipient: AgentId | None) -> Any:
        return await self._record(Entry(0, "response", message, sender, recipient=recipient), message)

    def at(self, timestamp: int) -> Entry | None:
        return next((e for e in self.history if e.timestamp == timestamp), None)

    def truncate(self, cutoff: int) -> None:
        self.history = [e for e in self.history if e.timestamp < cutoff]
