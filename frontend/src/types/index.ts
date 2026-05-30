export interface BirthDetails {
  date: string;
  time: string;
  place: string;
  latitude?: number;
  longitude?: number;
  timezone?: string;
}

export type MessageRole = "user" | "assistant" | "tool";

export interface ToolEvent {
  tool: string;
  status: "running" | "done" | "error";
  input?: Record<string, unknown>;
  output?: unknown;
}

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  streaming?: boolean;
  toolEvents?: ToolEvent[];
  timestamp: number;
}

export type StreamEventType =
  | "token"
  | "tool_start"
  | "tool_end"
  | "done"
  | "error";

export interface StreamEvent {
  type: StreamEventType;
  content?: string;
  tool?: string;
  input?: Record<string, unknown>;
  output?: unknown;
  message?: string;
}
