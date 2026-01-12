<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { studentCoursesApi } from '../../api/student-courses.api'
import type { StudentCourse, Course } from '../../types/course.types'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const activeTab = ref<'registered' | 'extended'>('registered')
const myCourses = ref<StudentCourse[]>([])
const extendedCourses = ref<Course[]>([])
const isLoading = ref(false)

async function fetchMyCourses() {
  isLoading.value = true
  try {
    const res = await studentCoursesApi.getMyCourses()
    myCourses.value = res.data
  } catch (error) {
    ElMessage.error('Không thể tải danh sách khóa học của tôi')
  } finally {
    isLoading.value = false
  }
}

async function fetchExtendedCourses() {
  isLoading.value = true
  try {
    // We need current enrolled courses to filter them out
    if (myCourses.value.length === 0) {
      const resMy = await studentCoursesApi.getMyCourses()
      myCourses.value = resMy.data
    }

    const res = await studentCoursesApi.getAllCourses()
    const allCourses = res.data

    // Filter out courses that are already registered
    const myCourseIds = new Set(myCourses.value.map((c) => c.id))
    extendedCourses.value = allCourses.filter((c) => !myCourseIds.has(c.id))
  } catch (error) {
    ElMessage.error('Không thể tải danh sách khóa học mở rộng')
  } finally {
    isLoading.value = false
  }
}

function handleTabChange(tab: 'registered' | 'extended') {
  activeTab.value = tab
  if (tab === 'registered') {
    fetchMyCourses()
  } else {
    fetchExtendedCourses()
  }
}

function goToCourse(courseId: string) {
  router.push(`/student/courses/${courseId}`)
}

