<script setup lang="ts">
import StudentNavbar from '@/shared/components/StudentNavbar.vue'
</script>

<template>
  <div class="min-h-screen bg-slate-50">
    <StudentNavbar />
    <main>
      <router-view />
    </main>
  </div>
</template>
