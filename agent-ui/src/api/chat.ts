import { http } from "./http";
import type { ChatResponse } from "../types/chat";

export async function sendChatMessage(
  message: string,
  sessionId: string,
): Promise<ChatResponse> {
  const response = await http.post<ChatResponse>("/chat", {
      message,
      session_id: sessionId,
  });
  return response.data;
}
