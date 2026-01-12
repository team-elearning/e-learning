<script setup lang="ts">
import { computed, ref } from 'vue'
import { ElMessage } from 'element-plus'

type QuickAction = { label: string; icon: string; onClick: () => void; color: string }
type EventItem = { title: string; time: string; type: string }
type CourseItem = { title: string; students: number; status: string; trend: number[] }

const quickActions: QuickAction[] = [
  {
    label: 'Tạo khóa học',
    icon: '✨',
    onClick: () => ElMessage.info('Tạo khóa học: làm sau 😄'),
    color: 'text-blue-600 bg-blue-50',
  },
  {
    label: 'Chấm bài',
    icon: '✍️',
    onClick: () => ElMessage.info('Chấm điểm: làm sau 😄'),
    color: 'text-green-600 bg-green-50',
  },
  {
    label: 'Tạo đề thi',
    icon: '📝',
    onClick: () => ElMessage.info('Tạo bài kiểm tra: làm sau 😄'),
    color: 'text-purple-600 bg-purple-50',
  },
  {
    label: 'Báo cáo',
    icon: '📊',
    onClick: () => ElMessage.info('Báo cáo: làm sau 😄'),
    color: 'text-orange-600 bg-orange-50',
  },
]

const upcoming = ref<EventItem[]>([
  { title: 'Kiểm tra giữa kỳ Toán 5', time: '11:24 AM', type: 'exam' },
  { title: 'Họp phụ huynh', time: '02:30 PM', type: 'meeting' },
  { title: 'Hạn nộp bài tập về nhà', time: '05:00 PM', type: 'deadline' },
])

const courses = ref<CourseItem[]>([
  {
    title: 'Tiếng Anh Giao Tiếp 1',
    students: 34,
    status: 'Đang dạy',
    trend: [3, 6, 4, 8, 5, 9, 10],
  },
  {
    title: 'Lập Trình Python Căn Bản',
    students: 28,
    status: 'Đang dạy',
    trend: [6, 7, 5, 4, 6, 5, 7],
  },
  {
    title: 'Thiết Kế Web Frontend',
    students: 45,
    status: 'Sắp kết thúc',
    trend: [2, 3, 4, 3, 2, 4, 2],
  },
  {
    title: 'Database Management',
    students: 12,
    status: 'Mới mở',
    trend: [5, 4, 6, 5, 7, 6, 8],
  },
])

const stats = computed(() => ({
  courses: 11,
  students: 156,
  lessons: 28,
}))

function sparkPoints(values: number[], w = 100, h = 30) {
  if (values.length < 2) return ''
  const min = Math.min(...values)
  const max = Math.max(...values)
  const dx = w / (values.length - 1)
  return values
    .map((v, i) => {
      const t = max === min ? 0.5 : (v - min) / (max - min)
      const x = i * dx
      const y = h - t * h // Invert Y because SVG coordinates
      return `${x.toFixed(1)},${y.toFixed(1)}`
    })
    .join(' ')
}
</script>

