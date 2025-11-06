<!-- src/components/navbar/StudentNavbar.vue -->
<template>
  <nav class="sticky top-0 z-50 h-16 bg-white/90 backdrop-blur-lg border-b border-gray-200/80 shadow-sm">
    <div class="mx-auto flex h-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
      <!-- Logo -->
      <div class="flex items-center gap-3">
        <RouterLink 
          to="/student/dashboard" 
          class="logo-wrapper group relative inline-block transition-transform duration-[400ms] ease-[cubic-bezier(0.34,1.56,0.64,1)] hover:scale-[1.08] hover:-rotate-[3deg]"
        >
          <div class="logo-glow absolute inset-[-15px] rounded-full bg-[radial-gradient(circle,rgba(59,130,246,0.3)_0%,rgba(20,184,166,0.2)_30%,transparent_70%)] opacity-0 blur-[20px] transition-all duration-500 ease-out animate-float group-hover:opacity-100 group-hover:scale-110"></div>
          <LogoEduriot :size="90" primary="#3B82F6" accent="#14B8A6" class="relative z-10" />
        </RouterLink>
      </div>

      <!-- Desktop Menu -->
      <ul class="hidden items-center gap-2 md:flex">
        <li v-for="item in menu" :key="item.path">
          <RouterLink
            :to="item.path"
            @click="handleClick(item.path)"
            class="group relative rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
            :class="isActive(item.path) ? 'text-emerald-600' : 'text-gray-600 hover:text-gray-900'"
          >
            <span class="absolute inset-0 -z-10 rounded-lg bg-gradient-to-r from-emerald-50 to-blue-50 opacity-0 transition-all duration-300 group-hover:opacity-100"></span>
            <span class="relative z-10">{{ item.label }}</span>
            <span 
              class="absolute bottom-0 left-1/2 h-0.5 -translate-x-1/2 rounded-full bg-gradient-to-r from-emerald-500 via-blue-500 to-emerald-500 bg-[length:200%_100%] transition-all duration-500"
              :class="isActive(item.path) ? 'w-4/5 animate-gradient-x' : 'w-0 group-hover:w-4/5'"
            ></span>
            <span 
              v-if="clickedItem === item.path" 
              class="absolute inset-0 rounded-lg bg-[radial-gradient(circle,rgba(16,185,129,0.4)_0%,transparent_70%)] pointer-events-none animate-ripple-out"
            ></span>
          </RouterLink>
        </li>
      </ul>

      <!-- Right side actions -->
      <div class="flex items-center gap-3">
        <!-- Notification Bell Component -->
        <NotificationBell :user-id="auth.user?.id" role="student" />

        <!-- Avatar Dropdown -->
        <div class="relative" ref="avatarWrapper">
          <button
            @click="avatarOpen = !avatarOpen"
            class="group relative flex items-center gap-2 transition-all duration-300 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
          >
            <div class="relative">
              <!-- Glow ring -->
              <div class="absolute inset-[-4px] rounded-full bg-gradient-to-br from-emerald-500/50 via-blue-500/50 to-emerald-500/50 bg-[length:200%_200%] opacity-0 blur-[8px] transition-opacity duration-400 animate-gradient-rotate group-hover:opacity-100"></div>
              
              <!-- Avatar image -->
              <img
                class="relative z-10 h-10 w-10 rounded-full object-cover ring-2 ring-white shadow-md transition-all duration-300 group-hover:ring-emerald-400"
                :src="avatarSrc"
                alt="avatar"
              />
              
              <!-- Online status indicator -->
              <span class="absolute -bottom-0.5 -right-0.5 flex items-center justify-center z-20">
                <span class="absolute h-3 w-3 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-400 animate-pulse-custom"></span>
                <span class="relative h-2.5 w-2.5 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-400 border-2 border-white shadow-[0_0_0_1px_rgba(16,185,129,0.2),0_2px_4px_rgba(0,0,0,0.2)]"></span>
              </span>
            </div>
          </button>

          <!-- Dropdown Menu -->
          <Transition
            enter-active-class="transition ease-out duration-200"
            enter-from-class="transform opacity-0 scale-90 -translate-y-3"
            enter-to-class="transform opacity-100 scale-100 translate-y-0"
            leave-active-class="transition ease-in duration-150"
            leave-from-class="transform opacity-100 scale-100 translate-y-0"
            leave-to-class="opacity-0 scale-90 -translate-y-3"
          >
            <div
              v-if="avatarOpen"
              class="absolute right-0 z-30 mt-3 w-56 origin-top-right rounded-2xl border border-gray-200/50 bg-white/95 p-2 shadow-2xl shadow-gray-400/20 backdrop-blur-xl ring-1 ring-black/5"
            >
              <!-- User info -->
              <div class="px-3 py-3 border-b border-gray-100 mb-2">
                <div class="flex items-center gap-2 mb-1">
                  <p class="text-sm font-semibold text-gray-800">{{ displayName }}</p>
                  <span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full bg-gradient-to-br from-emerald-100 to-emerald-50 text-[10px] font-semibold text-emerald-700">
                    <span class="h-1.5 w-1.5 rounded-full bg-gradient-to-br from-emerald-500 to-emerald-400 animate-pulse"></span>
                    Online
                  </span>
                </div>
                <p class="text-xs text-gray-500 truncate">{{ displayEmail }}</p>
              </div>

              <!-- Menu items -->
              <div class="py-1 space-y-1">
                <!-- ⭐ THÊM LẠI PROFILE LINK ⭐ -->
                <RouterLink
                  to="/student/account/profile"
                  class="menu-item group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-gray-700 transition-all duration-300 hover:bg-gradient-to-r hover:from-emerald-50 hover:to-blue-50 hover:text-emerald-700 hover:translate-x-1"
                  @click="avatarOpen = false"
                >
                  <svg
                    class="h-5 w-5 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-12"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                    />
                  </svg>
                  <span>Tài khoản</span>
                </RouterLink>

                <!-- Logout button -->
                <button
                  @click="showConfirm = true"
                  class="menu-item group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-red-600 transition-all duration-300 hover:bg-red-50 hover:translate-x-1"
                >
                  <svg
                    class="h-5 w-5 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-12"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      stroke-width="2"
                      d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                    />
                  </svg>
                  <span>Đăng xuất</span>
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <!-- Mobile Menu Button -->
        <div class="md:hidden">
          <button
            @click="open = !open"
            class="relative h-11 w-11 rounded-xl transition-all duration-300 hover:bg-gradient-to-br hover:from-emerald-50 hover:to-blue-50 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50"
            aria-label="Mở menu"
          >
            <div class="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 flex flex-col gap-[5px]">
              <span 
                class="block w-5 h-0.5 bg-gradient-to-r from-gray-600 to-gray-800 rounded-sm transition-all duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] origin-center"
                :class="{ 'rotate-45 translate-y-[7px]': open }"
              ></span>
              <span 
                class="block w-5 h-0.5 bg-gradient-to-r from-gray-600 to-gray-800 rounded-sm transition-all duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)]"
                :class="{ 'opacity-0 scale-0': open }"
              ></span>
              <span 
                class="block w-5 h-0.5 bg-gradient-to-r from-gray-600 to-gray-800 rounded-sm transition-all duration-300 ease-[cubic-bezier(0.34,1.56,0.64,1)] origin-center"
                :class="{ '-rotate-45 -translate-y-[7px]': open }"
              ></span>
            </div>
          </button>
        </div>
      </div>
    </div>

    <!-- Mobile Menu -->
    <Transition
      enter-active-class="transition ease-out duration-300"
      enter-from-class="opacity-0 -translate-y-4"
      enter-to-class="opacity-100 translate-y-0"
      leave-active-class="transition ease-in duration-200"
      leave-from-class="opacity-100 translate-y-0"
      leave-to-class="opacity-0 -translate-y-4"
    >
      <div
        v-if="open"
        ref="mobileMenuWrapper"
        class="md:hidden border-t border-gray-200/50 bg-white/95 backdrop-blur-xl animate-slide-down"
      >
        <div class="space-y-2 px-3 pt-3 pb-4">
          <RouterLink
            v-for="(item, index) in menu"
            :key="item.path"
            :to="item.path"
            class="mobile-link group flex items-center justify-between rounded-xl px-4 py-3.5 text-base font-medium transition-all duration-300"
            :class="
              isActive(item.path)
                ? 'bg-gradient-to-r from-emerald-50 to-blue-50 text-emerald-700 shadow-sm'
                : 'text-gray-600 hover:bg-gray-50 hover:translate-x-2'
            "
            :style="{ transitionDelay: `${index * 50}ms` }"
            @click="open = false"
          >
            <span>{{ item.label }}</span>
            <svg
              class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-2"
              :class="{ 'text-emerald-600': isActive(item.path) }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 5l7 7-7 7"
              />
            </svg>
          </RouterLink>
        </div>
      </div>
    </Transition>
  </nav>

  <ConfirmLogout
    :open="showConfirm"
    :loading="isLoggingOut"
    @update:open="showConfirm = $event"
    @confirm="handleLogout"
  />
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth.store'
import { onClickOutside } from '@vueuse/core'
import LogoEduriot from '@/components/ui/LogoEduriot.vue'
import ConfirmLogout from '@/components/ui/ConfirmLogout.vue'
import NotificationBell from '@/components/shared/NotificationBell.vue'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const open = ref(false)
const avatarOpen = ref(false)
const showConfirm = ref(false)
const isLoggingOut = ref(false)

