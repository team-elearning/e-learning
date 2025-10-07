<template>
  <aside class="h-full flex flex-col bg-white border-r border-gray-200 shadow-sm md:shadow-none">
    <div class="p-5 flex items-center gap-3 border-b border-gray-200">
      <RouterLink to="/teacher/dashboard" class="text-xl font-bold tracking-tight text-gray-800">
        <LogoEduriot :size="28" primary="#3B82F6" accent="#14B8A6" />
      </RouterLink>
    </div>

    <nav class="flex-1 p-3 space-y-1">
      <RouterLink
        v-for="item in menuItems"
        :key="item.path"
        :to="item.path"
        class="flex items-center gap-3 p-3 rounded-lg text-base transition-colors duration-200 relative group"
        :class="
          isActive(item.path)
            ? 'bg-blue-50 text-blue-700 font-semibold'
            : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
        "
      >
        <component :is="item.icon" class="h-5 w-5"></component>
        <span>{{ item.label }}</span>
        <span
          v-if="isActive(item.path)"
          class="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-2/3 bg-blue-600 rounded-r-md transition-all duration-200"
        ></span>
      </RouterLink>
    </nav>

    <div class="p-4 border-t border-gray-200 text-sm text-gray-500">
      <p>&copy; 2025 Teacher Panel. All rights reserved.</p>
    </div>
  </aside>
</template>

<script setup lang="ts">
import { useRoute } from 'vue-router'
import {
  HomeIcon,
  BookOpenIcon,
  AcademicCapIcon,
  ClipboardDocumentListIcon,
  UserGroupIcon,
} from '@heroicons/vue/24/outline'
import LogoEduriot from '@/components/ui/LogoEduriot.vue'

const route = useRoute()

const menuItems = [
  { path: '/teacher/dashboard', label: 'Dashboard', icon: HomeIcon },
  { path: '/teacher/courses', label: 'Khóa học', icon: BookOpenIcon },
  { path: '/teacher/classes', label: 'Lớp học', icon: AcademicCapIcon },
  { path: '/teacher/exams', label: 'Bài kiểm tra', icon: ClipboardDocumentListIcon },
  { path: '/teacher/students', label: 'Học sinh', icon: UserGroupIcon },
]

// Active khi URL bắt đầu bằng path của menu
const isActive = (path: string) => route.path.startsWith(path)
</script>
