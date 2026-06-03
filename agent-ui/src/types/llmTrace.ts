export interface LlmTraceSummary {
  id: number;
  trace_id: string;
  session_id: string;
  user_input: string;
  final_output: string | null;
  model_name: string;
  provider: string | null;
  status: string;
  duration_ms: number | null;
  total_tokens: number | null;
  created_at: string;
}

export interface LlmTraceMessage {
  id: number;
  trace_id: string;
  session_id: string;
  message_order: number;
  role: string;
  content: string;
  message_type: string;
  tool_name: string | null;
  created_at: string;
}

export interface LlmTraceDetail {
  conversation: LlmTraceSummary;
  messages: LlmTraceMessage[];
}
