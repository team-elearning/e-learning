<template>
  <div class="h-screen w-screen overflow-hidden bg-gray-100">
    <div class="flex h-full flex-col">
      <header class="sticky top-0 z-20 h-14 border-b bg-white">
        <StudentNavbar />
      </header>
      <main class="min-h-0 flex-1 overflow-y-auto bg-gray-50 p-4">
        <router-view />
      </main>
      <!-- Nếu muốn bottom nav cho mobile: thêm component ở đây -->
      <!-- <StudentBottomNav class="md:hidden" /> -->
    </div>
  </div>
</template>

<script setup lang="ts">
import StudentNavbar from '@/components/shared/StudentNavbar.vue'
</script>
