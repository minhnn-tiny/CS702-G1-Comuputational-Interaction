import { schemeTableau10 } from "d3";
import type { ColorField, Msg } from "./types";

export const field = (m: Pick<Msg, "type" | "sender" | "recipient">, f: ColorField) => (f === "type" ? m.type : f === "sender" ? m.sender : m.recipient ?? "none");

const fixed: Record<string, string> = {
  MagenticOneOrchestrator: "#4e79a7",
  Coder: "#f28e2b",
  Executor: "#59a14f",
  WebSearcher: "#e15759",
  user: "#9c755f",
  group: "#bab0ab",
  TextMessage: "#4e79a7",
  GroupChatRequestPublish: "#bab0ab",
  ToolCallRequestEvent: "#f28e2b",
  ToolCallExecutionEvent: "#edc948",
  StopMessage: "#e15759",
  GroupChatReset: "#76b7b2",
};
export const colorFor = (value: string, domain: string[]) =>
  fixed[value] ?? schemeTableau10[Math.max(0, domain.indexOf(value)) % schemeTableau10.length];
