<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { http } from "../../api/http";

interface MetricDetail {
  metric_code: string; metric_name: string; entity_code: string;
  formula_type: string; formula_config: any; time_field: string;
  format_type: string; description: string; status: string; version: number;
}
interface MetricValue {
  value: number | null; unit: string; measures: Record<string, number>; period: string;
}
interface DimInfo {
  dimension_code: string; dimension_name: string; field_expression: string;
  data_type: string; is_filterable: number; is_groupable: number;
}

const route = useRoute();
const metric = ref<MetricDetail | null>(null);
const value = ref<MetricValue | null>(null);
const dims = ref<DimInfo[]>([]);
const loading = ref(false);

onMounted(async () => {
  loading.value = true;
  const code = route.params.code as string;
  try {
    const { data: m } = await http.get<MetricDetail>(`/metrics/${code}`);
    metric.value = m;
    const { data: v } = await http.get<MetricValue>(`/metrics/${code}/value`);
    value.value = v;
    const { data: d } = await http.get<DimInfo[]>(`/entities/${m.entity_code}/dimensions`);
    dims.value = d;
  } catch { /* 404 */ }
  finally { loading.value = false; }
});
</script>

<template>
  <section class="workspace" aria-label="指标详情">
    <header class="topbar">
      <div>
        <p class="eyebrow">指标详情</p>
        <h2 v-if="metric">{{ metric.metric_name }}</h2>
      </div>
    </header>

    <p v-if="loading">加载中...</p>

    <article v-if="metric" class="metric-detail-page">
      <section class="detail-section">
        <h3>基本信息</h3>
        <dl>
          <dt>指标编码</dt><dd><code>{{ metric.metric_code }}</code></dd>
          <dt>所属实体</dt><dd>{{ metric.entity_code }}</dd>
          <dt>公式类型</dt><dd>{{ metric.formula_type }}</dd>
          <dt>时间字段</dt><dd>{{ metric.time_field || "—" }}</dd>
          <dt>版本</dt><dd>v{{ metric.version }}</dd>
          <dt>状态</dt><dd><span :class="metric.status === 'active' ? 'status-active' : 'status-draft'">{{ metric.status }}</span></dd>
        </dl>
      </section>

      <section class="detail-section" v-if="value">
        <h3>当前数值（{{ value.period }}）</h3>
        <div class="metric-value">{{ value.value }}{{ value.unit }}</div>
        <div class="metric-sub" v-if="value.measures">
          <span v-for="(v, k) in value.measures" :key="k">{{ k }}: {{ v }}</span>
        </div>
      </section>

      <section class="detail-section">
        <h3>口径说明</h3>
        <p>{{ metric.description }}</p>
      </section>

      <section class="detail-section" v-if="dims.length">
        <h3>可用维度（{{ dims.length }}）</h3>
        <table class="admin-table">
          <thead><tr><th>编码</th><th>名称</th><th>字段</th><th>可过滤</th><th>可分组</th></tr></thead>
          <tbody>
            <tr v-for="d in dims" :key="d.dimension_code">
              <td><code>{{ d.dimension_code }}</code></td>
              <td>{{ d.dimension_name }}</td>
              <td><code>{{ d.field_expression }}</code></td>
              <td>{{ d.is_filterable ? '✅' : '—' }}</td>
              <td>{{ d.is_groupable ? '✅' : '—' }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </article>

    <p v-if="!loading && !metric" class="empty-hint">指标不存在</p>
  </section>
</template>
