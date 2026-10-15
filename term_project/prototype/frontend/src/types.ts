export interface Msg {
  timestamp: number;
  kind: "publish" | "send" | "response";
  sender: string;
  recipient: string | null;
  envelope_type: string;
  type: string;
  source: string | null;
  content: string;
  editable: boolean;
  body: unknown;
}
export type QueueMsg = Omit<Msg, "timestamp" | "editable" | "body">;
export interface Session { id: number; reset_from: number | null; messages: Msg[] }
export interface State {
  agents: string[];
  targets: string[];
  task_id: string | null;
  task: string | null;
  recording: string | null;
  running: boolean;
  busy: boolean;
  queue: QueueMsg[];
  sessions: Session[];
  current_session: number;
}
export type ColorField = "type" | "sender" | "recipient";
