<template>
  <nav class="sticky top-0 z-50 h-16 bg-white/80 backdrop-blur-md border-b border-gray-200/80">
    <div
      class="mx-auto flex h-full max-w-screen-2xl items-center justify-between px-4 sm:px-6 lg:px-8"
    >
      <div class="flex items-center gap-4">
        <RouterLink to="/teacher/dashboard" class="text-xl font-bold tracking-tight text-gray-800">
          <LogoEduriot :size="80" primary="#3B82F6" accent="#14B8A6" />
        </RouterLink>
      </div>

      <ul class="hidden items-center gap-2 md:flex">
        <li v-for="item in menu" :key="item.path">
          <RouterLink
            :to="item.path"
            class="relative rounded-md px-3 py-2 text-sm transition-colors duration-200 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
            :class="
              isActive(item.path)
                ? 'font-semibold text-blue-600'
                : 'text-gray-500 hover:text-gray-900'
            "
          >
            <span>{{ item.label }}</span>
            <Transition
              enter-active-class="transition-all duration-300 ease-out"
              enter-from-class="w-0 opacity-0"
              enter-to-class="w-1/2 opacity-100"
              leave-active-class="transition-all duration-200 ease-in"
              leave-from-class="w-1/2 opacity-100"
              leave-to-class="w-0 opacity-0"
            >
              <span
                v-if="isActive(item.path)"
                class="absolute bottom-0 left-1/2 -translate-x-1/2 h-0.5 bg-blue-600 rounded-full"
              ></span>
            </Transition>
          </RouterLink>
        </li>
      </ul>

      <div class="flex items-center gap-3">
        <button
          class="rounded-full p-2 text-gray-500 hover:bg-gray-100 hover:text-gray-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-2"
          aria-label="Notifications"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            stroke-width="2"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6 6 0 10-12 0v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
        </button>

        <div class="relative" ref="avatarWrapper">
          <button
            @click="avatarOpen = !avatarOpen"
            class="flex items-center gap-2 rounded-full transition-shadow duration-200 hover:shadow-md focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 ring-offset-2"
            aria-label="User menu"
            :aria-expanded="avatarOpen"
          >
            <img
              class="h-9 w-9 rounded-full object-cover"
              src="https://i.pravatar.cc/80?img=5"
              alt="User avatar"
            />
          </button>

          <Transition
            enter-active-class="transition ease-out duration-100"
            enter-from-class="transform opacity-0 scale-95"
            enter-to-class="transform opacity-100 scale-100"
            leave-active-class="transition ease-in duration-75"
            leave-from-class="transform opacity-100 scale-100"
            leave-to-class="transform opacity-0 scale-95"
          >
            <div
              v-if="avatarOpen"
              class="absolute right-0 z-30 mt-2 w-56 origin-top-right rounded-xl border bg-white p-2 shadow-xl shadow-gray-400/10 ring-1 ring-black ring-opacity-5 focus:outline-none"
            >
              <div class="px-2 py-2 border-b">
                <p class="text-sm font-semibold text-gray-800">{{ user?.name || 'Giáo viên' }}</p>
                <p class="text-xs text-gray-500 truncate">
                  {{ user?.email || 'teacher@example.com' }}
                </p>
              </div>
              <div class="py-1">
                <RouterLink
                  to="/teacher/account/profile"
                  class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-gray-700 hover:bg-gray-100"
                  @click="avatarOpen = false"
                  >Tài khoản</RouterLink
                >
              </div>
              <div class="py-1">
                <button
                  @click="onLogout"
                  class="flex w-full items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-600 hover:bg-red-50"
                >
                  Đăng xuất
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <div class="md:hidden">
          <button
            @click="open = !open"
            class="relative h-10 w-10 flex items-center justify-center rounded-full hover:bg-gray-100 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
            aria-label="Open main menu"
            :aria-expanded="open"
          >
            <div class="space-y-1.5">
              <span
                class="block w-5 h-0.5 bg-gray-600 transition-transform duration-300 ease-out"
                :class="{ 'rotate-45 translate-y-2': open }"
              ></span>
              <span
                class="block w-5 h-0.5 bg-gray-600 transition-opacity duration-300 ease-out"
                :class="{ 'opacity-0': open }"
              ></span>
              <span
                class="block w-5 h-0.5 bg-gray-600 transition-transform duration-300 ease-out"
                :class="{ '-rotate-45 -translate-y-2': open }"
              ></span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 -translate-y-2"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-2"
    >
      <div v-if="open" class="md:hidden border-t border-gray-200/80 bg-white/95 backdrop-blur-md">
        <div class="space-y-1 px-2 pt-2 pb-3">
          <RouterLink
            v-for="item in menu"
            :key="item.path"
            :to="item.path"
            class="block rounded-md px-3 py-2 text-base font-medium"
            :class="
              isActive(item.path) ? 'bg-blue-50 text-blue-700' : 'text-gray-600 hover:bg-gray-100'
            "
            @click="open = false"
          >
            {{ item.label }}
          </RouterLink>
        </div>
      </div>
    </Transition>
  </nav>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/store/auth.store'
import { onClickOutside } from '@vueuse/core'
import LogoEduriot from '@/components/ui/LogoEduriot.vue'

const auth = useAuthStore()
const user = computed(() => auth.user)

const menu = [
  { path: '/teacher/dashboard', label: 'Dashboard' },
  { path: '/teacher/courses', label: 'Khóa học' },
  { path: '/teacher/classes', label: 'Lớp học' },
  { path: '/teacher/exams', label: 'Bài kiểm tra' },
  { path: '/teacher/students', label: 'Học sinh' },
]

const route = useRoute()
const isActive = (path: string) =>
  route.path === path || (path !== '/teacher/dashboard' && route.path.startsWith(path + '/'))

// States for menus
const open = ref(false)
const avatarOpen = ref(false)

const onLogout = () => {
  avatarOpen.value = false
  auth.logout()
}

// Click outside handler for avatar menu
const avatarWrapper = ref(null)
onClickOutside(avatarWrapper, () => {
  avatarOpen.value = false
})
</script>
