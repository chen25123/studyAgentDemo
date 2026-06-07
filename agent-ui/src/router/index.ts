import { createRouter, createWebHistory } from "vue-router";

import BugMetricsView from "../views/BugMetricsView.vue";
import ChatView from "../views/ChatView.vue";
import LlmTraceView from "../views/LlmTraceView.vue";
import LoginView from "../views/LoginView.vue";
import ReqMetricsView from "../views/ReqMetricsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/chat" },
    { path: "/login", name: "login", component: LoginView },
    { path: "/chat", name: "chat", component: ChatView, meta: { requiresAuth: true } },
    { path: "/quality/bugs", name: "bug-metrics", component: BugMetricsView, meta: { requiresAuth: true } },
    { path: "/quality/requirements", name: "req-metrics", component: ReqMetricsView, meta: { requiresAuth: true } },
    { path: "/admin/llm-traces", name: "llm-traces", component: LlmTraceView, meta: { requiresAuth: true } },
  ],
});

router.beforeEach((to, _from, next) => {
  const token = localStorage.getItem("token");
  if (to.meta.requiresAuth && !token) {
    next({ name: "login" });
  } else if (to.name === "login" && token) {
    next({ name: "chat" });
  } else {
    next();
  }
});
