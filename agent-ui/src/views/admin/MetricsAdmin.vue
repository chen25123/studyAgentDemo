<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import { http } from "../../api/http";

interface MetricItem {
  metric_code: string; metric_name: string; entity_code: string;
  formula_type: string; format_type: string; description: string; status?: string;
}

const metrics = ref<MetricItem[]>([]);
const loading = ref(false);
const router = useRouter();

onMounted(async () => {
  loading.value = true;
  try {
    const { data } = await http.get<MetricItem[]>("/metrics");
    metrics.value = data;
  } finally { loading.value = false; }
});
</script>

<template>
  <section class="workspace" aria-label="指标管理">
    <header class="topbar">
      <div>
        <p class="eyebrow">Admin</p>
        <h2>指标管理</h2>
      </div>
    </header>

    <p v-if="loading">加载中...</p>

    <table v-else class="admin-table">
      <thead>
        <tr>
          <th>指标编码</th>
          <th>名称</th>
          <th>实体</th>
          <th>类型</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="m in metrics" :key="m.metric_code">
          <td><code>{{ m.metric_code }}</code></td>
          <td>{{ m.metric_name }}</td>
          <td>{{ m.entity_code }}</td>
          <td>
            <span class="metric-tag">{{ m.formula_type === "ratio" ? "比率" : "计数" }}</span>
          </td>
          <td>
            <button
              class="btn-sm"
              @click="router.push({ name: 'metric-detail', params: { code: m.metric_code } })"
            >
              详情
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
