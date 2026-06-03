<script setup lang="ts">
import type { LlmTraceSummary } from "../../types/llmTrace";

defineProps<{
  traces: LlmTraceSummary[];
}>();

const emit = defineEmits<{
  select: [traceId: string];
}>();
</script>

<template>
  <div class="trace-list">
    <button
      v-for="trace in traces"
      :key="trace.trace_id"
      class="trace-row"
      type="button"
      @click="emit('select', trace.trace_id)"
    >
      <span class="trace-row-title">{{ trace.user_input }}</span>
      <span class="trace-row-meta">
        {{ trace.status }} · {{ trace.model_name }} · {{ trace.duration_ms ?? "-" }}ms
      </span>
      <span class="trace-row-meta">{{ trace.created_at }}</span>
    </button>
  </div>
</template>
