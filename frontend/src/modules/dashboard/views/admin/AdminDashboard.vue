<script setup lang="ts">
import { ref } from 'vue'
import {
  Users,
  BookOpen,
  DollarSign,
  TrendingUp,
  Activity,
  MoreHorizontal,
  PlusCircle,
  FileText,
} from 'lucide-vue-next'

// Mock Data for Stats
const stats = [
  {
    title: 'Tổng học viên',
    value: '2,420',
    change: '+12%',
    trend: 'up',
    icon: Users,
    color: 'text-blue-600',
    bg: 'bg-blue-100',
  },
  {
    title: 'Tổng khóa học',
    value: '45',
    change: '+3',
    trend: 'up',
    icon: BookOpen,
    color: 'text-indigo-600',
    bg: 'bg-indigo-100',
  },
  {
    title: 'Doanh thu tháng',
    value: '124.5tr',
    change: '+8.2%',
    trend: 'up',
    icon: DollarSign,
    color: 'text-emerald-600',
    bg: 'bg-emerald-100',
  },
  {
    title: 'Đang hoạt động',
    value: '543',
    change: '-2%',
    trend: 'down',
    icon: Activity,
    color: 'text-purple-600',
    bg: 'bg-purple-100',
  },
]

// Mock Data for Recent User Registrations
const recentUsers = ref([
  {
    id: 1,
    name: 'Nguyễn Văn A',
    email: 'nguyenvana@example.com',
    role: 'Student',
    status: 'Active',
    date: '10/01/2026',
    avatar: 'https://ui-avatars.com/api/?name=Nguyen+Van+A&background=random',
  },
  {
    id: 2,
    name: 'Trần Thị B',
    email: 'tranthib@example.com',
    role: 'Student',
    status: 'Pending',
    date: '09/01/2026',
    avatar: 'https://ui-avatars.com/api/?name=Tran+Thi+B&background=random',
  },
  {
    id: 3,
    name: 'Lê Văn C',
    email: 'levanc@example.com',
    role: 'Instructor',
    status: 'Active',
    date: '09/01/2026',
    avatar: 'https://ui-avatars.com/api/?name=Le+Van+C&background=random',
  },
  {
    id: 4,
    name: 'Phạm Thị D',
    email: 'phamthid@example.com',
    role: 'Student',
    status: 'Active',
    date: '08/01/2026',
    avatar: 'https://ui-avatars.com/api/?name=Pham+Thi+D&background=random',
  },
])

// Mock Data for Popular Courses
const popularCourses = ref([
  {
    id: 1,
    title: 'Lập trình Web Fullstack với Vue & Node',
    sales: 120,
    revenue: '240.000.000đ',
    rating: 4.8,
  },
  {
    id: 2,
    title: 'Thiết kế UI/UX cơ bản cho người mới',
    sales: 85,
    revenue: '85.000.000đ',
    rating: 4.5,
  },
  {
    id: 3,
    title: 'Python for Data Science',
    sales: 210,
    revenue: '315.000.000đ',
    rating: 4.9,
  },
])
</script>

