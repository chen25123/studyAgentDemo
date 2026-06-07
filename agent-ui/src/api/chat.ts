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

export interface SseEvent {
  type: "thinking" | "tool_start" | "tool_result" | "message_delta" | "final" | "error";
  content?: string;
  tool?: string;
  message?: string;
  summary?: string;
}

export async function sendChatMessageStream(
  message: string,
  sessionId: string,
  onEvent: (event: SseEvent) => void,
  signal?: AbortSignal,
): Promise<string> {
  const response = await fetch("/api/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });

  if (!response.ok) {
    throw new Error(`后端返回 ${response.status}`);
  }

  const reader = response.body?.getReader();
  if (!reader) throw new Error("浏览器不支持流式读取");

  const decoder = new TextDecoder();
  let buffer = "";
  let fullContent = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const event: SseEvent = JSON.parse(line.slice(6));
          if (event.type === "message_delta" && event.content) {
            fullContent += event.content;
          }
          onEvent(event);
        } catch {
          // 忽略解析失败的行
        }
      }
    }
  }

  // 处理 buffer 中残留的行
  if (buffer.startsWith("data: ")) {
    try {
      const event: SseEvent = JSON.parse(buffer.slice(6));
      if (event.type === "message_delta" && event.content) {
        fullContent += event.content;
      }
      onEvent(event);
    } catch {
      // ignore
    }
  }

  return fullContent;
}
