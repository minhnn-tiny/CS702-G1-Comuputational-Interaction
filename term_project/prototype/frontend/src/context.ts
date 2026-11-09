import type { Msg, Suspect } from "./types";

const WARN = /traceback|error|exception|404|not found|no results|timed out|failed|could not|unable to/i;

/** E1 step 2: assemble the context around a suspect message from the session history alone (no model call).
 *  chain: the preceding messages exchanged with the suspect's sender or recipient (who told it what);
 *  tools: tool calls and results since the previous orchestrator instruction (what it actually did);
 *  warnings: messages in that window whose text looks like an error. */
export function assemble(messages: Msg[], s: Suspect) {
  const i = messages.findIndex((m) => m.timestamp === s.timestamp);
  if (i < 0) return undefined;
  const target = messages[i];
  const before = messages.slice(0, i);
  // Messages this agent exchanged: sent by it, sent by the agent it addressed, addressed to it, or broadcast to the
  // group (every agent receives those).
  const party = new Set([target.sender, target.recipient]);
  const chain = before
    .filter((m) => m.type === "TextMessage" && (party.has(m.sender) || m.recipient === target.sender || m.recipient === "group"))
    .slice(-3);
  let start = before.length;
  while (start > 0 && !(before[start - 1].sender === "MagenticOneOrchestrator" && before[start - 1].type === "TextMessage")) start--;
  const window = before.slice(Math.max(0, start - 1));
  const tools = window.filter((m) => m.type.startsWith("ToolCall")).slice(-6);
  const warnings = window.filter((m) => m.content && WARN.test(m.content) && !tools.includes(m)).slice(-3);
  const evidence = s.evidence.map((t) => messages.find((m) => m.timestamp === t)).filter((m): m is Msg => !!m);
  return { target, chain, tools, warnings, evidence };
}
