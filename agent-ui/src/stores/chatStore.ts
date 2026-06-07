import { defineStore } from "pinia";
import { computed, ref } from "vue";

import { sendChatMessageStream } from "../api/chat";
import type { ChatMessage } from "../types/chat";

const ERROR_MAP: Record<string, string> = {
  timeout: "响应超时，请稍后重试",
  "60,000ms": "响应超时，请稍后重试",
  network: "网络异常，请检查后端服务是否已启动",
  NetworkError: "网络异常，请检查后端服务是否已启动",
  "Failed to fetch": "无法连接到后端服务，请确认 uvicorn 已启动",
  "500": "后端处理异常，请查看终端日志",
  "503": "后端服务暂时不可用",
};

function toUserError(raw: string): string {
  for (const [key, value] of Object.entries(ERROR_MAP)) {
    if (raw.includes(key)) return value;
  }
  return `后端连接失败：${raw}`;
}

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

  // 当前正在构建的 Agent 消息 ID（流式写入用）
  let _streamMsgId = 0;
  // AbortController 用于取消请求
  let _abortController: AbortController | null = null;

  const messages = ref<ChatMessage[]>([
    {
      id: 1,
      role: "agent",
      content:
        "我可以查询需求和 Bug 数据、分析研发风险、生成质量报告，也可以在接入后执行受控状态流转。",
      time: "09:30",
    },
  ]);

  const suggestions = ref([
    "最近一个月创建了多少 Bug？其中多少已关闭？",
    "分析延期需求最多的模块",
    "找出重开次数高的 Bug",
    "生成一份研发质量周报",
  ]);

  const canSend = computed(() => input.value.trim().length > 0 && !loading.value);

  async function sendMessage(text?: string): Promise<void> {
    const content = (text ?? input.value).trim();
    if (!content || loading.value) return;

    // 用户消息
    messages.value.push({
      id: Date.now(),
      role: "user",
      content,
      time: nowTime(),
    });
    input.value = "";
    loading.value = true;

    // Agent 占位消息（流式填充）
    _streamMsgId = Date.now() + 1;
    messages.value.push({
      id: _streamMsgId,
      role: "agent",
      content: "",
      time: nowTime(),
    });

    _abortController = new AbortController();

    try {
      await sendChatMessageStream(
        content,
        sessionId,
        (event) => {
          const msg = messages.value.find((m) => m.id === _streamMsgId);
          if (!msg) return;

          switch (event.type) {
            case "tool_start":
              // 工具开始——追加状态行（不覆盖已有文本）
              if (msg.content) {
                msg.content += `\n\n${event.message}`;
              } else {
                msg.content = event.message ?? "";
              }
              break;
            case "tool_result":
              // 工具完成——追加结果摘要
              if (event.summary) {
                msg.content += `\n---\n${event.summary}`;
              }
              break;
            case "message_delta":
              // LLM 逐 token——如果之前是状态行则清掉重建，否则累加
              if (msg.content && msg.content.startsWith("正在")) {
                msg.content = event.content ?? "";
              } else {
                msg.content += event.content ?? "";
              }
              break;
            case "error":
              msg.content = `错误：${event.message}`;
              break;
            case "chart":
              // 后端生成的图表（base64 PNG）
              if (event.image) {
                msg.chart = event.image;
              }
              break;
            case "final":
              // 流结束，内容已完整
              break;
          }
        },
        _abortController.signal,
      );

      backendStatus.value = "已连接";

      // 如果最终内容为空（可能 LLM 没返回 stream），给个兜底
      const finalMsg = messages.value.find((m) => m.id === _streamMsgId);
      if (finalMsg && !finalMsg.content) {
        finalMsg.content = "（未获取到回复）";
      }
    } catch (error) {
      backendStatus.value = "连接失败";
      const msg = messages.value.find((m) => m.id === _streamMsgId);
      const errMsg = error instanceof Error ? error.message : "未知错误";
      const displayMsg = error instanceof Error ? toUserError(error.message) : "未知错误";
      if (msg) {
        msg.content = displayMsg;
      }
    } finally {
      loading.value = false;
      _abortController = null;
    }
  }

  function cancelMessage(): void {
    if (_abortController) {
      _abortController.abort();
      _abortController = null;
    }
    loading.value = false;
  }

  return {
    backendStatus,
    canSend,
    cancelMessage,
    input,
    loading,
    messages,
    nowTime,
    sendMessage,
    suggestions,
  };
});
