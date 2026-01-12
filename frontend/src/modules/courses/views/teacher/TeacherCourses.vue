<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { coursesApi } from '../../api/courses.api'
import type { Course } from '../../types/course.types'
import { ElMessage } from 'element-plus'

const router = useRouter()
const courses = ref<Course[]>([])
const isLoading = ref(false)

async function fetchCourses() {
  isLoading.value = true
  try {
    const res = await coursesApi.getInstructorCourses()
    courses.value = res.data
  } catch (error) {
    ElMessage.error('Không thể tải danh sách khóa học')
  } finally {
    isLoading.value = false
  }
}

function handleCreate() {
  router.push('/teacher/courses/create')
}

function handleEdit(id: string) {
  router.push(`/teacher/courses/${id}/edit`)
}

onMounted(() => {
  fetchCourses()
})
</script>

<template>
  <div class="p-6 lg:p-8 min-h-screen bg-slate-50">
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Quản lý khóa học</h1>
        <p class="text-slate-500 mt-1">Danh sách các khóa học bạn đang giảng dạy</p>
      </div>
      <button
        @click="handleCreate"
        class="bg-[rgb(var(--primary))] hover:bg-[rgb(var(--primary))]/90 text-white px-4 py-2.5 rounded-xl font-semibold shadow-lg shadow-indigo-200 transition-all flex items-center gap-2"
      >
        <span class="text-xl">+</span> Tạo khóa học mới
      </button>
    </div>

    <!-- Loading State -->
    <div v-if="isLoading" class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="i in 3"
        :key="i"
        class="bg-white rounded-2xl p-4 border border-slate-100 shadow-sm animate-pulse"
      >
        <div class="h-48 bg-slate-200 rounded-xl mb-4"></div>
        <div class="h-6 bg-slate-200 rounded w-3/4 mb-2"></div>
        <div class="h-4 bg-slate-200 rounded w-1/2"></div>
      </div>
    </div>

    <!-- Empty State -->
    <div
      v-else-if="courses.length === 0"
      class="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-300"
    >
      <div class="text-6xl mb-4">📚</div>
      <h3 class="text-xl font-bold text-gray-800 mb-2">Chưa có khóa học nào</h3>
      <button
        @click="handleCreate"
        class="text-[rgb(var(--primary))] font-semibold hover:underline"
      >
        Tạo khóa học ngay
      </button>
    </div>

    <!-- Course List -->
    <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
      <div
        v-for="course in courses"
        :key="course.id"
        class="group bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden flex flex-col"
      >
        <!-- Thumbnail -->
        <div class="relative h-48 overflow-hidden bg-slate-100">
          <img
            :src="course.thumbnail_url"
            :alt="course.title"
            class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
            loading="lazy"
          />
          <div
            class="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-60"
          ></div>

          <div class="absolute top-3 right-3 flex gap-2">
            <span
              class="px-2.5 py-1 rounded-lg text-xs font-bold backdrop-blur-md border border-white/20 shadow-sm"
              :class="
                course.published ? 'bg-emerald-500/90 text-white' : 'bg-slate-500/90 text-white'
              "
            >
              {{ course.published ? 'Đang hoạt động' : 'Nháp' }}
            </span>
          </div>

          <div class="absolute bottom-3 left-4 right-4 text-white">
            <div class="flex items-center gap-2 mb-1">
              <span
                class="bg-white/20 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border border-white/10"
              >
                {{ course.subject?.title }}
              </span>
              <span
                class="bg-white/20 backdrop-blur-md px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border border-white/10"
              >
                Lớp {{ course.grade }}
              </span>
            </div>
          </div>
        </div>

        <!-- Content -->
        <div class="p-5 flex-1 flex flex-col">
          <h3
            class="font-bold text-lg text-gray-900 leading-snug mb-2 line-clamp-2 group-hover:text-[rgb(var(--primary))] transition-colors"
          >
            {{ course.title }}
          </h3>

          <div class="flex items-center gap-4 text-xs font-medium text-slate-500 mb-4">
            <div class="flex items-center gap-1">
              <span>📖</span> {{ course.stats?.total_lessons ?? 0 }} bài học
            </div>
            <div class="flex items-center gap-1">
              <span>👥</span> {{ course.stats?.students_count ?? 0 }} học viên
            </div>
          </div>

          <div class="mt-auto pt-4 border-t border-slate-50 flex items-center justify-between">
            <div class="text-sm font-bold text-[rgb(var(--primary))]">
              {{
                course.is_free
                  ? 'Miễn phí'
                  : new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(
                      Number(course.price),
                    )
              }}
            </div>
            <div class="flex gap-2">
              <button
                @click="handleEdit(course.id)"
                class="p-2 text-slate-400 hover:text-[rgb(var(--primary))] hover:bg-indigo-50 rounded-lg transition-colors"
                title="Chỉnh sửa"
              >
                <span class="text-lg">✎</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
