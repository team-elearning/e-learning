<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAuthStore } from '@/stores/auth.store'

type MenuItem = { label: string; path: string; icon: string }

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const logoSrc = '/favicon.png' // <-- đổi đúng tên logo trong /public

const drawerOpen = ref(false)

const displayName = computed(() => auth.user?.fullName || auth.user?.username || 'Giáo viên')
const pageTitle = computed(() => (route.meta.title as string) || 'Teacher')

const menu: MenuItem[] = [
  { label: 'Dashboard', path: '/teacher/dashboard', icon: '🏠' },
  { label: 'Khóa học', path: '/teacher/courses', icon: '📚' },
  { label: 'Lớp học', path: '/teacher/classes', icon: '🏫' },
  { label: 'Bài thi', path: '/teacher/exams', icon: '🧪' },
  { label: 'Học sinh', path: '/teacher/students', icon: '👩‍🎓' },
  { label: 'Thông báo', path: '/teacher/notifications', icon: '🔔' },
  { label: 'Cài đặt', path: '/teacher/settings', icon: '⚙️' },
]

const activePath = computed(() => route.path)

function navigate(path: string) {
  const resolved = router.resolve(path)
  if (!resolved.matched.length) {
    ElMessage.info('Màn này chưa làm route 😄')
    return
  }
  router.push(path)
  drawerOpen.value = false
}

async function logout() {
  try {
    await ElMessageBox.confirm('Bạn chắc chắn muốn đăng xuất?', 'Xác nhận', {
      confirmButtonText: 'Đăng xuất',
      cancelButtonText: 'Hủy',
      type: 'warning',
    })
    auth.logout()
    router.push('/login')
  } catch {
    // cancel
  }
}
</script>

<template>
  <div class="min-h-screen" :style="{ background: 'rgb(var(--bg))' }">
    <!-- TOPBAR -->
    <header class="sticky top-0 z-40 border-b bg-white/80 backdrop-blur">
      <div class="px-4 h-16 flex items-center gap-3">
        <!-- Mobile: open drawer -->
        <el-button class="md:hidden" circle plain @click="drawerOpen = true">☰</el-button>

        <!-- Brand -->
        <button class="flex items-center gap-3" @click="navigate('/teacher/dashboard')">
          <img
            :src="logoSrc"
            alt="Logo"
            class="h-9 w-9 rounded-xl border bg-white object-contain"
          />
          <div class="leading-tight text-left">
            <div class="font-semibold">Teacher</div>
            <div class="text-xs text-slate-500">EduRiot LMS</div>
          </div>
        </button>

        <!-- Page title -->
        <div class="hidden md:block ml-3">
          <div class="text-xs text-slate-500">Trang hiện tại</div>
          <div class="font-semibold leading-tight">{{ pageTitle }}</div>
        </div>

        <div class="flex-1"></div>

        <!-- Actions -->
        <el-tooltip content="Thông báo (placeholder)" placement="bottom">
          <el-button circle plain @click="ElMessage.info('Thông báo: làm sau 😄')">🔔</el-button>
        </el-tooltip>

        <el-dropdown trigger="click">
          <el-button plain>
            <span class="mr-2">👤</span>
            <span class="hidden sm:inline">{{ displayName }}</span>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="navigate('/teacher/settings')">Cài đặt</el-dropdown-item>
              <el-dropdown-item divided @click="logout">Đăng xuất</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <!-- DESKTOP LAYOUT -->
    <div class="flex">
      <!-- SIDEBAR (desktop) -->
      <aside class="hidden md:flex w-[280px] shrink-0 border-r bg-white min-h-[calc(100vh-64px)]">
        <div class="w-full p-3 flex flex-col gap-3">
          <!-- menu -->
          <el-menu class="border-0" :default-active="activePath" router="false">
            <el-menu-item v-for="m in menu" :key="m.path" :index="m.path" @click="navigate(m.path)">
              <span class="mr-2">{{ m.icon }}</span>
              <span>{{ m.label }}</span>
            </el-menu-item>
          </el-menu>

          <div class="mt-auto rounded-2xl border p-4 bg-slate-50">
            <div class="text-sm font-medium">Quick</div>
            <div class="text-xs text-slate-600 mt-1">Tạo khóa học / bài thi nhanh.</div>
            <div class="mt-3 flex flex-col gap-2">
              <el-button type="primary" plain @click="ElMessage.info('Tạo khóa học: làm sau 😄')"
                >+ Tạo khóa học</el-button
              >
              <el-button plain @click="ElMessage.info('Tạo bài thi: làm sau 😄')"
                >+ Tạo bài thi</el-button
              >
            </div>
          </div>
        </div>
      </aside>

      <!-- CONTENT -->
      <main class="flex-1 p-4 md:p-6">
        <!-- giữ content không quá rộng cho đẹp -->
        <div class="mx-auto max-w-6xl">
          <slot />
        </div>
      </main>
    </div>

    <!-- MOBILE DRAWER SIDEBAR -->
    <el-drawer v-model="drawerOpen" direction="ltr" size="80%">
      <template #header>
        <div class="flex items-center gap-3">
          <img
            :src="logoSrc"
            alt="Logo"
            class="h-9 w-9 rounded-xl border bg-white object-contain"
          />
          <div>
            <div class="font-semibold">Teacher Menu</div>
            <div class="text-xs text-slate-500">{{ displayName }}</div>
          </div>
        </div>
      </template>

      <el-menu class="border-0" :default-active="activePath">
        <el-menu-item v-for="m in menu" :key="m.path" :index="m.path" @click="navigate(m.path)">
          <span class="mr-2">{{ m.icon }}</span>
          <span>{{ m.label }}</span>
        </el-menu-item>
      </el-menu>

      <div class="mt-5">
        <el-button class="w-full" type="danger" plain @click="logout">Đăng xuất</el-button>
      </div>
    </el-drawer>
  </div>
</template>
