<!-- src/components/navbar/TeacherNavbar.vue -->
<template>
  <nav class="sticky top-0 z-50 h-16 bg-white/90 backdrop-blur-lg border-b border-gray-200/80 shadow-sm">
    <div class="mx-auto flex h-full max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
      <div class="flex items-center gap-3">
        <RouterLink to="/teacher/dashboard" class="logo-wrapper group relative">
          <div class="logo-glow-bg"></div>
          <LogoEduriot :size="90" primary="#3B82F6" accent="#14B8A6" class="relative z-10" />
        </RouterLink>
      </div>

      <ul class="hidden items-center gap-2 md:flex">
        <li v-for="item in menu" :key="item.path">
          <RouterLink
            :to="item.path"
            @click="handleClick(item.path)"
            class="nav-link group relative rounded-lg px-4 py-2.5 text-sm font-medium transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50"
            :class="isActive(item.path) ? 'text-blue-600' : 'text-gray-600 hover:text-gray-900'"
          >
            <span class="absolute inset-0 -z-10 rounded-lg bg-gradient-to-r from-sky-50 via-blue-50 to-cyan-50 opacity-0 transition-all duration-300 group-hover:opacity-100"></span>
            <span class="relative z-10">{{ item.label }}</span>
            <span
              class="absolute bottom-0 left-1/2 h-0.5 -translate-x-1/2 rounded-full bg-gradient-to-r from-sky-500 via-blue-500 to-cyan-500 bg-[length:200%_100%] transition-all duration-500"
              :class="isActive(item.path) ? 'w-4/5 animate-gradient-x' : 'w-0 group-hover:w-4/5'"
            ></span>
            <span v-if="clickedItem === item.path" class="ripple-effect"></span>
          </RouterLink>
        </li>
      </ul>

      <div class="flex items-center gap-3">
        <button
          class="group relative rounded-full p-2.5 transition-all duration-300 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50"
          :class="hasNotifications
            ? 'text-blue-600 hover:bg-gradient-to-br hover:from-sky-50 hover:via-blue-50 hover:to-cyan-50'
            : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'"
          aria-label="Thông báo"
          aria-live="polite"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            class="h-6 w-6 transition-transform duration-300"
            :class="hasNotifications
              ? 'group-hover:rotate-12 group-hover:scale-110'
              : 'group-hover:rotate-6 group-hover:scale-105'"
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
          <span v-if="hasNotifications" class="notification-badge">
            <span class="notification-ping"></span>
            <span class="notification-dot"></span>
          </span>
        </button>

        <div class="relative" ref="avatarWrapper">
          <button
            @click="avatarOpen = !avatarOpen"
            class="avatar-btn group relative flex items-center gap-2 transition-all duration-300 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50"
          >
            <div class="avatar-container relative">
              <div class="avatar-glow-ring"></div>
              <img
                class="relative z-10 h-10 w-10 rounded-full object-cover ring-2 ring-white shadow-md transition-all duration-300 group-hover:ring-blue-400"
                :src="avatarSrc"
                alt="avatar"
              />
              <span class="online-status">
                <span class="online-pulse"></span>
                <span class="online-dot"></span>
              </span>
            </div>
          </button>

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
              class="dropdown-menu absolute right-0 z-30 mt-3 w-56 origin-top-right rounded-2xl border border-gray-200/50 bg-white/95 p-2 shadow-2xl shadow-gray-400/20 backdrop-blur-xl ring-1 ring-black/5"
            >
              <div class="user-info px-3 py-3 border-b border-gray-100 mb-2">
                <div class="flex items-center gap-2 mb-1">
                  <p class="text-sm font-semibold text-gray-800">{{ displayName }}</p>
                  <span class="status-badge">
                    <span class="status-dot"></span>
                    Online
                  </span>
                </div>
                <p class="text-xs text-gray-500 truncate">{{ displayEmail }}</p>
              </div>

              <div class="py-1 space-y-1">
                <RouterLink
                  to="/teacher/account/profile"
                  class="menu-item group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-gray-700 transition-all duration-300 hover:bg-gradient-to-r hover:from-sky-50 hover:via-blue-50 hover:to-cyan-50 hover:text-blue-700 hover:translate-x-1"
                  @click="avatarOpen = false"
                >
                  <svg class="h-5 w-5 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                  </svg>
                  <span class="flex-1">Tài khoản</span>
                  <svg class="h-4 w-4 opacity-0 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </RouterLink>

                <button
                  @click="onLogout"
                  class="menu-item group flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-sm text-red-600 transition-all duration-300 hover:bg-red-50 hover:translate-x-1"
                >
                  <svg class="h-5 w-5 transition-transform duration-300 group-hover:scale-110 group-hover:rotate-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                  </svg>
                  <span class="flex-1">Đăng xuất</span>
                  <svg class="h-4 w-4 opacity-0 transition-all duration-300 group-hover:opacity-100 group-hover:translate-x-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
            </div>
          </Transition>
        </div>

        <div class="md:hidden">
          <button
            @click="open = !open"
            class="hamburger-btn relative h-11 w-11 rounded-xl transition-all duration-300 hover:bg-gradient-to-br hover:from-sky-50 hover:via-blue-50 hover:to-cyan-50 hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500/50"
            aria-label="Mở menu"
          >
            <div class="hamburger-icon">
              <span :class="{ 'rotate-45 translate-y-2': open }"></span>
              <span :class="{ 'opacity-0 scale-0': open }"></span>
              <span :class="{ '-rotate-45 -translate-y-2': open }"></span>
            </div>
          </button>
        </div>
      </div>
    </div>

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
        class="mobile-menu md:hidden border-t border-gray-200/50 bg-white/95 backdrop-blur-xl"
      >
        <div class="space-y-2 px-3 pt-3 pb-4">
          <RouterLink
            v-for="(item, index) in menu"
            :key="item.path"
            :to="item.path"
            class="mobile-link group flex items-center justify-between rounded-xl px-4 py-3.5 text-base font-medium transition-all duration-300"
            :class="isActive(item.path)
              ? 'bg-gradient-to-r from-sky-50 via-blue-50 to-cyan-50 text-blue-700 shadow-sm'
              : 'text-gray-600 hover:bg-gray-50 hover:translate-x-2'"
            :style="{ transitionDelay: `${index * 50}ms` }"
            @click="open = false"
          >
            <span>{{ item.label }}</span>
            <svg
              class="h-5 w-5 transition-transform duration-300 group-hover:translate-x-2"
              :class="{ 'text-blue-600': isActive(item.path) }"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
            </svg>
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
const route = useRoute()

