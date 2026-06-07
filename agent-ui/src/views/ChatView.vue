<script setup lang="ts">
import { onMounted, ref } from "vue";

import { fetchDashboardSummary } from "../api/dashboard";
import { http } from "../api/http";
import MessageInput from "../components/chat/MessageInput.vue";
import MessageList from "../components/chat/MessageList.vue";
import { useChatStore } from "../stores/chatStore";
import type { MetricCard, RiskItem } from "../types/dashboard";

const chatStore = useChatStore();

const metrics = ref<MetricCard[]>([]);
const risks = ref<RiskItem[]>([]);
const dashboardLoading = ref(false);
const dashboardError = ref("");

onMounted(() => {
  loadDashboard();
  loadSuggestions();
});

async function loadSuggestions(): Promise<void> {
  try {
    const { data } = await http.get<string[]>("/suggestions");
    if (data.length > 0) {
      chatStore.suggestions = data;
    }
  } catch {
    // keep defaults
  }
}

async function loadDashboard(): Promise<void> {
  dashboardLoading.value = true;
  dashboardError.value = "";
  try {
    const data = await fetchDashboardSummary();
    metrics.value = data.metrics;
    risks.value = data.risks;
  } catch {
    dashboardError.value = "指标数据加载失败";
    // 兜底：显示空数据而非假数据
    metrics.value = [];
    risks.value = [];
  } finally {
    dashboardLoading.value = false;
  }
}
</script>

<template>
  <section class="workspace" aria-label="Agent 对话工作区">
    <header class="topbar">
      <div>
        <p class="eyebrow">研发数据问答</p>
        <h2>让 Agent 解释数据，而不是只返回数字</h2>
      </div>
      <button class="primary-action" type="button">{{ chatStore.backendStatus }}</button>
    </header>

    <section class="chat-panel">
      <MessageList
        :loading="chatStore.loading"
        :messages="chatStore.messages"
        :now-time="chatStore.nowTime"
      />
      <MessageInput
        v-model="chatStore.input"
        :can-send="chatStore.canSend"
        :loading="chatStore.loading"
        :suggestions="chatStore.suggestions"
        @send="chatStore.sendMessage"
      />
    </section>
  </section>

  <aside class="insights" aria-label="指标和风险">
    <p v-if="dashboardError" class="dashboard-error">{{ dashboardError }}</p>

    <section class="metric-grid">
      <article
        v-for="metric in metrics"
        :key="metric.label"
        class="metric-card"
      >
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <p>{{ metric.trend }}</p>
      </article>
      <p v-if="dashboardLoading" class="dashboard-loading">加载指标中...</p>
    </section>

    <section class="risk-panel">
      <h2>风险提示</h2>
      <p v-if="risks.length === 0 && !dashboardLoading" class="risk-empty">
        暂无风险数据
      </p>
      <article v-for="risk in risks" :key="risk.title" class="risk-item">
        <div>
          <h3>{{ risk.title }}</h3>
          <p>{{ risk.detail }}</p>
        </div>
        <span :class="`risk-${risk.level}`">{{ risk.level }}</span>
      </article>
    </section>
  </aside>
</template>
