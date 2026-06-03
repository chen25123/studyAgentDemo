import { createRouter, createWebHistory } from "vue-router";

import ChatView from "../views/ChatView.vue";
import LlmTraceView from "../views/LlmTraceView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/chat",
    },
    {
      path: "/chat",
      name: "chat",
      component: ChatView,
    },
    {
      path: "/admin/llm-traces",
      name: "llm-traces",
      component: LlmTraceView,
    },
  ],
});