const open = ref(false)
const avatarOpen = ref(false)

const TEACHER_NAVBAR_FALLBACK = 'https://i.pravatar.cc/80?img=5'

const avatarSrc = computed(() => auth.user?.avatar || TEACHER_NAVBAR_FALLBACK)
const displayName = computed(() => auth.user?.name || 'Giáo viên')
const displayEmail = computed(() => auth.user?.email || 'teacher@example.com')

const unreadCount = ref(0)
const hasNotifications = computed(() => unreadCount.value > 0)

const menu = [
  { path: '/teacher/dashboard', label: 'Dashboard' },
  { path: '/teacher/courses', label: 'Khóa học' },
  { path: '/teacher/classes', label: 'Lớp học' },
  { path: '/teacher/exams', label: 'Bài kiểm tra' },
  { path: '/teacher/students', label: 'Học sinh' },
]

// Avatar dropdown click outside
const avatarWrapper = ref<HTMLElement | null>(null)
onClickOutside(avatarWrapper, () => { avatarOpen.value = false })

// Mobile menu click outside — giống StudentNavbar
const mobileMenuWrapper = ref<HTMLElement | null>(null)
onClickOutside(mobileMenuWrapper, (event) => {
  const target = event.target as HTMLElement
  // Chỉ đóng khi click KHÔNG phải vào nút hamburger
  const isHamburgerClick = target.closest('.hamburger-btn')
  if (!isHamburgerClick) {
    open.value = false
  }
})

function isActive(path: string) {
  if (path === '/teacher/dashboard') return route.path === path
  return route.path.startsWith(path)
}

function onLogout() {
  avatarOpen.value = false
  open.value = false
  auth.logout()
}

const clickedItem = ref<string | null>(null)
let animationTimeout: number | null = null

function handleClick(path: string) {
  clickedItem.value = path
  if (animationTimeout) clearTimeout(animationTimeout)
  animationTimeout = window.setTimeout(() => { clickedItem.value = null }, 800)
}
</script>

<style scoped>
.logo-wrapper { position: relative; display: inline-block; transition: transform 0.4s cubic-bezier(0.34, 1.56, 0.64, 1); }
.logo-glow-bg { position: absolute; inset: -15px; background: radial-gradient(circle, rgba(14,165,233,0.35) 0%, rgba(59,130,246,0.3) 30%, rgba(6,182,212,0.2) 60%, transparent 80%); border-radius: 50%; opacity: 0; filter: blur(20px); transition: opacity 0.5s ease, transform 0.5s ease; animation: float 3s ease-in-out infinite; }
.logo-wrapper:hover .logo-glow-bg { opacity: 1; transform: scale(1.2); }
.logo-wrapper:hover { transform: scale(1.08) rotate(-3deg); }
@keyframes float { 0%,100%{transform:translateY(0) scale(1)} 50%{transform:translateY(-5px) scale(1.05)} }

