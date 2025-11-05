<!-- src/components/shared/AdminNavbar.vue -->
<template>
  <header class="flex h-full items-center justify-between px-4">
    <!-- Left: Hamburger + dynamic title -->
    <div class="flex items-center min-w-0 gap-2">
      <!-- Hamburger menu, chỉ hiện trên mobile -->
      <button
        class="mr-2 flex md:hidden items-center justify-center rounded p-2 hover:bg-gray-100"
        aria-label="Mở menu"
        @click="$emit('toggle-sidebar')"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          class="h-6 w-6"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 6h16M4 12h16M4 18h16"
          />
        </svg>
      </button>
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
        @click="showConfirm = true"
      >
        <LogOut class="h-4 w-4" /> Đăng xuất
      </button>
    </div>
    <ConfirmLogout
      :open="showConfirm"
      @update:open="showConfirm = $event"
      @confirm="handleLogout"
    />
  </header>
</template>

<script setup lang="ts">
import { ref, computed, defineEmits } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth.store'
import ConfirmLogout from '@/components/ui/ConfirmLogout.vue'
import { Bell, LogOut } from 'lucide-vue-next'

const emit = defineEmits(['toggle-sidebar'])

const auth = useAuthStore()
const user = computed(() => auth.user)

const route = useRoute()
const router = useRouter()

const pageTitle = computed(() => {
  const matched = [...route.matched].reverse().find((r) => r.meta?.title) as any
  return matched?.meta?.title || 'Admin'
})

// Confirm popup
const showConfirm = ref(false)

async function handleLogout() {
  try {
    if (typeof auth.logout === 'function') {
      await auth.logout()
    } else {
      // localStorage.removeItem('access')
      // localStorage.removeItem('accessToken')
      // localStorage.removeItem('refresh')
      localStorage.clear()
    }
  } finally {
    router.push({ name: 'Login', query: {} })
  }
}
</script>
