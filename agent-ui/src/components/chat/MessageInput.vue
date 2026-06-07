<script setup lang="ts">
const props = defineProps<{
  canSend: boolean;
  loading: boolean;
  suggestions: string[];
}>();

const input = defineModel<string>({ required: true });

const emit = defineEmits<{
  send: [text?: string];
}>();

function onKeydown(e: KeyboardEvent): void {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    if (props.canSend) {
      emit("send");
    }
  }
}
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
      placeholder="输入问题，Enter 发送，Shift+Enter 换行"
      @keydown="onKeydown"
    />
    <button type="submit" :disabled="!canSend">发送</button>
  </form>
</template>
