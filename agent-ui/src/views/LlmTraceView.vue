<script setup lang="ts">
import { onMounted } from "vue";

import TraceDetail from "../components/traces/TraceDetail.vue";
import TraceList from "../components/traces/TraceList.vue";
import { useChatStore } from "../stores/chatStore";
import { useTraceStore } from "../stores/traceStore";

const chatStore = useChatStore();
const traceStore = useTraceStore();

onMounted(() => {
  void traceStore.loadTraces();
});
</script>

<template>
  <section class="workspace workspace-wide" aria-label="LLM Trace 工作区">
    <header class="topbar">
      <div>
        <p class="eyebrow">开发者追踪</p>
        <h2>追溯每一次 LLM 调用</h2>
      </div>
      <button class="primary-action" type="button">{{ chatStore.backendStatus }}</button>
    </header>

    <section class="trace-panel">
      <div class="trace-toolbar">
        <button type="button" @click="traceStore.loadTraces">刷新</button>
        <span v-if="traceStore.loading">加载中...</span>
        <span v-else>最近 LLM 调用记录</span>
      </div>

      <p v-if="traceStore.error" class="trace-error">{{ traceStore.error }}</p>

      <div class="trace-layout">
        <TraceList
          :traces="traceStore.traces"
          @select="traceStore.selectTrace"
        />
        <TraceDetail :detail="traceStore.traceDetail" />
      </div>
    </section>
  </section>
</template>
