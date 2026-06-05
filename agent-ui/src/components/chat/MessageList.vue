<script setup lang="ts">
import type { ChatMessage } from "../../types/chat";

defineProps<{
  loading: boolean;
  messages: ChatMessage[];
  nowTime: () => string;
}>();
</script>

<template>
  <div class="message-list">
    <article
      v-for="message in messages"
      :key="message.id"
      class="message"
      :class="`message-${message.role}`"
    >
      <div class="message-meta">
        <span>{{ message.role === "agent" ? "Agent" : "你" }}</span>
        <time>{{ message.time }}</time>
      </div>
      <p class="message-text">{{ message.content }}</p>
    </article>

    <article v-if="loading" class="message message-agent">
      <div class="message-meta">
        <span>Agent</span>
        <time>{{ nowTime() }}</time>
      </div>
      <p class="message-text">正在分析...</p>
    </article>
  </div>
</template>
