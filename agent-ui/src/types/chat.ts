export type MessageRole = "user" | "agent";

export interface ChatMessage {
  id: number;
  role: MessageRole;
  content: string;
  time: string;
  chart?: string;  // base64 PNG chart image
}

export interface ChatResponse {
  session_id: string;
  reply: string;
}
