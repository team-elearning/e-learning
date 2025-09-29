<template>
  <div class="h-screen w-screen overflow-hidden bg-gray-100">
    <div class="flex h-full">
      <!-- Sidebar -->
      <aside class="hidden md:flex w-64 shrink-0 flex-col border-r bg-white">
        <AdminSidebar />
      </aside>

      <!-- Main -->
      <div class="flex min-w-0 flex-1 flex-col">
        <header class="sticky top-0 z-20 h-14 border-b bg-white">
          <AdminNavbar />
        </header>

        <main class="min-h-0 flex-1 overflow-y-auto bg-gray-50 p-4">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import AdminSidebar from '@/components/shared/AdminSidebar.vue'
import AdminNavbar from '@/components/shared/AdminNavbar.vue'
</script>
