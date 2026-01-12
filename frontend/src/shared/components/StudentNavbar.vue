<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth.store'
import { Menu, X } from 'lucide-vue-next'

type NavItem = { label: string; path: string; icon: string }

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const isMenuOpen = ref(false)

const displayName = computed(() => auth.user?.fullName || auth.user?.username || 'Sinh viên')

const nav: NavItem[] = [
  { label: 'Tổng quan', path: '/student/dashboard', icon: '🏠' },
  { label: 'Khóa học của tôi', path: '/student/courses', icon: '📚' },
  { label: 'Lịch học', path: '/student/schedule', icon: '📅' },
  { label: 'Kết quả học tập', path: '/student/results', icon: '📊' },
]

const active = computed(() => {
  const p = route.path
  const found = [...nav].reverse().find((n) => p.startsWith(n.path))
  return found?.path || '/student/dashboard'
})

function go(path: string) {
  const resolved = router.resolve(path)
  router.push(path)
  isMenuOpen.value = false
}

function notify() {
  ElMessage.info('Không có thông báo mới')
}

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
      <button class="flex items-center gap-3 group" @click="go('/student/dashboard')">
        <div
          class="h-10 w-10 rounded-xl bg-gradient-to-br from-blue-500 to-indigo-600 flex items-center justify-center text-white font-bold text-xl shadow-lg group-hover:shadow-blue-200 transition duration-300"
        >
          S
        </div>
        <div class="hidden md:block text-left leading-tight">
          <div class="font-extrabold tracking-tight text-gray-800 text-lg">EduRiot</div>
          <div class="text-xs font-bold text-blue-600 uppercase tracking-wider">Student</div>
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
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-slate-500 hover:text-gray-900 hover:bg-slate-200/50'
          "
          @click="go(n.path)"
        >
          <span v-if="active === n.path">{{ n.icon }}</span>
          {{ n.label }}
        </button>
      </nav>

      <!-- Mobile Menu Button -->
      <button
        class="md:hidden p-2 text-slate-500 hover:bg-slate-100 rounded-lg"
        @click="isMenuOpen = !isMenuOpen"
      >
        <Menu v-if="!isMenuOpen" class="w-6 h-6" />
        <X v-else class="w-6 h-6" />
      </button>

      <!-- right -->
      <div class="hidden md:flex items-center gap-4">
        <el-input placeholder="Tìm kiếm..." class="hidden lg:block w-48" size="default">
          <template #prefix>🔍</template>
        </el-input>

        <button
          class="relative p-2 rounded-full text-slate-500 hover:bg-slate-100 transition"
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
              class="h-9 w-9 rounded-full bg-gradient-to-tr from-blue-100 to-cyan-100 border-2 border-white shadow-sm flex items-center justify-center text-lg group-hover:scale-105 transition duration-200"
            >
              👨‍🎓
            </div>
            <div class="hidden sm:block text-left leading-tight">
              <div class="text-sm font-bold text-gray-800">{{ displayName }}</div>
              <!-- <div class="text-xs text-blue-600 font-medium">Sinh viên năm 3</div> -->
            </div>
            <div class="hidden sm:block text-slate-400 group-hover:text-slate-600 transition">
              ⌄
            </div>
          </button>

          <template #dropdown>
            <el-dropdown-menu class="min-w-[200px] p-2">
              <div class="px-4 py-3 border-b border-slate-100 mb-2">
                <div class="font-bold text-gray-800">{{ displayName }}</div>
                <div class="text-xs text-slate-500">student@eduriot.com</div>
              </div>
              <el-dropdown-item @click="router.push('/student/profile')">
                <span class="mr-2">👤</span> Hồ sơ cá nhân
              </el-dropdown-item>
              <el-dropdown-item @click="router.push('/student/change-password')">
                <span class="mr-2">🔐</span> Đổi mật khẩu
              </el-dropdown-item>
              <div class="h-px bg-slate-100 my-2"></div>
              <el-dropdown-item class="!text-red-500 hover:!bg-red-50" @click="logout">
                <!-- Mobile Navigation Menu -->
                <div
                  v-if="isMenuOpen"
                  class="md:hidden absolute top-16 left-0 right-0 bg-white border-b border-slate-200 shadow-xl p-4 flex flex-col gap-2 z-50 animate-in slide-in-from-top-2"
                >
                  <button
                    v-for="n in nav"
                    :key="n.path"
                    class="flex items-center gap-3 px-4 py-3 rounded-xl font-medium transition-colors"
                    :class="
                      active === n.path
                        ? 'bg-blue-50 text-blue-600'
                        : 'text-slate-600 hover:bg-slate-50'
                    "
                    @click="go(n.path)"
                  >
                    <span>{{ n.icon }}</span>
                    {{ n.label }}
                  </button>

                  <div class="h-px bg-slate-100 my-2"></div>

                  <div class="flex items-center gap-3 px-4 py-3">
                    <div
                      class="h-8 w-8 rounded-full bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold text-sm"
                    >
                      {{ displayName.charAt(0) }}
                    </div>
                    <div class="flex-1">
                      <div class="text-sm font-bold text-gray-900">{{ displayName }}</div>
                      <div class="text-xs text-slate-500">Học sinh</div>
                    </div>
                    <button
                      @click="logout"
                      class="text-xs font-semibold text-red-500 hover:bg-red-50 px-3 py-1.5 rounded-lg transition"
                    >
                      Đăng xuất
                    </button>
                  </div>
                </div>
                <span class="mr-2">⎋</span> Đăng xuất
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </header>
</template>
