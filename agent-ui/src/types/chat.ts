export type MessageRole = "user" | "agent";

export interface ChatMessage {
  id: number;
  role: MessageRole;
  content: string;
  time: string;
}

export interface ChatResponse {
  session_id: string;
  reply: string;
}