<template>
  <div class="p-8 bg-slate-50 min-h-screen">
    <!-- Header -->
    <div class="flex items-center justify-between mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
        <p class="text-slate-500">Tổng quan tình hình hoạt động của hệ thống.</p>
      </div>
      <div class="flex gap-3">
        <button
          class="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-600 hover:bg-slate-50 font-medium transition-colors"
        >
          <FileText class="w-4 h-4" />
          Xuất báo cáo
        </button>
        <button
          class="flex items-center gap-2 px-4 py-2 bg-[rgb(var(--primary))] text-white rounded-lg hover:bg-[rgb(var(--primary))]/90 font-medium transition-colors shadow-sm"
        >
          <PlusCircle class="w-4 h-4" />
          Thêm khóa học
        </button>
      </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-6 mb-8">
      <div
        v-for="(stat, index) in stats"
        :key="index"
        class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm hover:shadow-md transition-shadow"
      >
        <div class="flex items-center justify-between mb-4">
          <div :class="`p-3 rounded-xl ${stat.bg}`">
            <component :is="stat.icon" :class="`w-6 h-6 ${stat.color}`" />
          </div>
          <span
            :class="`text-sm font-medium ${stat.trend === 'up' ? 'text-green-600' : 'text-red-600'}`"
          >
            {{ stat.change }}
          </span>
        </div>
        <h3 class="text-slate-500 text-sm font-medium mb-1">{{ stat.title }}</h3>
        <p class="text-2xl font-bold text-gray-900">{{ stat.value }}</p>
      </div>
    </div>

    <!-- Charts & Analytics (Mock) -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
      <!-- Revenue Chart Area -->
      <div class="lg:col-span-2 bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <div class="flex items-center justify-between mb-6">
          <h3 class="font-bold text-gray-900 text-lg">Biểu đồ doanh thu</h3>
          <select
            class="text-sm border-slate-200 rounded-lg text-slate-600 focus:ring-indigo-500 focus:border-indigo-500"
          >
            <option>7 ngày qua</option>
            <option>Tháng này</option>
            <option>Năm nay</option>
          </select>
        </div>
        <!-- Mock Chart Placeholder -->
        <div class="h-64 flex items-end justify-between gap-2 px-4">
          <div
            v-for="h in [40, 65, 45, 80, 55, 90, 70, 85, 60, 75, 50, 95]"
            :key="h"
            class="w-full bg-[rgb(var(--primary))] opacity-10 hover:opacity-100 transition-opacity rounded-t-sm"
            :style="{ height: `${h}%` }"
          ></div>
        </div>
        <div class="flex justify-between mt-4 text-xs text-slate-400">
          <span>Jan</span><span>Feb</span><span>Mar</span><span>Apr</span><span>May</span
          ><span>Jun</span><span>Jul</span><span>Aug</span><span>Sep</span><span>Oct</span
          ><span>Nov</span><span>Dec</span>
        </div>
      </div>

      <!-- Popular Courses -->
      <div class="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
        <h3 class="font-bold text-gray-900 text-lg mb-6">Khóa học phổ biến</h3>
        <div class="space-y-6">
          <div v-for="course in popularCourses" :key="course.id" class="flex flex-col gap-2">
            <div class="flex justify-between items-start">
              <h4 class="font-medium text-gray-800 text-sm line-clamp-1" :title="course.title">
                {{ course.title }}
              </h4>
              <span class="text-yellow-500 text-xs font-bold flex items-center gap-1">
                ★ {{ course.rating }}
              </span>
            </div>
            <div class="flex justify-between text-xs">
              <span class="text-slate-500">{{ course.sales }} học viên</span>
              <span class="font-semibold text-emerald-600">{{ course.revenue }}</span>
            </div>
            <div class="h-1.5 w-full bg-slate-100 rounded-full overflow-hidden">
              <div class="h-full bg-indigo-500" style="width: 70%"></div>
            </div>
          </div>
        </div>
        <button
          class="w-full mt-6 py-2 text-sm text-[rgb(var(--primary))] font-medium hover:bg-indigo-50 rounded-lg transition-colors"
        >
          Xem tất cả khóa học
        </button>
      </div>
    </div>

    <!-- Recent Users Table -->
    <div class="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
      <div class="p-6 border-b border-slate-100 flex items-center justify-between">
        <h3 class="font-bold text-gray-900 text-lg">Người dùng mới đăng ký</h3>
        <button class="text-indigo-600 text-sm font-medium hover:underline">Xem tất cả</button>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr class="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider">
              <th class="px-6 py-4 font-semibold">User</th>
              <th class="px-6 py-4 font-semibold">Role</th>
              <th class="px-6 py-4 font-semibold">Status</th>
              <th class="px-6 py-4 font-semibold">Date</th>
              <th class="px-6 py-4 font-semibold text-right">Action</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr v-for="user in recentUsers" :key="user.id" class="hover:bg-slate-50/50 transition">
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <img :src="user.avatar" alt="avatar" class="w-8 h-8 rounded-full bg-slate-200" />
                  <div>
                    <div class="font-medium text-gray-900 text-sm">{{ user.name }}</div>
                    <div class="text-slate-500 text-xs">{{ user.email }}</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-semibold',
                    user.role === 'Instructor'
                      ? 'bg-purple-100 text-purple-700'
                      : 'bg-blue-100 text-blue-700',
                  ]"
                >
                  {{ user.role }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-semibold',
                    user.status === 'Active'
                      ? 'bg-green-100 text-green-700'
                      : 'bg-yellow-100 text-yellow-700',
                  ]"
                >
                  {{ user.status }}
                </span>
              </td>
              <td class="px-6 py-4 text-sm text-slate-600">{{ user.date }}</td>
              <td class="px-6 py-4 text-right">
                <button class="text-slate-400 hover:text-slate-600">
                  <MoreHorizontal class="w-5 h-5" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>
