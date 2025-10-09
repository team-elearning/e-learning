<!-- src/components/shared/AdminSidebar.vue -->
<template>
  <aside class="h-full flex flex-col">
    <!-- Brand -->
    <div class="h-14 flex items-center gap-2 border-b px-4">
      <button
        class="mr-2 flex md:hidden items-center justify-center rounded p-2 hover:bg-gray-100"
        aria-label="Đóng menu"
        @click="$emit('close')"
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
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
      <RouterLink
        to="/admin/dashboard"
        class="font-semibold text-gray-800 hover:text-gray-900"
        style="
          display: flex;
          margin-right: 8px;
          align-items: center;
          gap: 8px;
          justify-content: center;
        "
      >
        <!-- <div class="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-600/10">
          <span class="text-lg">🎓</span>
        </div>
        <span class="hidden text-base font-semibold text-emerald-700 sm:inline"> My Learning </span> -->
        <LogoEduriot
          :size="90"
          primary="#3B82F6"
          accent="#14B8A6"
          style="justify-content: center; margin-left: 55px"
        />
      </RouterLink>
    </div>

    <!-- Nav -->
    <nav class="flex-1 overflow-y-auto p-3">
      <template v-for="(group, gi) in groups" :key="gi">
        <div class="px-2 pt-3 pb-2 text-[11px] uppercase tracking-wide text-gray-400">
          {{ group.label }}
        </div>
        <ul class="mb-2">
          <li v-for="item in group.items" :key="item.to" class="px-1">
            <RouterLink :to="item.to" v-slot="{ isActive }" class="block">
              <div
                class="flex items-center gap-3 rounded px-3 py-2 text-sm transition"
                :class="
                  isActive
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                "
              >
                <component :is="item.icon" class="h-4 w-4" />
                <span class="truncate">{{ item.label }}</span>
              </div>
            </RouterLink>
          </li>
        </ul>
      </template>
    </nav>

    <!-- Footer -->
    <div class="border-t p-3 text-xs text-gray-500">© {{ year }} Your Org</div>
  </aside>
</template>

<script setup lang="ts">
import {
  LayoutDashboard,
  Users,
  BookOpen,
  CreditCard,
  BarChart3,
  ShieldCheck,
  FileText,
  History,
} from 'lucide-vue-next'
import LogoEduriot from '@/components/ui/LogoEduriot.vue'

const year = new Date().getFullYear()

type NavItem = { to: string; label: string; icon: any }
type NavGroup = { label: string; items: NavItem[] }

const groups: NavGroup[] = [
  {
    label: 'Tổng quan',
    items: [{ to: '/admin/dashboard', label: 'Dashboard', icon: LayoutDashboard }],
  },
  {
    label: 'Quản trị',
    items: [
      { to: '/admin/users', label: 'Người dùng', icon: Users },
      { to: '/admin/courses', label: 'Khóa học', icon: BookOpen },
      { to: '/admin/transactions', label: 'Giao dịch', icon: CreditCard },
    ],
  },
  {
    label: 'Báo cáo',
    items: [
      { to: '/admin/reports/revenue', label: 'Doanh thu', icon: BarChart3 },
      { to: '/admin/reports/users', label: 'Người dùng', icon: FileText },
      { to: '/admin/reports/learning', label: 'Học tập', icon: FileText },
      { to: '/admin/reports/content', label: 'Nội dung', icon: FileText },
    ],
  },
  {
    label: 'Hệ thống',
    items: [
      { to: '/admin/system', label: 'Cấu hình', icon: ShieldCheck },
      { to: '/admin/system/security', label: 'Bảo mật', icon: ShieldCheck },
      { to: '/admin/system/activity', label: 'Log hoạt động', icon: History },
    ],
  },
]
</script>
