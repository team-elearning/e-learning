<script setup lang="ts">
import { ref } from 'vue'

// Mock Data (Replace with Store/API later)
const studentName = ref('Sinh viên')
const currentDate = new Date().toLocaleDateString('vi-VN', {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
})

const stats = [
  { label: 'Khóa học đang học', value: 5, icon: '📚', color: 'bg-blue-100 text-blue-600' },
  { label: 'Bài tập chưa nộp', value: 3, icon: '📝', color: 'bg-orange-100 text-orange-600' },
  { label: 'Điểm trung bình', value: '8.5', icon: '🏆', color: 'bg-green-100 text-green-600' },
  { label: 'Giờ học tuần này', value: '12h', icon: '⏱️', color: 'bg-purple-100 text-purple-600' },
]

const courses = ref([
  {
    id: 1,
    title: 'Lập trình Web Frontend',
    instructor: 'Nguyễn Văn A',
    progress: 75,
    totalLessons: 20,
    completedLessons: 15,
    image:
      'https://images.unsplash.com/photo-1547658719-da2b51169166?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 2,
    title: 'Cơ sở dữ liệu nâng cao',
    instructor: 'Trần Thị B',
    progress: 30,
    totalLessons: 12,
    completedLessons: 4,
    image:
      'https://images.unsplash.com/photo-1544383204-dbd5d2302325?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 3,
    title: 'Tiếng Anh chuyên ngành CNTT',
    instructor: 'David Wilson',
    progress: 90,
    totalLessons: 30,
    completedLessons: 27,
    image:
      'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
  },
  {
    id: 4,
    title: 'Nhập môn Trí tuệ nhân tạo',
    instructor: 'Lê Văn C',
    progress: 10,
    totalLessons: 15,
    completedLessons: 1.5,
    image:
      'https://images.unsplash.com/photo-1620712943543-bcc4688e7485?ixlib=rb-4.0.3&auto=format&fit=crop&w=800&q=80',
  },
])

const deadlines = ref([
  {
    id: 1,
    title: 'Nộp bài tập lớn cuối kỳ',
    course: 'Lập trình Web',
    due: 'Hôm nay, 23:59',
    urgent: true,
  },
  { id: 2, title: 'Quiz chương 3', course: 'Cơ sở dữ liệu', due: 'Ngày mai, 10:00', urgent: false },
  {
    id: 3,
    title: 'Bài luận tiếng Anh',
    course: 'Tiếng Anh CNTT',
    due: '12/11/2023',
    urgent: false,
  },
])

const recentActivities = ref([
  { id: 1, text: 'Đã hoàn thành bài học "CSS Grid System"', time: '2 giờ trước' },
  { id: 2, text: 'Giáo viên đã chấm bài tập #2', time: '5 giờ trước' },
  { id: 3, text: 'Đã tham gia khóa học mới "AI Advance"', time: '1 ngày trước' },
])
</script>

