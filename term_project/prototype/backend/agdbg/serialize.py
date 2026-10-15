"""JSON views of runtime messages for the UI, plus text-level editing of a message."""

from __future__ import annotations

import dataclasses
import json
from typing import Any

from autogen_agentchat.messages import BaseChatMessage, TextMessage
from autogen_agentchat.teams._group_chat._events import (
    GroupChatAgentResponse,
    GroupChatMessage,
    GroupChatStart,
)
from autogen_core._single_threaded_agent_runtime import (
    PublishMessageEnvelope,
    ResponseMessageEnvelope,
    SendMessageEnvelope,
)

from .recorder import Entry


def _inner(msg: Any) -> BaseChatMessage | Any:
    """The human-facing chat message carried inside a group-chat event, if any."""
    if isinstance(msg, GroupChatMessage):
        return msg.message
    if isinstance(msg, GroupChatStart) and msg.messages:
        return msg.messages[0]
    if isinstance(msg, GroupChatAgentResponse):
        return msg.response.chat_message
    return msg


def inner_text(msg: Any) -> str:
    inner = _inner(msg)
    content = getattr(inner, "content", None)
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    try:
        return json.dumps(
            [c.model_dump(mode="json") if hasattr(c, "model_dump") else dataclasses.asdict(c) if dataclasses.is_dataclass(c) else c for c in content],
            indent=1,
        )
    except Exception:
        return str(content)


def is_text(msg: Any) -> bool:
    return isinstance(_inner(msg), TextMessage)


def inner_source(msg: Any) -> str | None:
    return getattr(_inner(msg), "source", None)


def inner_type(msg: Any) -> str:
    return type(_inner(msg)).__name__


def with_content(msg: Any, text: str) -> Any:
    """Deep copy of `msg` whose carried TextMessage content is replaced by `text`."""
    copy = msg.model_copy(deep=True)
    inner = _inner(copy)
    if not isinstance(inner, TextMessage):
        raise ValueError(f"{type(inner).__name__} cannot be edited as text")
    inner.content = text
    return copy


def _agent(a: Any) -> str | None:
    return None if a is None else a.type.split("_")[0] if "_" in a.type else a.type


def _topic(t: Any) -> str | None:
    return None if t is None else t.type.split("_")[0]


def _dump(msg: Any) -> Any:
    try:
        return msg.model_dump(mode="json")
    except Exception:
        return str(msg)


def entry_json(e: Entry) -> dict[str, Any]:
    return {
        "timestamp": e.timestamp,
        "kind": e.kind,
        "sender": _agent(e.sender) or "user",
        "recipient": _agent(e.recipient) if e.recipient is not None else _topic(e.topic_id),
        "envelope_type": type(e.message).__name__,
        "type": inner_type(e.message),
        "source": inner_source(e.message),
        "content": inner_text(e.message),
        "editable": isinstance(_inner(e.message), TextMessage) and e.kind != "response",
        "body": _dump(e.message),
    }


def envelope_json(env: Any) -> dict[str, Any]:
    match env:
        case PublishMessageEnvelope():
            kind, sender, recipient = "publish", env.sender, None
            topic = env.topic_id
        case SendMessageEnvelope():
            kind, sender, recipient, topic = "send", env.sender, env.recipient, None
        case ResponseMessageEnvelope():
            kind, sender, recipient, topic = "response", env.sender, env.recipient, None
        case _:
            kind, sender, recipient, topic = "?", None, None, None
    return {
        "kind": kind,
        "sender": _agent(sender) or "user",
        "recipient": _agent(recipient) if recipient is not None else _topic(topic),
        "envelope_type": type(env.message).__name__,
        "type": inner_type(env.message),
        "source": inner_source(env.message),
        "content": inner_text(env.message),
    }
