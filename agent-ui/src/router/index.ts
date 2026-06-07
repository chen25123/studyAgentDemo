import { createRouter, createWebHistory } from "vue-router";

import BugMetricsView from "../views/BugMetricsView.vue";
import ChatView from "../views/ChatView.vue";
import LlmTraceView from "../views/LlmTraceView.vue";
import ReqMetricsView from "../views/ReqMetricsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/chat" },
    { path: "/chat", name: "chat", component: ChatView },
    { path: "/quality/bugs", name: "bug-metrics", component: BugMetricsView },
    { path: "/quality/requirements", name: "req-metrics", component: ReqMetricsView },
    { path: "/admin/llm-traces", name: "llm-traces", component: LlmTraceView },
  ],
});