<template>
  <div class="min-h-screen bg-slate-50/50 p-6 lg:p-8">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 tracking-tight">
          Xin chào, {{ studentName }}! 👋
        </h1>
        <p class="text-slate-500 mt-1 font-medium">{{ currentDate }}</p>
      </div>
      <div>
        <button
          class="bg-[rgb(var(--primary))] hover:bg-[rgb(var(--primary))]/90 text-white px-5 py-2.5 rounded-xl font-semibold shadow-lg shadow-indigo-200 transition-all flex items-center gap-2"
        >
          <span>✨</span> Vào học ngay
        </button>
      </div>
    </div>

    <!-- Stats -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-8">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="bg-white p-5 rounded-2xl shadow-sm border border-slate-100 flex items-center gap-4 hover:shadow-md transition-all duration-300"
      >
        <div
          :class="`w-14 h-14 rounded-xl flex items-center justify-center text-2xl ${stat.color}`"
        >
          {{ stat.icon }}
        </div>
        <div>
          <div class="text-2xl font-bold text-gray-800">{{ stat.value }}</div>
          <div class="text-sm font-medium text-slate-500">{{ stat.label }}</div>
        </div>
      </div>
    </div>

    <div class="grid grid-cols-1 xl:grid-cols-3 gap-8">
      <!-- Left Column: Courses -->
      <div class="xl:col-span-2 space-y-8">
        <!-- Progress Section -->
        <div>
          <div class="flex items-center justify-between mb-5">
            <h2 class="text-lg font-bold text-gray-800">Khóa học của tôi</h2>
            <a href="#" class="text-[rgb(var(--primary))] text-sm font-semibold hover:underline"
              >Xem tất cả</a
            >
          </div>

          <div class="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div
              v-for="course in courses"
              :key="course.id"
              class="group bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-lg transition-all duration-300 overflow-hidden flex flex-col"
            >
              <div class="h-40 relative overflow-hidden">
                <div class="absolute inset-0 bg-gray-200 animate-pulse" v-if="!course.image"></div>
                <img
                  :src="course.image"
                  alt="Course thumbnail"
                  class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                />
                <div
                  class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent"
                ></div>
                <div class="absolute bottom-3 left-4 right-4 text-white">
                  <h3 class="font-bold text-lg leading-tight line-clamp-1">{{ course.title }}</h3>
                  <p class="text-xs text-white/80 mt-1">GV: {{ course.instructor }}</p>
                </div>
              </div>

              <div class="p-5 flex-1 flex flex-col justify-between">
                <div>
                  <div class="flex justify-between text-xs font-semibold text-slate-500 mb-2">
                    <span>Tiến độ</span>
                    <span>{{ course.progress }}%</span>
                  </div>
                  <div class="w-full bg-slate-100 rounded-full h-2 mb-4 overflow-hidden">
                    <div
                      class="bg-[rgb(var(--primary))] h-2 rounded-full transition-all duration-1000 ease-out"
                      :style="{ width: `${course.progress}%` }"
                    ></div>
                  </div>
                  <div class="text-xs text-slate-400 font-medium">
                    {{ course.completedLessons }}/{{ course.totalLessons }} bài học
                  </div>
                </div>

                <div class="mt-4 pt-4 border-t border-slate-50 flex justify-end">
                  <button
                    class="text-xs font-bold text-[rgb(var(--primary))] bg-indigo-50 hover:bg-indigo-100 px-4 py-2 rounded-lg transition-colors"
                  >
                    Tiếp tục học →
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Sidebar -->
      <div class="space-y-8">
        <!-- Deadlines -->
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span>📅</span> Sắp đến hạn
          </h3>
          <div class="space-y-4">
            <div v-for="task in deadlines" :key="task.id" class="flex gap-3">
              <div class="flex-none pt-1">
                <div
                  :class="`w-2 h-2 rounded-full ${task.urgent ? 'bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.6)]' : 'bg-amber-400'}`"
                ></div>
              </div>
              <div class="flex-1">
                <div class="text-sm font-semibold text-gray-800 leading-tight">
                  {{ task.title }}
                </div>
                <div class="text-xs text-slate-500 mt-1 font-medium">
                  {{ task.course }} •
                  <span :class="task.urgent ? 'text-red-500' : ''">{{ task.due }}</span>
                </div>
              </div>
            </div>
          </div>
          <button
            class="w-full mt-5 py-2 text-sm font-semibold text-slate-500 hover:text-[rgb(var(--primary))] hover:bg-indigo-50 rounded-lg transition-colors border border-transparent hover:border-indigo-100 border-dashed"
          >
            Xem lịch chi tiết
          </button>
        </div>

        <!-- Recent Activity -->
        <div class="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
          <h3 class="font-bold text-gray-800 mb-4 flex items-center gap-2">
            <span>🔔</span> Hoạt động gần đây
          </h3>
          <div class="relative border-l-2 border-slate-100 ml-2 space-y-6">
            <div v-for="(act, index) in recentActivities" :key="act.id" class="ml-4 relative">
              <div
                class="absolute -left-[21px] top-1 w-3 h-3 bg-white border-2 border-[rgb(var(--secondary))] rounded-full"
              ></div>
              <p class="text-sm text-gray-700 font-medium">{{ act.text }}</p>
              <p class="text-xs text-slate-400 mt-0.5">{{ act.time }}</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Optional: Add custom scrollbar or specific scoped styles here */
</style>
