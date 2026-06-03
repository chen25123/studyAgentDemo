import { http } from "./http";
import type { LlmTraceDetail, LlmTraceSummary } from "../types/llmTrace";

export async function fetchLlmTraces(): Promise<LlmTraceSummary[]> {
  const response = await http.get<LlmTraceSummary[]>("/admin/llm-traces");
  return response.data;
}

export async function fetchLlmTraceDetail(traceId: string): Promise<LlmTraceDetail> {
  const response = await http.get<LlmTraceDetail>(
    `/admin/llm-traces/${encodeURIComponent(traceId)}`,
  );
  return response.data;
}