async function handleUnenroll(course: StudentCourse) {
  try {
    await ElMessageBox.confirm(
      `Bạn có chắc chắn muốn hủy đăng ký khóa học "${course.title}"?`,
      'Hủy đăng ký',
      {
        confirmButtonText: 'Hủy đăng ký',
        cancelButtonText: 'Không',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )

    await studentCoursesApi.unenrollCourse(course.id)
    ElMessage.success('Hủy đăng ký thành công')
    fetchMyCourses()
  } catch {
    // Cancelled
  }
}

async function handleEnroll(course: Course) {
  const price = Number(course.price) || 0
  if (price > 0) {
    ElMessage.info('Tính năng thanh toán đang phát triển')
    return
  }

  try {
    await ElMessageBox.confirm(
      `Bạn có muốn đăng ký khóa học miễn phí "${course.title}" ngay bây giờ?`,
      'Đăng ký khóa học',
      {
        confirmButtonText: 'Đăng ký ngay',
        cancelButtonText: 'Để sau',
        type: 'info',
      },
    )

    await studentCoursesApi.enrollCourse(course.id)
    ElMessage.success('Ghi danh thành công')
    // Remove from extended list
    extendedCourses.value = extendedCourses.value.filter((c) => c.id !== course.id)
    // Switch to registered tab or just notify? Let's switch to registered to show progress
    activeTab.value = 'registered'
    fetchMyCourses()
  } catch {
    // Cancelled
  }
}

onMounted(() => {
  fetchMyCourses()
})
</script>

<template>
  <div class="p-6 lg:p-8 min-h-screen bg-slate-50">
    <div class="max-w-7xl mx-auto">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
        <div>
          <h1 class="text-2xl font-bold text-gray-900 tracking-tight">Khóa học của tôi</h1>
          <p class="text-slate-500 mt-1">Tiếp tục hành trình học tập của bạn</p>
        </div>
      </div>

      <!-- Tabs -->
      <div class="border-b border-slate-200 mb-8">
        <nav class="flex gap-6" aria-label="Tabs">
          <button
            @click="handleTabChange('registered')"
            :class="[
              activeTab === 'registered'
                ? 'border-[rgb(var(--primary))] text-[rgb(var(--primary))]'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors',
            ]"
          >
            Khóa học đã đăng ký
          </button>
          <button
            @click="handleTabChange('extended')"
            :class="[
              activeTab === 'extended'
                ? 'border-[rgb(var(--primary))] text-[rgb(var(--primary))]'
                : 'border-transparent text-slate-500 hover:text-slate-700 hover:border-slate-300',
              'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm transition-colors',
            ]"
          >
            Khóa học mở rộng
          </button>
        </nav>
      </div>

      <!-- Content -->
      <div v-if="activeTab === 'registered'">
        <!-- Loading -->
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
          v-else-if="myCourses.length === 0"
          class="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-300"
        >
          <div class="text-6xl mb-4">📚</div>
          <h3 class="text-xl font-bold text-gray-800 mb-2">Bạn chưa đăng ký khóa học nào</h3>
          <p class="text-slate-500 mb-6">
            Hãy khám phá các khóa học thú vị và bắt đầu học tập ngay hôm nay!
          </p>
          <button
            @click="handleTabChange('extended')"
            class="text-[rgb(var(--primary))] font-semibold hover:underline"
          >
            Khám phá khóa học
          </button>
        </div>

        <!-- List -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <div
            v-for="course in myCourses"
            :key="course.id"
            class="group bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden flex flex-col h-full cursor-pointer"
            @click="goToCourse(course.id)"
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
                v-if="course.my_progress?.is_completed"
                class="absolute top-2 right-2 bg-green-500 text-white text-xs font-bold px-2 py-1 rounded-full shadow-sm"
              >
                Đã hoàn thành
              </div>
            </div>

            <!-- Body -->
            <div class="p-5 flex flex-col flex-1">
              <div class="mb-2">
                <span
                  class="inline-block px-2 py-1 bg-slate-100 text-slate-600 text-xs font-semibold rounded-md mb-2"
                >
                  {{ course.subject?.title || 'General' }}
                </span>
                <h3
                  class="text-lg font-bold text-gray-900 group-hover:text-[rgb(var(--primary))] transition-colors line-clamp-2"
                >
                  {{ course.title }}
                </h3>
              </div>

              <div class="mt-auto pt-4 border-t border-slate-50">
                <!-- Progress Bar -->
                <div
                  class="mb-2 flex justify-between items-center text-xs text-slate-500 font-medium"
                >
                  <span>Tiến độ</span>
                  <span
                    >{{
                      Math.round(
                        course.percent_completed || course.my_progress?.percent_completed || 0,
                      )
                    }}%</span
                  >
                </div>
                <div class="h-2 bg-slate-100 rounded-full overflow-hidden">
                  <div
                    class="h-full bg-[rgb(var(--primary))] rounded-full transition-all duration-500"
                    :style="{
                      width: `${course.percent_completed || course.my_progress?.percent_completed || 0}%`,
                    }"
                  ></div>
                </div>

                <div class="mt-3 flex items-center justify-between text-xs text-slate-400">
                  <span>{{ course.stats?.total_lessons || 0 }} bài học</span>
                  <button
                    @click.stop="handleUnenroll(course)"
                    class="text-red-500 hover:text-red-700 hover:underline px-2"
                    title="Hủy đăng ký"
                  >
                    Hủy
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="activeTab === 'extended'">
        <!-- Loading -->
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
          v-else-if="extendedCourses.length === 0"
          class="text-center py-20 bg-white rounded-3xl border border-dashed border-slate-300"
        >
          <div class="text-6xl mb-4">🎉</div>
          <h3 class="text-xl font-bold text-gray-800 mb-2">Bạn đã đăng ký tất cả các khóa học!</h3>
          <p class="text-slate-500">
            Tuyệt vời, hãy quay lại tab "Khóa học đã đăng ký" để bắt đầu học.
          </p>
          <button
            @click="activeTab = 'registered'"
            class="mt-4 text-[rgb(var(--primary))] font-semibold hover:underline"
          >
            Về khóa học của tôi
          </button>
        </div>

        <!-- Content List -->
        <div v-else class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
          <div
            v-for="course in extendedCourses"
            :key="course.id"
            class="group bg-white rounded-2xl border border-slate-100 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden flex flex-col h-full"
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
                class="absolute top-2 right-2 bg-slate-900/70 backdrop-blur-md text-white px-3 py-1 rounded-full text-xs font-bold"
              >
                {{
                  course.is_free
                    ? 'Miễn phí'
                    : `${Number(course.price).toLocaleString()} ${course.currency}`
                }}
              </div>
            </div>

            <!-- Body -->
            <div class="p-5 flex flex-col flex-1">
              <div class="mb-2">
                <span
                  class="inline-block px-2 py-1 bg-slate-100 text-slate-600 text-xs font-semibold rounded-md mb-2"
                >
                  {{ course.subject?.title || 'General' }}
                </span>
                <h3 class="text-lg font-bold text-gray-900 line-clamp-2 mb-1">
                  {{ course.title }}
                </h3>
                <p class="text-slate-500 text-sm line-clamp-2 h-10">
                  {{ course.short_description || 'Chưa có mô tả' }}
                </p>
              </div>

              <div class="mt-auto pt-4 border-t border-slate-50">
                <div class="flex items-center justify-between">
                  <div class="text-xs text-slate-500">
                    <span class="block font-bold text-slate-700 text-sm">{{
                      course.owner_name
                    }}</span>
                    <span>Giảng viên</span>
                  </div>
                  <button
                    @click="handleEnroll(course)"
                    class="bg-[rgb(var(--primary))] hover:bg-[rgb(var(--primary))]/90 text-white px-4 py-2 rounded-lg text-sm font-semibold shadow-md shadow-indigo-100 transition-all"
                  >
                    {{ course.is_free ? 'Đăng ký ngay' : 'Mua khóa học' }}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
