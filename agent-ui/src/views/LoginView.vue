<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useAuthStore } from "../stores/authStore";

const username = ref("");
const password = ref("");
const error = ref("");
const loading = ref(false);
const router = useRouter();
const auth = useAuthStore();

async function doLogin(): Promise<void> {
  error.value = "";
  loading.value = true;
  try {
    await auth.login(username.value, password.value);
    await auth.loadUser();
    router.push({ name: "chat" });
  } catch {
    error.value = "用户名或密码错误";
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="login-page">
    <form class="login-form" @submit.prevent="doLogin">
      <h1>DevFlow Agent</h1>
      <p>研发流程智能助手</p>

      <p v-if="error" class="login-error">{{ error }}</p>

      <label>用户名</label>
      <input v-model="username" type="text" autocomplete="username" />

      <label>密码</label>
      <input v-model="password" type="password" autocomplete="current-password" />

      <button type="submit" :disabled="loading || !username || !password">
        {{ loading ? "登录中..." : "登录" }}
      </button>

      <p class="login-hint">默认管理员：user_0001 / admin123</p>
    </form>
  </main>
</template>
