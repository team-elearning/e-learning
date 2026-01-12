<script setup lang="ts">
import TeacherNavbar from '@/shared/components/TeacherNavbar.vue'
</script>

<template>
  <div class="min-h-screen" :style="{ background: 'rgb(var(--bg))' }">
    <TeacherNavbar />
    <main class="mx-auto max-w-6xl px-4 py-6">
      <router-view />
    </main>
  </div>
</template>
