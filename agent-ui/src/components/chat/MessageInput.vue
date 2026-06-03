<script setup lang="ts">
defineProps<{
  canSend: boolean;
  loading: boolean;
  suggestions: string[];
}>();

const input = defineModel<string>({ required: true });

const emit = defineEmits<{
  send: [text?: string];
}>();
</script>

<template>
  <div class="suggestions" aria-label="快捷问题">
    <button
      v-for="suggestion in suggestions"
      :key="suggestion"
      type="button"
      :disabled="loading"
      @click="emit('send', suggestion)"
    >
      {{ suggestion }}
    </button>
  </div>

  <form class="composer" @submit.prevent="emit('send')">
    <textarea
      v-model="input"
      rows="2"
      placeholder="输入问题，例如：最近一个月创建的 Bug 里有多少已经关闭？"
    />
    <button type="submit" :disabled="!canSend">发送</button>
  </form>
</template>