.nav-link { position: relative; }
@keyframes gradient-x { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }
.animate-gradient-x { animation: gradient-x 3s ease infinite; }

.ripple-effect { position: absolute; inset: 0; border-radius: 0.5rem; background: radial-gradient(circle, rgba(59,130,246,0.4) 0%, transparent 70%); animation: ripple-out 0.8s cubic-bezier(0.34, 1.56, 0.64, 1); pointer-events: none; }
@keyframes ripple-out { 0%{transform:scale(0);opacity:1} 100%{transform:scale(2.5);opacity:0} }

.notification-badge { position: absolute; top: 4px; right: 4px; display:flex; align-items:center; justify-content:center; }
.notification-ping { position: absolute; height: 10px; width: 10px; border-radius: 50%; background: linear-gradient(135deg, #0ea5e9, #3b82f6); animation: ping-animation 1.5s cubic-bezier(0, 0, 0.2, 1) infinite; }
.notification-dot { position: relative; height: 8px; width: 8px; border-radius: 50%; background: linear-gradient(135deg, #0ea5e9, #3b82f6); border: 2px solid white; box-shadow: 0 2px 4px rgba(0,0,0,0.2); }
@keyframes ping-animation { 75%,100%{transform:scale(2.5);opacity:0} }

.avatar-container { position: relative; }
.avatar-glow-ring { position: absolute; inset: -4px; border-radius: 50%; background: linear-gradient(135deg, rgba(14,165,233,0.5), rgba(59,130,246,0.5), rgba(6,182,212,0.5)); background-size: 200% 200%; opacity: 0; filter: blur(8px); transition: opacity 0.4s ease; animation: gradient-rotate 3s ease infinite; }
.avatar-btn:hover .avatar-glow-ring { opacity: 1; }
@keyframes gradient-rotate { 0%,100%{background-position:0% 50%} 50%{background-position:100% 50%} }

.online-status { position:absolute; bottom:-2px; right:-2px; display:flex; align-items:center; justify-content:center; z-index:20; }
.online-pulse { position:absolute; height:12px; width:12px; border-radius:50%; background: linear-gradient(135deg, #0ea5e9, #3b82f6); animation: pulse-animation 2s cubic-bezier(0.4,0,0.6,1) infinite; }
.online-dot { position:relative; height:10px; width:10px; border-radius:50%; background: linear-gradient(135deg, #0ea5e9, #3b82f6); border:2px solid white; box-shadow:0 0 0 1px rgba(59,130,246,0.2), 0 2px 4px rgba(0,0,0,0.2); }
@keyframes pulse-animation { 0%,100%{transform:scale(1);opacity:.8} 50%{transform:scale(2);opacity:0} }

.status-badge { display:inline-flex; align-items:center; gap:4px; padding:2px 8px; border-radius:9999px; background: linear-gradient(135deg, #e0f2fe, #dbeafe); font-size:10px; font-weight:600; color:#0369a1; }
.status-dot { height:6px; width:6px; border-radius:50%; background: linear-gradient(135deg, #0ea5e9, #3b82f6); animation: pulse-dot 2s ease-in-out infinite; }

.menu-item { position: relative; overflow: hidden; }
.menu-item::before { content:''; position:absolute; left:0; top:0; height:100%; width:3px; background: linear-gradient(180deg, #0ea5e9, #3b82f6); transform: scaleY(0); transform-origin: top; transition: transform .3s cubic-bezier(0.34,1.56,0.64,1); border-radius:0 3px 3px 0; }
.menu-item:hover::before { transform: scaleY(1); }

.hamburger-icon { position:absolute; left:50%; top:50%; transform:translate(-50%,-50%); display:flex; flex-direction:column; gap:5px; }
.hamburger-icon span { display:block; width:20px; height:2px; background: linear-gradient(90deg, #6b7280, #374151); border-radius:2px; transition:all .3s cubic-bezier(0.34,1.56,0.64,1); transform-origin:center; }

.mobile-menu { animation: slide-down .3s ease-out; }
@keyframes slide-down { from{opacity:0;transform:translateY(-20px)} to{opacity:1;transform:translateY(0)} }

.mobile-link { position:relative; overflow:hidden; }
.mobile-link::after { content:''; position:absolute; bottom:0; left:0; right:0; height:2px; background: linear-gradient(90deg, #0ea5e9, #3b82f6); transform:scaleX(0); transform-origin:left; transition:transform .4s cubic-bezier(0.34,1.56,0.64,1); }
.mobile-link:hover::after { transform: scaleX(1); }

* { transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1); }

@media (prefers-reduced-motion: reduce) {
  *,*::before,*::after{ animation-duration:.01ms !important; animation-iteration-count:1 !important; transition-duration:.01ms !important; }
}
</style>
