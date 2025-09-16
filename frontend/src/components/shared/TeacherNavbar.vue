<template>
  <nav class="flex h-full items-center justify-between px-4">
    <!-- Left -->
    <div class="flex items-center gap-3 min-w-0">
      <div class="h-8 w-8 flex items-center justify-center rounded-full bg-indigo-600/10">📘</div>
      <div class="truncate font-semibold text-indigo-700">Teacher Center</div>
    </div>

    <!-- Right -->
    <div class="flex items-center gap-3">
      <!-- (tùy chọn) menu nhanh -->
      <RouterLink
        to="/teacher/dashboard"
        class="hidden md:inline rounded px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900"
      >
        Dashboard
      </RouterLink>
      <RouterLink
        to="/teacher/courses"
        class="hidden md:inline rounded px-3 py-1 text-sm text-gray-600 hover:bg-gray-50 hover:text-gray-900"
      >
        Khóa học
      </RouterLink>

      <button class="rounded p-2 hover:bg-gray-100" aria-label="Notifications">🔔</button>

      <div class="hidden sm:flex flex-col items-end">
        <span class="text-sm font-medium leading-4">{{ user?.name || 'Giáo viên' }}</span>
        <span class="text-xs text-gray-500 leading-4">{{
          user?.email || 'teacher@example.com'
        }}</span>
      </div>

      <img
        class="h-8 w-8 rounded-full object-cover"
        src="https://i.pravatar.cc/80?img=5"
        alt="avatar"
      />

      <button
        class="ml-2 rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
        @click="onLogout"
      >
        Đăng xuất
      </button>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/store/auth.store'

const auth = useAuthStore()
const user = computed(() => auth.user)
const onLogout = () => auth.logout()
</script>
