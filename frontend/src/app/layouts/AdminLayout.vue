<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import {
  LayoutDashboard,
  Users,
  BookOpen,
  Settings,
  LogOut,
  Menu,
  X,
  Bell,
  Search,
  ChevronDown,
} from 'lucide-vue-next'
import { ElMessageBox } from 'element-plus'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isSidebarOpen = ref(false)
const isProfileOpen = ref(false)

const menuItems = [
  {
    title: 'Dashboard',
    path: '/admin/dashboard',
    icon: LayoutDashboard,
  },
  {
    title: 'Quản lý người dùng',
    path: '/admin/users',
    icon: Users,
  },
  {
    title: 'Quản lý Khóa học',
    path: '/admin/courses',
    icon: BookOpen,
  },
  {
    title: 'Cài đặt hệ thống',
    path: '/admin/settings',
    icon: Settings,
  },
]

const toggleSidebar = () => {
  isSidebarOpen.value = !isSidebarOpen.value
}

const handleLogout = async () => {
  try {
    await ElMessageBox.confirm('Bạn có chắc chắn muốn đăng xuất?', 'Đăng xuất', {
      confirmButtonText: 'Đăng xuất',
      cancelButtonText: 'Hủy',
      type: 'warning',
    })
    authStore.logout()
    router.push('/login')
  } catch {
    // Cancelled
  }
}

const currentRouteName = computed(() => {
  const activeItem = menuItems.find((item) => route.path.startsWith(item.path))
  return activeItem ? activeItem.title : 'Admin Portal'
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex">
    <!-- Mobile Sidebar Backdrop -->
    <div
      v-if="isSidebarOpen"
      @click="isSidebarOpen = false"
      class="fixed inset-0 bg-black/50 z-20 lg:hidden glass-backdrop"
    ></div>

    <!-- Sidebar -->
    <aside
      :class="[
        'fixed lg:static inset-y-0 left-0 z-30 w-64 bg-slate-900 text-white transition-transform duration-300 ease-in-out flex flex-col',
        isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0',
      ]"
    >
      <!-- Logo -->
      <div class="h-16 flex items-center px-6 border-b border-slate-800">
        <span
          class="text-xl font-bold bg-gradient-to-r from-blue-400 to-indigo-400 bg-clip-text text-transparent"
        >
          EduRiot Admin
        </span>
        <button
          @click="isSidebarOpen = false"
          class="ml-auto lg:hidden text-slate-400 hover:text-white"
        >
          <X class="w-6 h-6" />
        </button>
      </div>

      <!-- Nav Items -->
      <nav class="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-3 rounded-lg text-slate-300 hover:bg-slate-800 hover:text-white transition-colors group"
          active-class="bg-indigo-600 text-white shadow-lg shadow-indigo-900/20"
        >
          <component :is="item.icon" class="w-5 h-5 group-hover:scale-110 transition-transform" />
          <span class="font-medium">{{ item.title }}</span>
        </router-link>
      </nav>

      <!-- User Profile (Bottom Sidebar) -->
      <div class="border-t border-slate-800 p-4">
        <div class="flex items-center gap-3">
          <img
            :src="`https://ui-avatars.com/api/?name=${authStore.user?.username}&background=random`"
            class="w-8 h-8 rounded-full bg-slate-700"
          />
          <div class="flex-1 min-w-0">
            <p class="text-sm font-medium text-white truncate">
              {{ authStore.user?.username || 'Admin' }}
            </p>
            <p class="text-xs text-slate-400 truncate">
              {{ authStore.user?.email || 'admin@system.com' }}
            </p>
          </div>
          <button
            @click="handleLogout"
            class="text-slate-400 hover:text-red-400 transition-colors"
            title="Đăng xuất"
          >
            <LogOut class="w-5 h-5" />
          </button>
        </div>
      </div>
    </aside>

    <!-- Main Content Wrapper -->
    <div class="flex-1 flex flex-col min-w-0 h-screen overflow-hidden">
      <!-- Navbar -->
      <header
        class="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-8 z-10 sticky top-0"
      >
        <div class="flex items-center gap-4">
          <button @click="toggleSidebar" class="lg:hidden text-slate-500 hover:text-slate-700">
            <Menu class="w-6 h-6" />
          </button>
          <h2 class="text-lg font-bold text-gray-800 hidden sm:block">{{ currentRouteName }}</h2>
        </div>

        <div class="flex items-center gap-4">
          <!-- Search Bar -->
          <div class="hidden md:flex items-center relative">
            <Search class="w-4 h-4 absolute left-3 text-slate-400" />
            <input
              type="text"
              placeholder="Search..."
              class="pl-9 pr-4 py-2 rounded-full bg-slate-100 border-none text-sm focus:ring-2 focus:ring-indigo-500 w-64 transition-all focus:w-80"
            />
          </div>

          <!-- Notification -->
          <button
            class="relative p-2 text-slate-500 hover:bg-slate-100 rounded-full transition-colors"
          >
            <Bell class="w-5 h-5" />
            <span
              class="absolute top-1.5 right-1.5 w-2 h-2 bg-red-500 rounded-full border-2 border-white"
            ></span>
          </button>
        </div>
      </header>

      <!-- Page Content -->
      <main class="flex-1 overflow-y-auto bg-slate-50 relative">
        <router-view v-slot="{ Component }">
          <transition
            enter-active-class="transition duration-200 ease-out"
            enter-from-class="opacity-0 translate-y-2"
            enter-to-class="opacity-100 translate-y-0"
            leave-active-class="transition duration-150 ease-in"
            leave-from-class="opacity-100 translate-y-0"
            leave-to-class="opacity-0 translate-y-2"
            mode="out-in"
          >
            <component :is="Component" />
          </transition>
        </router-view>
      </main>
    </div>
  </div>
</template>

<style scoped>
.router-link-active {
  background-color: rgb(79 70 229); /* indigo-600 */
  color: white;
}
.glass-backdrop {
  backdrop-filter: blur(4px);
}
</style>
