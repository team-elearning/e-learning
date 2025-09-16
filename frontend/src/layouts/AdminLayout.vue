<template>
  <!-- Shell full screen -->
  <div class="h-screen w-screen overflow-hidden bg-gray-100">
    <div class="flex h-full">
      <!-- Sidebar (desktop) -->
      <aside class="hidden md:flex w-64 shrink-0 flex-col border-r bg-white">
        <Sidebar />
      </aside>

      <!-- Main column -->
      <div class="flex min-w-0 flex-1 flex-col">
        <!-- Navbar (sticky) -->
        <header
          class="sticky top-0 z-20 h-14 border-b bg-white"
          style="height: 67px; box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1)"
        >
          <Navbar />
        </header>

        <!-- Content scroll riêng, không kéo cả trang -->
        <main class="min-h-0 flex-1 overflow-y-auto bg-gray-50 p-4">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import Sidebar from '@/components/shared/Sidebar.vue'
import Navbar from '@/components/shared/Navbar.vue'
</script>
