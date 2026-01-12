<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth.store'
import { Menu, X, Bell, LogOut } from 'lucide-vue-next'

type NavItem = { label: string; path: string; icon: string }

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isMenuOpen = ref(false)

const displayName = computed(() => auth.user?.fullName || auth.user?.username || 'Giáo viên')

const nav: NavItem[] = [
  { label: 'Trang chủ', path: '/teacher/dashboard', icon: '🏠' },
  { label: 'Khóa học', path: '/teacher/courses', icon: '📚' },
  { label: 'Học viên', path: '/teacher/students', icon: '🎓' },
  { label: 'Bài kiểm tra', path: '/teacher/exams', icon: '📝' },
  { label: 'Báo cáo', path: '/teacher/reports', icon: '📊' },
]

const active = computed(() => {
  const p = route.path
  const found = [...nav].reverse().find((n) => p.startsWith(n.path))
  return found?.path || '/teacher/dashboard'
})

function go(path: string) {
  const resolved = router.resolve(path)
  router.push(path)
  isMenuOpen.value = false
}

function notify() {
  ElMessage.info('Không có thông báo mới')
}

// ... rest of imports

async function logout() {
  try {
    await ElMessageBox.confirm('Bạn có chắc chắn muốn đăng xuất?', 'Đăng xuất', {
      confirmButtonText: 'Đăng xuất',
      cancelButtonText: 'Hủy',
      type: 'warning',
      confirmButtonClass: 'el-button--danger',
    })
    auth.logout()
    router.push('/login')
  } catch {
    // cancel
  }
}
</script>

<template>
  <header class="sticky top-0 z-40 bg-white/80 backdrop-blur-lg border-b border-slate-200">
    <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center gap-6">
      <!-- left: logo -->
      <button class="flex items-center gap-3 group" @click="go('/teacher/dashboard')">
        <div
          class="h-10 w-10 rounded-xl bg-gradient-to-br from-[rgb(var(--primary))] to-[rgb(var(--secondary))] flex items-center justify-center text-white font-bold text-xl shadow-lg group-hover:shadow-[rgb(var(--primary))]/30 transition duration-300"
        >
          E
        </div>
        <div class="hidden md:block text-left leading-tight">
          <div class="font-extrabold tracking-tight text-[rgb(var(--text))] text-lg">EduRiot</div>
          <div class="text-xs font-bold text-[rgb(var(--primary))] uppercase tracking-wider">
            Teacher
          </div>
        </div>
      </button>

      <!-- center: nav -->
      <nav
        class="hidden md:flex items-center gap-1 mx-auto bg-slate-50 p-1 rounded-xl border border-slate-100"
      >
        <button
          v-for="n in nav"
          :key="n.path"
          class="px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200 flex items-center gap-2"
          :class="
            active === n.path
              ? 'bg-white text-[rgb(var(--primary))] shadow-sm'
              : 'text-[rgb(var(--text-light))] hover:text-[rgb(var(--text))] hover:bg-slate-200/50'
          "
          @click="go(n.path)"
        >
          <span v-if="active === n.path">{{ n.icon }}</span>
          {{ n.label }}
        </button>
      </nav>

      <div class="flex-1 md:hidden"></div>

      <!-- right -->
      <div class="flex items-center gap-2 sm:gap-4">
        <!-- Mobile Toggle -->
        <button
          class="md:hidden p-2 text-slate-500 hover:bg-slate-100 rounded-lg transition-colors"
          @click="isMenuOpen = !isMenuOpen"
        >
          <component :is="isMenuOpen ? X : Menu" class="w-6 h-6" />
        </button>

        <button
          class="relative p-2 rounded-full text-[rgb(var(--text-light))] hover:bg-slate-100 transition"
          @click="notify"
        >
          <span
            class="absolute top-2 right-2 h-2 w-2 rounded-full bg-red-500 border-2 border-white"
          ></span>
          🔔
        </button>

        <div class="h-6 w-px bg-slate-200 hidden sm:block"></div>

        <el-dropdown trigger="click" popper-class="custom-dropdown">
          <button class="flex items-center gap-3 group">
            <div
              class="h-9 w-9 rounded-full bg-gradient-to-tr from-indigo-100 to-purple-100 border-2 border-white shadow-sm flex items-center justify-center text-lg group-hover:scale-105 transition duration-200"
            >
              👩‍🏫
            </div>
            <div class="hidden sm:block text-left leading-tight">
              <div class="text-sm font-bold text-[rgb(var(--text))]">{{ displayName }}</div>
              <div class="text-xs text-[rgb(var(--secondary))] font-medium">Đang hoạt động</div>
            </div>
            <div class="hidden sm:block text-slate-400 group-hover:text-slate-600 transition">
              ⌄
            </div>
          </button>

          <template #dropdown>
            <el-dropdown-menu class="min-w-[200px] p-2">
              <div class="px-4 py-3 border-b border-slate-100 mb-2">
                <div class="font-bold text-[rgb(var(--text))]">{{ displayName }}</div>
                <div class="text-xs text-[rgb(var(--text-light))]">teacher@eduriot.com</div>
              </div>
              <el-dropdown-item @click="router.push('/teacher/profile')">
                <span class="mr-2">👤</span> Hồ sơ cá nhân
              </el-dropdown-item>
              <el-dropdown-item @click="router.push('/teacher/change-password')">
                <span class="mr-2">🔐</span> Đổi mật khẩu
              </el-dropdown-item>
              <div class="h-px bg-slate-100 my-2"></div>
              <el-dropdown-item class="!text-red-500 hover:!bg-red-50" @click="logout">
                <span class="mr-2">⎋</span> Đăng xuất
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- Mobile Menu -->
    <div
      v-if="isMenuOpen"
      class="md:hidden absolute top-16 left-0 w-full bg-white border-b border-slate-200 shadow-xl"
    >
      <nav class="flex flex-col p-4 gap-2">
        <button
          v-for="n in nav"
          :key="n.path"
          class="px-4 py-3 rounded-lg text-sm font-semibold text-left flex items-center gap-3 transition-colors"
          :class="
            active === n.path
              ? 'bg-indigo-50 text-indigo-600'
              : 'text-slate-600 hover:bg-slate-50'
          "
          @click="go(n.path)"
        >
          <span>{{ n.icon }}</span>
          {{ n.label }}
        </button>
      </nav>
    </div>
  </header>
</template>

<style>
/* Custom tweaks if needed, mainly relying on Tailwind */
.custom-dropdown .el-dropdown-menu__item:hover {
  color: rgb(var(--primary));
  background-color: rgb(248, 250, 252);
}
</style>
