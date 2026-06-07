<script setup lang="ts">
import { onMounted, ref } from "vue";
import { http } from "../api/http";

interface MetricInfo {
  metric_code: string; metric_name: string; entity_code: string;
  formula_type: string; format_type: string; description: string;
}
interface MetricValue {
  metric_code: string; metric_name: string; value: number | null;
  unit: string; measures: Record<string, number>; period: string;
}

const metrics = ref<MetricInfo[]>([]);
const values = ref<Record<string, MetricValue>>({});
const loading = ref(false);

onMounted(async () => {
  loading.value = true;
  try {
    const { data } = await http.get<MetricInfo[]>("/metrics");
    metrics.value = data.filter((m) => m.entity_code === "requirement");

    for (const m of metrics.value) {
      try {
        const { data: v } = await http.get<MetricValue>(
          `/metrics/${encodeURIComponent(m.metric_code)}/value`
        );
        values.value[m.metric_code] = v;
      } catch { /* skip */ }
    }
  } finally { loading.value = false; }
});

function fmt(v: number | null, unit: string): string {
  if (v === null) return "—";
  return unit === "%" ? `${v}%` : v >= 1000 ? `${v.toLocaleString()}` : `${v}`;
}
</script>

<template>
  <section class="workspace" aria-label="需求巡检">
    <header class="topbar">
      <div>
        <p class="eyebrow">需求巡检</p>
        <h2>需求指标本月实时数据</h2>
      </div>
    </header>

    <p v-if="loading">加载中...</p>

    <section class="metric-cards">
      <article v-for="m in metrics" :key="m.metric_code" class="metric-card-detail">
        <h3>{{ m.metric_name }}</h3>
        <code>{{ m.metric_code }}</code>
        <div class="metric-value">
          {{ fmt(values[m.metric_code]?.value ?? null, m.format_type === 'percent' ? '%' : '个') }}
        </div>
        <p>{{ m.description }}</p>
        <div v-if="values[m.metric_code]?.measures" class="metric-sub">
          <span v-for="(v, k) in values[m.metric_code]?.measures" :key="k">
            {{ k }}: {{ typeof v === 'number' && v >= 1000 ? v.toLocaleString() : v }}
          </span>
        </div>
      </article>
    </section>

    <p v-if="!loading && metrics.length === 0" class="empty-hint">暂无需求指标</p>
  </section>
</template>
