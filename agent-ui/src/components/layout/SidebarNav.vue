<script setup lang="ts">
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();

function isActive(name: string): boolean {
  return route.name === name;
}
</script>

<template>
  <aside class="sidebar" aria-label="Agent 能力">
    <div class="brand">
      <div class="brand-mark">D</div>
      <div>
        <h1>DevFlow Agent</h1>
        <p>研发流程智能助手</p>
      </div>
    </div>

    <nav class="nav-list">
      <button
        class="nav-item"
        :class="{ active: isActive('chat') }"
        type="button"
        @click="router.push({ name: 'chat' })"
      >
        对话分析
      </button>
      <button
        class="nav-item"
        :class="{ active: isActive('req-metrics') }"
        type="button"
        @click="router.push({ name: 'req-metrics' })"
      >
        需求巡检
      </button>
      <button
        class="nav-item"
        :class="{ active: isActive('bug-metrics') }"
        type="button"
        @click="router.push({ name: 'bug-metrics' })"
      >
        Bug 质量
      </button>
      <button
        class="nav-item"
        :class="{ active: isActive('chat') }"
        type="button"
        @click="router.push({ name: 'chat' })"
        title="在对话中生成报告"
      >
        报告生成
      </button>
      <button
        class="nav-item nav-item-muted"
        :class="{ active: isActive('llm-traces') }"
        type="button"
        @click="router.push({ name: 'llm-traces' })"
      >
        LLM Trace
      </button>
      <button
        class="nav-item nav-item-muted"
        :class="{ active: isActive('admin-metrics') }"
        type="button"
        @click="router.push({ name: 'admin-metrics' })"
      >
        指标管理
      </button>
    </nav>

    <section class="source-panel">
      <h2>数据源</h2>
      <div class="source-row">
        <span>MySQL</span>
        <strong>agent_workflow</strong>
      </div>
      <div class="source-row">
        <span>框架</span>
        <strong>LangGraph</strong>
      </div>
      <div class="source-row">
        <span>模式</span>
        <strong>只读分析</strong>
      </div>
    </section>
  </aside>
</template>
