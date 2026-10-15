"""Thin AutoGen ChatCompletionClient on top of the official Anthropic SDK (1.x)."""

from __future__ import annotations

import json
import os
from typing import Any, Mapping, Optional, Sequence

import anthropic
from autogen_core import CancellationToken, FunctionCall
from autogen_core.models import (
    AssistantMessage,
    ChatCompletionClient,
    CreateResult,
    FunctionExecutionResultMessage,
    LLMMessage,
    ModelInfo,
    RequestUsage,
    SystemMessage,
    UserMessage,
)
from autogen_core.tools import Tool, ToolSchema

DEFAULT_MODEL = os.environ.get("AGDBG_MODEL", "claude-haiku-5-5")

MODEL_INFO = ModelInfo(
    vision=False,
    function_calling=True,
    json_output=True,
    structured_output=False,
    family="claude",
    multiple_system_messages=True,
)


def _tool_def(tool: Tool | ToolSchema) -> dict[str, Any]:
    schema: ToolSchema = tool.schema if isinstance(tool, Tool) else tool
    params = schema.get("parameters") or {"type": "object", "properties": {}}
    return {
        "name": schema["name"],
        "description": schema.get("description", ""),
        "input_schema": {
            "type": "object",
            "properties": params.get("properties", {}),
            "required": params.get("required", []),
        },
    }


