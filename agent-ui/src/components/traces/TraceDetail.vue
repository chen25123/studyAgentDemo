<script setup lang="ts">
import type { LlmTraceDetail } from "../../types/llmTrace";

defineProps<{
  detail: LlmTraceDetail | null;
}>();
</script>

<template>
  <div class="trace-detail">
    <template v-if="detail">
      <div class="trace-detail-head">
        <h3>{{ detail.conversation.trace_id }}</h3>
        <p>
          {{ detail.conversation.session_id }} ·
          {{ detail.conversation.status }} ·
          {{ detail.conversation.total_tokens ?? "-" }} tokens
        </p>
      </div>

      <article
        v-for="item in detail.messages"
        :key="item.id"
        class="trace-message"
      >
        <div class="trace-message-meta">
          <strong>{{ item.message_order }}. {{ item.role }}</strong>
          <span>{{ item.message_type }}</span>
        </div>
        <pre>{{ item.content }}</pre>
      </article>
    </template>
    <p v-else class="trace-empty">选择一条记录查看完整 messages。</p>
  </div>
</template>
