import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { sendChatMessage } from "../api/chat";
import type { ChatMessage } from "../types/chat";

function nowTime(): string {
  return new Intl.DateTimeFormat("zh-CN", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(new Date());
}

export const useChatStore = defineStore("chat", () => {
  const input = ref("");
  const loading = ref(false);
  const sessionId = crypto.randomUUID();
  const backendStatus = ref<"未连接" | "已连接" | "连接失败">("未连接");

  const messages = ref<ChatMessage[]>([
    {
      id: 1,
      role: "agent",
      content:
        "我可以查询需求和 Bug 数据、分析研发风险、生成质量报告，也可以在接入后执行受控状态流转。",
      time: "09:30",
    },
  ]);

  const suggestions = [
    "最近一个月创建了多少 Bug？其中多少已关闭？",
    "分析延期需求最多的模块",
    "找出重开次数高的 Bug",
    "生成一份研发质量周报",
  ];

  const canSend = computed(() => input.value.trim().length > 0 && !loading.value);

  async function sendMessage(text?: string): Promise<void> {
    const content = (text ?? input.value).trim();
    if (!content || loading.value) return;

    messages.value.push({
      id: Date.now(),
      role: "user",
      content,
      time: nowTime(),
    });
    input.value = "";
    loading.value = true;

    try {
      const response = await sendChatMessage(content, sessionId);
      backendStatus.value = "已连接";
      messages.value.push({
        id: Date.now() + 1,
        role: "agent",
        content: response.reply,
        time: nowTime(),
      });
    } catch (error) {
      backendStatus.value = "连接失败";
      const message = error instanceof Error ? error.message : "后端请求失败";
      messages.value.push({
        id: Date.now() + 1,
        role: "agent",
        content: `后端连接失败：${message}`,
        time: nowTime(),
      });
    } finally {
      loading.value = false;
    }
  }

  return {
    backendStatus,
    canSend,
    input,
    loading,
    messages,
    nowTime,
    sendMessage,
    suggestions,
  };
});
