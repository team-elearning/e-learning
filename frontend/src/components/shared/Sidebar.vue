<template>
  <aside class="h-full flex flex-col">
    <div class="px-4 py-3 border-b">
      <div class="text-lg font-semibold">Admin Panel</div>
      <div class="text-xs text-gray-500">v1.0</div>
    </div>

    <nav class="flex-1 overflow-y-auto p-2">
      <RouterLink
        v-for="item in menu"
        :key="item.path"
        :to="item.path"
        v-slot="{ isActive }"
        class="mb-1 block"
      >
        <div
          class="flex items-center gap-3 rounded px-3 py-2 text-sm transition"
          :class="
            isActive
              ? 'bg-gray-100 text-gray-900 font-medium'
              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
          "
        >
          <span class="i">📊</span>
          <span>{{ item.label }}</span>
        </div>
      </RouterLink>
    </nav>

    <div class="border-t p-3 text-xs text-gray-500">© {{ new Date().getFullYear() }} Your Org</div>
  </aside>
</template>

<script setup lang="ts">
const menu = [
  { path: '/admin/dashboard', label: 'Dashboard' },
  { path: '/admin/users', label: 'Quản lý người dùng' },
  { path: '/admin/courses', label: 'Quản lý khóa học' },
  { path: '/admin/transactions', label: 'Giao dịch' },
  { path: '/admin/reports/revenue', label: 'Báo cáo' },
  { path: '/admin/system', label: 'Cấu hình hệ thống' },
]
</script>
