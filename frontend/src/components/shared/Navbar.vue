<template>
  <header class="flex h-full items-center justify-between px-4">
    <!-- Left -->
    <div class="flex items-center gap-3 min-w-0">
      <div class="truncate font-semibold text-gray-700">Admin Dashboard</div>
    </div>

    <!-- Right -->
    <div class="flex items-center gap-3">
      <button class="rounded p-2 hover:bg-gray-100" aria-label="Notifications">🔔</button>

      <div class="hidden sm:flex flex-col items-end">
        <span class="text-sm font-medium leading-4">{{ user?.name || 'Admin' }}</span>
        <span class="text-xs text-gray-500 leading-4">{{
          user?.email || 'admin@example.com'
        }}</span>
      </div>

      <img
        class="h-8 w-8 rounded-full object-cover"
        src="https://i.pravatar.cc/80?img=3"
        alt="avatar"
      />

      <button
        class="ml-2 rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
        @click="onLogout"
      >
        Đăng xuất
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useAuthStore } from '@/store/auth.store'

const auth = useAuthStore()
const user = computed(() => auth.user)
const onLogout = () => auth.logout()
</script>
