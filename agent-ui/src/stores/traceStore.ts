import { defineStore } from "pinia";
import { ref } from "vue";

import { fetchLlmTraceDetail, fetchLlmTraces } from "../api/llmTraces";
import type { LlmTraceDetail, LlmTraceSummary } from "../types/llmTrace";

export const useTraceStore = defineStore("trace", () => {
  const traces = ref<LlmTraceSummary[]>([]);
  const traceDetail = ref<LlmTraceDetail | null>(null);
  const loading = ref(false);
  const error = ref("");

  async function loadTraces(): Promise<void> {
    loading.value = true;
    error.value = "";

    try {
      traces.value = await fetchLlmTraces();
      traceDetail.value = null;
    } catch (requestError) {
      error.value = requestError instanceof Error ? requestError.message : "日志加载失败";
    } finally {
      loading.value = false;
    }
  }

  async function selectTrace(traceId: string): Promise<void> {
    loading.value = true;
    error.value = "";

    try {
      traceDetail.value = await fetchLlmTraceDetail(traceId);
    } catch (requestError) {
      error.value = requestError instanceof Error ? requestError.message : "日志详情加载失败";
    } finally {
      loading.value = false;
    }
  }

  return {
    error,
    loadTraces,
    loading,
    selectTrace,
    traceDetail,
    traces,
  };
});