<template>
  <div class="space-y-8">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4">
      <div>
        <h1 class="text-3xl font-extrabold text-[rgb(var(--text))] tracking-tight">Tổng quan</h1>
        <p class="text-[rgb(var(--text-light))] mt-1">
          Chào buổi sáng, chúc bạn một ngày giảng dạy hiệu quả!
        </p>
      </div>
      <button
        class="px-5 py-2.5 bg-[rgb(var(--primary))] text-white rounded-xl font-semibold shadow-lg shadow-indigo-500/20 hover:shadow-indigo-500/30 hover:-translate-y-0.5 transition-all"
      >
        + Sự kiện mới
      </button>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div class="glass-panel p-6 relative overflow-hidden group">
        <div class="relative z-10">
          <div class="text-[rgb(var(--text-light))] font-medium mb-2">Tổng khóa học</div>
          <div class="text-4xl font-bold text-[rgb(var(--text))]">{{ stats.courses }}</div>
        </div>
        <div
          class="absolute right-[-20px] bottom-[-20px] text-[10rem] opacity-5 select-none transition group-hover:scale-110 duration-500"
        >
          📚
        </div>
      </div>
      <div class="glass-panel p-6 relative overflow-hidden group">
        <div class="relative z-10">
          <div class="text-[rgb(var(--text-light))] font-medium mb-2">Học viên tích cực</div>
          <div class="text-4xl font-bold text-[rgb(var(--text))]">{{ stats.students }}</div>
        </div>
        <div
          class="absolute right-[-20px] bottom-[-20px] text-[10rem] opacity-5 select-none transition group-hover:scale-110 duration-500"
        >
          👨‍🎓
        </div>
      </div>
      <div class="glass-panel p-6 relative overflow-hidden group">
        <div class="relative z-10">
          <div class="text-[rgb(var(--text-light))] font-medium mb-2">Bài giảng tuần này</div>
          <div class="text-4xl font-bold text-[rgb(var(--text))]">{{ stats.lessons }}</div>
        </div>
        <div
          class="absolute right-[-20px] bottom-[-20px] text-[10rem] opacity-5 select-none transition group-hover:scale-110 duration-500"
        >
          🎬
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
      <!-- Main Content -->
      <div class="xl:col-span-2 space-y-8">
        <!-- Quick Actions -->
        <section>
          <h2 class="text-lg font-bold text-[rgb(var(--text))] mb-4">Thao tác nhanh</h2>
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <button
              v-for="a in quickActions"
              :key="a.label"
              class="glass-panel p-4 flex flex-col items-center justify-center gap-3 hover:shadow-lg transition duration-200 group"
              @click="a.onClick"
            >
              <div
                :class="`h-12 w-12 rounded-2xl flex items-center justify-center text-2xl transition group-hover:scale-110 duration-200 ${a.color}`"
              >
                {{ a.icon }}
              </div>
              <span class="font-semibold text-sm text-[rgb(var(--text))]">{{ a.label }}</span>
            </button>
          </div>
        </section>

        <!-- Courses List -->
        <section class="glass-panel p-6">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-lg font-bold text-[rgb(var(--text))]">Khóa học của tôi</h2>
            <button class="text-sm font-semibold text-[rgb(var(--primary))] hover:underline">
              Xem tất cả
            </button>
          </div>

          <div class="overflow-x-auto">
            <table class="w-full text-left border-collapse">
              <thead>
                <tr
                  class="text-xs text-[rgb(var(--text-light))] uppercase border-b border-gray-100"
                >
                  <th class="font-semibold py-3 pl-2">Tên khóa học</th>
                  <th class="font-semibold py-3 text-center">Học viên</th>
                  <th class="font-semibold py-3 text-center">Trạng thái</th>
                  <th class="font-semibold py-3 text-right pr-2">Hoạt động</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="c in courses"
                  :key="c.title"
                  class="group hover:bg-slate-50 transition border-b border-gray-50 last:border-0"
                >
                  <td class="py-4 pl-2 font-medium text-[rgb(var(--text))]">{{ c.title }}</td>
                  <td class="py-4 text-center text-sm font-semibold text-[rgb(var(--text-light))]">
                    {{ c.students }}
                  </td>
                  <td class="py-4 text-center">
                    <span
                      class="px-2.5 py-1 rounded-full text-xs font-bold"
                      :class="
                        c.status === 'Đang dạy'
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-slate-100 text-slate-600'
                      "
                    >
                      {{ c.status }}
                    </span>
                  </td>
                  <td class="py-4 pr-2">
                    <div class="flex justify-end">
                      <svg
                        width="100"
                        height="30"
                        class="opacity-70 group-hover:opacity-100 transition"
                      >
                        <polyline
                          fill="none"
                          stroke="rgb(var(--primary))"
                          stroke-width="2"
                          stroke-linecap="round"
                          stroke-linejoin="round"
                          :points="sparkPoints(c.trend)"
                        />
                      </svg>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>

      <!-- Sidebar -->
      <div class="space-y-8">
        <!-- Upcoming Events -->
        <section class="glass-panel p-6">
          <h2 class="text-lg font-bold text-[rgb(var(--text))] mb-4">Sắp diễn ra</h2>
          <div class="space-y-4">
            <div
              v-for="(ev, i) in upcoming"
              :key="i"
              class="flex items-start gap-4 p-3 rounded-xl hover:bg-slate-50 transition"
            >
              <div
                class="h-12 w-12 rounded-xl bg-slate-100 flex flex-col items-center justify-center text-[rgb(var(--text))] font-bold shrink-0 border border-slate-200"
              >
                <span class="text-xs text-[rgb(var(--text-light))] uppercase">{{
                  ev.time.split(' ')[1]
                }}</span>
                <span class="text-sm">{{ ev.time.split(':')[0] }}</span>
              </div>
              <div>
                <div
                  class="font-semibold text-[rgb(var(--text))] line-clamp-2 md:line-clamp-1 leading-tight mb-1"
                >
                  {{ ev.title }}
                </div>
                <div
                  class="text-xs px-2 py-0.5 rounded-md inline-block font-medium capitalize bg-slate-100 text-slate-500"
                >
                  {{ ev.type }}
                </div>
              </div>
            </div>
          </div>
          <button
            class="w-full mt-4 py-2.5 text-sm font-bold text-[rgb(var(--text-light))] bg-slate-50 rounded-xl hover:bg-slate-100 transition"
          >
            Xem lịch chi tiết
          </button>
        </section>

        <!-- Promo / Teacher Helper -->
        <section
          class="relative overflow-hidden rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 p-6 text-white shadow-lg"
        >
          <div class="relative z-10">
            <h3 class="font-bold text-lg mb-2">Cần hỗ trợ?</h3>
            <p class="text-indigo-100 text-sm mb-4">
              Liên hệ với đội ngũ admin để được giải đáp thắc mắc về giáo án.
            </p>
            <button
              class="px-4 py-2 bg-white text-indigo-600 text-sm font-bold rounded-lg hover:bg-opacity-90 transition"
            >
              Gửi yêu cầu
            </button>
          </div>
          <div
            class="absolute bottom-[-30px] right-[-30px] w-32 h-32 bg-white opacity-10 rounded-full blur-2xl"
          ></div>
        </section>
      </div>
    </div>
  </div>
</template>