const defaultAvatar = 'https://i.pravatar.cc/80?img=10'
const avatarSrc = computed(() => auth.user?.avatar || defaultAvatar)
const displayName = computed(() => auth.user?.name || 'Học sinh')
const displayEmail = computed(() => auth.user?.email || 'student@example.com')

const menu = [
  { path: '/student/dashboard', label: 'Trang chủ' },
  { path: '/student/courses', label: 'Khóa học' },
  { path: '/student/exams', label: 'Ôn luyện & Thi' },
  { path: '/student/payments', label: 'Thanh toán' },
]

// Click outside handlers
const avatarWrapper = ref<HTMLElement | null>(null)
onClickOutside(avatarWrapper, () => {
  avatarOpen.value = false
})

const mobileMenuWrapper = ref<HTMLElement | null>(null)
onClickOutside(mobileMenuWrapper, (event) => {
  const target = event.target as HTMLElement
  const isHamburgerClick = target.closest('button[aria-label="Mở menu"]')
  if (!isHamburgerClick) {
    open.value = false
  }
})

function isActive(path: string) {
  if (path === '/student/dashboard') return route.path === path
  return route.path.startsWith(path)
}

async function handleLogout() {
  try {
    isLoggingOut.value = true
    avatarOpen.value = false
    open.value = false

    if (typeof auth.logout === 'function') {
      await auth.logout()
    }
    localStorage.clear()
  } finally {
    isLoggingOut.value = false
    router.push({ name: 'Login' })
  }
}

const clickedItem = ref<string | null>(null)
let animationTimeout: number | null = null

function handleClick(path: string) {
  clickedItem.value = path
  if (animationTimeout) clearTimeout(animationTimeout)
  animationTimeout = window.setTimeout(() => {
    clickedItem.value = null
  }, 800)
}
</script>

<style scoped>
/* Chỉ giữ lại CSS cho pseudo-elements không thể làm bằng Tailwind */
.menu-item {
  position: relative;
  overflow: hidden;
}

.menu-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  height: 100%;
  width: 3px;
  background: linear-gradient(180deg, #10b981, #3b82f6);
  transform: scaleY(0);
  transform-origin: top;
  transition: transform 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);
  border-radius: 0 3px 3px 0;
}

.menu-item:hover::before {
  transform: scaleY(1);
}

.mobile-link {
  position: relative;
  overflow: hidden;
}

.mobile-link::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, #10b981, #3b82f6);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.mobile-link:hover::after {
  transform: scaleX(1);
}

/* Accessibility: Reduce motion for users who prefer it */
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
</style>