class AnthropicClient(ChatCompletionClient):
    def __init__(self, model: str = DEFAULT_MODEL, max_tokens: int = 4096) -> None:
        self._model = model
        self._max_tokens = max_tokens
        self._client = anthropic.AsyncAnthropic()
        self._total = RequestUsage(prompt_tokens=0, completion_tokens=0)
        self._last = RequestUsage(prompt_tokens=0, completion_tokens=0)
        # Raw assistant content (thinking + tool_use blocks) keyed by first tool-call id,
        # replayed verbatim so the API sees the thinking that produced each tool call.
        self._raw_turns: dict[str, list[dict[str, Any]]] = {}

    # --- conversion -------------------------------------------------------
    def _convert(self, messages: Sequence[LLMMessage], has_tools: bool) -> tuple[str, list[dict[str, Any]]]:
        """Without tools in the request (AutoGen's reflect-on-tool-use step) past tool calls are rendered as text,
        otherwise the model treats the open tool protocol as unfinished and answers with no text at all."""
        system_parts: list[str] = []
        out: list[dict[str, Any]] = []

        def push(role: str, content: list[dict[str, Any]]) -> None:
            if out and out[-1]["role"] == role:
                out[-1]["content"].extend(content)
            else:
                out.append({"role": role, "content": content})

        for m in messages:
            if isinstance(m, SystemMessage):
                system_parts.append(m.content)
            elif isinstance(m, UserMessage):
                text = m.content if isinstance(m.content, str) else "\n".join(str(p) for p in m.content)
                push("user", [{"type": "text", "text": text or "(empty)"}])
            elif isinstance(m, AssistantMessage):
                if isinstance(m.content, str):
                    push("assistant", [{"type": "text", "text": m.content or "(empty)"}])
                else:
                    raw = self._raw_turns.get(m.content[0].id) if m.content else None
                    if not has_tools:
                        push("assistant", [{"type": "text", "text": (m.thought + "\n" if m.thought else "") + "\n".join(f"[called {fc.name}({fc.arguments})]" for fc in m.content)}])
                    elif raw is not None:
                        push("assistant", list(raw))
                    else:
                        blocks: list[dict[str, Any]] = []
                        if m.thought:
                            blocks.append({"type": "text", "text": m.thought})
                        for fc in m.content:
                            blocks.append({"type": "tool_use", "id": fc.id, "name": fc.name, "input": json.loads(fc.arguments or "{}")})
                        push("assistant", blocks)
            elif isinstance(m, FunctionExecutionResultMessage) and not has_tools:
                push("user", [{"type": "text", "text": "\n\n".join(f"[result of {r.name}]\n{r.content}" for r in m.content)}])
            elif isinstance(m, FunctionExecutionResultMessage):
                push("user", [
                    {"type": "tool_result", "tool_use_id": r.call_id, "content": r.content, "is_error": bool(r.is_error)}
                    for r in m.content
                ])
        if out and out[0]["role"] != "user":
            out.insert(0, {"role": "user", "content": [{"type": "text", "text": "(start)"}]})
        return "\n\n".join(system_parts), out

    # --- ChatCompletionClient API ---------------------------------------
    async def create(
        self,
        messages: Sequence[LLMMessage],
        *,
        tools: Sequence[Tool | ToolSchema] = [],
        tool_choice: Any = "auto",
        json_output: Optional[bool | type] = None,
        extra_create_args: Mapping[str, Any] = {},
        cancellation_token: Optional[CancellationToken] = None,
    ) -> CreateResult:
        system, msgs = self._convert(messages, bool(tools))
        if json_output:
            system = (system + "\n\nRespond with a single valid JSON object and nothing else.").strip()
        if not tools and any(isinstance(m, FunctionExecutionResultMessage) for m in messages):
            system = (system + "\n\nNo tools are available in this turn. Write your reply now from the results already "
                      "gathered above; do not attempt further tool calls.").strip()
        kwargs: dict[str, Any] = dict(
            model=self._model, max_tokens=self._max_tokens, messages=msgs,
            output_config={"effort": os.environ.get("AGDBG_EFFORT", "low")},
        )
        if system:
            kwargs["system"] = system
        if tools:
            kwargs["tools"] = [_tool_def(t) for t in tools]
        # drop_block: after a reset-and-edit (or a tool-list change) an agent's replayed thinking blocks may be
        # bound to a different prefix; let the API drop them instead of failing the turn.
        resp = await self._client.beta.messages.create(
            betas=["server-side-fallback-2026-07-01", "thinking-binding-controls-2026-08-01"],
            fallbacks="default",
            thinking={"type": "adaptive", "block_binding": {"prefix_mismatch_behavior": "drop_block"}},
            **kwargs,
        )

        usage = RequestUsage(prompt_tokens=resp.usage.input_tokens, completion_tokens=resp.usage.output_tokens)
        self._last = usage
        self._total = RequestUsage(
            prompt_tokens=self._total.prompt_tokens + usage.prompt_tokens,
            completion_tokens=self._total.completion_tokens + usage.completion_tokens,
        )

        if os.environ.get("AGDBG_DEBUG"):
            print("[llm]", resp.stop_reason, [(b.type, getattr(b, "text", "")[:60]) for b in resp.content], getattr(resp, "input_transformations", None))
        texts = [b.text for b in resp.content if b.type == "text"]
        calls = [
            FunctionCall(id=b.id, name=b.name, arguments=json.dumps(b.input))
            for b in resp.content if b.type == "tool_use"
        ]
        if calls:
            self._raw_turns[calls[0].id] = [b.model_dump(exclude_none=True) for b in resp.content if b.type in ("thinking", "redacted_thinking", "text", "tool_use")]
            return CreateResult(finish_reason="function_calls", content=calls, usage=usage, cached=False, thought="\n".join(texts) or None)
        if resp.stop_reason == "refusal":
            return CreateResult(finish_reason="content_filter", content="(request declined by safety classifier)", usage=usage, cached=False)
        return CreateResult(
            finish_reason="length" if resp.stop_reason == "max_tokens" else "stop",
            content="\n".join(texts), usage=usage, cached=False,
        )

    async def create_stream(self, messages, *, tools=[], tool_choice="auto", json_output=None, extra_create_args={}, cancellation_token=None):  # type: ignore[override]
        yield await self.create(messages, tools=tools, tool_choice=tool_choice, json_output=json_output, extra_create_args=extra_create_args, cancellation_token=cancellation_token)

    async def close(self) -> None:
        await self._client.close()

    def actual_usage(self) -> RequestUsage:
        return self._last

    def total_usage(self) -> RequestUsage:
        return self._total

    def count_tokens(self, messages: Sequence[LLMMessage], *, tools: Sequence[Tool | ToolSchema] = []) -> int:
        return sum(len(str(getattr(m, "content", ""))) for m in messages) // 4

    def remaining_tokens(self, messages: Sequence[LLMMessage], *, tools: Sequence[Tool | ToolSchema] = []) -> int:
        return 200_000 - self.count_tokens(messages, tools=tools)

    @property
    def capabilities(self):  # type: ignore[override]
        return MODEL_INFO

    @property
    def model_info(self) -> ModelInfo:
        return MODEL_INFO
