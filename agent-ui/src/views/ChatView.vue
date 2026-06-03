<script setup lang="ts">
import MessageInput from "../components/chat/MessageInput.vue";
import MessageList from "../components/chat/MessageList.vue";
import { useChatStore } from "../stores/chatStore";
import type { Metric, RiskItem } from "../types/dashboard";

const chatStore = useChatStore();

const metrics: Metric[] = [
  { label: "近月创建 Bug", value: "26,794", trend: "关闭率 14.29%" },
  { label: "需求总量", value: "20,000", trend: "已上线 2,222" },
  { label: "重开 Bug", value: "11,429", trend: "需重点复盘" },
  { label: "延期需求", value: "11,110", trend: "交付压力偏高" },
];

const risks: RiskItem[] = [
  {
    title: "需求延期偏多",
    detail: "超过半数需求实际完成时间晚于计划时间。",
    level: "高",
  },
  {
    title: "重开 Bug 需要归因",
    detail: "重开记录集中时会影响测试回归效率。",
    level: "中",
  },
  {
    title: "未关联需求 Bug",
    detail: "存在 8,000 条 Bug 未关联需求，建议补齐来源。",
    level: "中",
  },
];
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
    <section class="metric-grid">
      <article v-for="metric in metrics" :key="metric.label" class="metric-card">
        <span>{{ metric.label }}</span>
        <strong>{{ metric.value }}</strong>
        <p>{{ metric.trend }}</p>
      </article>
    </section>

    <section class="risk-panel">
      <h2>风险提示</h2>
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
