<!-- src/components/shared/AdminNavbar.vue -->
<template>
  <header class="flex h-full items-center justify-between px-4">
    <!-- Left: dynamic title -->
    <div class="min-w-0">
      <h1 class="truncate text-base font-semibold text-gray-800">
        {{ pageTitle }}
      </h1>
    </div>

    <!-- Right: actions -->
    <div class="flex items-center gap-2">
      <button class="rounded p-2 hover:bg-gray-100" aria-label="Notifications">
        <Bell class="h-5 w-5" />
      </button>

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
        class="ml-2 inline-flex items-center gap-2 rounded bg-red-500 px-3 py-1 text-sm text-white hover:bg-red-600"
        @click="onLogout"
      >
        <LogOut class="h-4 w-4" /> Đăng xuất
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth.store'
import { Bell, LogOut } from 'lucide-vue-next'

const auth = useAuthStore()
const user = computed(() => auth.user)

const route = useRoute()
const pageTitle = computed(() => {
  const matched = [...route.matched].reverse().find((r) => r.meta?.title) as any
  return matched?.meta?.title || 'Admin'
})

const onLogout = () => auth.logout()
</script>
