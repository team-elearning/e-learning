<template>
  <!-- Brand tone: indigo -->
  <div class="h-screen w-screen overflow-hidden bg-gray-100">
    <div class="flex h-full">
      <!-- Sidebar (ẩn trên mobile) -->
      <!-- <aside class="hidden md:flex w-64 shrink-0 flex-col border-r bg-white">
        <TeacherSidebar />
      </aside> -->

      <!-- Cột phải -->
      <div class="flex min-w-0 flex-1 flex-col">
        <!-- Navbar dính trên -->
        <header class="sticky top-0 z-20 h-14 border-b bg-white">
          <TeacherNavbar />
        </header>

        <!-- Nội dung: chỉ phần này được cuộn -->
        <main class="min-h-0 flex-1 overflow-y-auto bg-gray-50 p-4">
          <router-view />
        </main>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// import TeacherSidebar from '@/components/shared/TeacherSidebar.vue'
import TeacherNavbar from '@/components/shared/TeacherNavbar.vue'
</script>
