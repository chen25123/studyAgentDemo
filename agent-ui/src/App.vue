<script setup lang="ts">
import { onMounted } from "vue";
import AppShell from "./components/layout/AppShell.vue";
import { useAuthStore } from "./stores/authStore";

const auth = useAuthStore();

onMounted(async () => {
  if (auth.isLoggedIn() && !auth.user) {
    await auth.loadUser();
  }
});
</script>

<template>
  <AppShell />
</template>
