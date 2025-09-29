<template>
  <nav class="h-full">
    <div class="mx-auto flex h-full max-w-7xl items-center justify-between px-4">
      <!-- Left: logo + brand -->
      <div class="flex items-center gap-3">
        <RouterLink to="/student/dashboard" class="flex items-center gap-2">
          <div class="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600/10">
            <span class="text-lg">🎓</span>
          </div>
          <span class="hidden text-base font-semibold text-emerald-700 sm:inline">
            My Learning
          </span>
        </RouterLink>
      </div>

      <!-- Center: menu (desktop) -->
      <ul class="hidden items-center gap-2 md:flex">
        <li v-for="item in menu" :key="item.path">
          <RouterLink
            :to="item.path"
            class="rounded px-3 py-2 text-sm transition"
            :class="
              isActive(item.path)
                ? 'bg-emerald-50 text-emerald-700 font-medium'
                : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
            "
          >
            {{ item.label }}
          </RouterLink>
        </li>
      </ul>

      <!-- Right: actions -->
      <div class="flex items-center gap-2">
        <button class="rounded p-2 hover:bg-gray-100" aria-label="Notifications">🔔</button>

        <!-- Avatar dropdown (placeholder) -->
        <div class="relative">
          <button
            class="flex items-center gap-2 rounded px-2 py-1 hover:bg-gray-100"
            @click="avatarOpen = !avatarOpen"
          >
            <img
              class="h-8 w-8 rounded-full object-cover"
              src="https://i.pravatar.cc/80?img=10"
              alt="avatar"
            />
            <span class="hidden text-sm sm:inline">Học sinh</span>
          </button>
          <div
            v-if="avatarOpen"
            class="absolute right-0 z-30 mt-2 w-40 rounded-md border bg-white p-1 shadow-lg"
            @click.outside="avatarOpen = false"
          >
            <RouterLink
              to="/student/account/profile"
              class="block rounded px-3 py-2 text-sm hover:bg-gray-50"
              @click="avatarOpen = false"
            >
              Tài khoản
            </RouterLink>
            <button
              class="block w-full rounded px-3 py-2 text-left text-sm text-red-600 hover:bg-red-50"
              @click="onLogout"
            >
              Đăng xuất
            </button>
          </div>
        </div>

        <!-- Hamburger (mobile) -->
        <button
          class="rounded p-2 hover:bg-gray-100 md:hidden"
          @click="open = !open"
          aria-label="Open menu"
          aria-expanded="true"
        >
          ☰
        </button>
      </div>
    </div>

    <!-- Mobile dropdown menu -->
    <div v-if="open" class="border-t bg-white md:hidden">
      <div class="mx-auto max-w-7xl px-2 py-2">
        <RouterLink
          v-for="item in menu"
          :key="item.path"
          :to="item.path"
          class="block rounded px-3 py-2 text-sm"
          :class="
            isActive(item.path)
              ? 'bg-emerald-50 text-emerald-700 font-medium'
              : 'text-gray-700 hover:bg-gray-50'
          "
          @click="open = false"
        >
          {{ item.label }}
        </RouterLink>
      </div>
    </div>
  </nav>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth.store'
const auth = useAuthStore()

const route = useRoute()
const open = ref(false)
const avatarOpen = ref(false)

const menu = [
  { path: '/student/dashboard', label: 'Trang chủ' },
  { path: '/student/courses', label: 'Khóa học' },
  { path: '/student/exams', label: 'Ôn luyện & Thi' },
  { path: '/student/payments', label: 'Thanh toán' },
  { path: '/student/account/profile', label: 'Tài khoản' },
]

function isActive(path: string) {
  // active nếu route hiện tại bắt đầu bằng path menu
  return route.path === path || route.path.startsWith(path + '/')
}
function onLogout() {
  avatarOpen.value = false
  open.value = false
  auth.logout()
}
</script>
