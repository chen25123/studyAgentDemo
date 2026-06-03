<script setup lang="ts">
import SidebarNav from "./SidebarNav.vue";
</script>

<template>
  <main class="app-shell">
    <SidebarNav />
    <RouterView />
  </main>
</template>
