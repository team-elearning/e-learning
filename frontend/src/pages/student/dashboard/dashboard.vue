<!-- src/pages/student/dashboard/dashboard.vue -->
<template>
  <div class="student-dashboard">
    <div class="container">
      <div v-if="errMsg" class="err">
        <div class="err-title">Đã xảy ra lỗi khi tải Dashboard</div>
        <pre class="err-pre">{{ errMsg }}</pre>
      </div>

      <!-- Continue Learning -->
      <section class="card hero">
        <div class="hero-head">Continue Learning</div>

        <div class="hero-body" v-if="resumeCourse">
          <div class="hero-title">{{ resumeCourse.title }}</div>
          <div class="hero-sub">
            {{ resumeCourse.done ? 'Đã hoàn thành' : `Đang học · ${resumeCourse.progress}%` }}
          </div>
          <div class="hero-progress">
            <span>Progress</span>
            <div class="spacer" />
            <button class="btn-primary" @click="onResume">Resume</button>
          </div>
        </div>

        <div class="hero-body" v-else>
          <div class="hero-title">Chưa có khóa học</div>
          <div class="hero-sub">Bắt đầu từ trang Khóa học</div>
          <div class="hero-progress">
            <span></span>
            <div class="spacer" />
            <button class="btn-primary" @click="goToCourses">Xem khóa học</button>
          </div>
        </div>
      </section>

      <!-- My Courses -->
      <section class="card">
        <div class="section-head">
          <h2>My Courses</h2>
          <button class="ghost" aria-label="view more" @click="goToCourses">›</button>
        </div>

        <div class="courses" v-if="featured.length">
          <div
            class="course-card"
            v-for="c in featured"
            :key="String(c.id)"
            @click="openCourse(Number(c.id))"
          >
            <img class="thumb" :src="c.thumbnail" :alt="c.title" />
            <div class="title">{{ c.title }}</div>
            <div class="progress-line">
              <div class="bar" :style="{ width: ((c.done ? 100 : c.progress) || 0) + '%' }"></div>
            </div>
            <div class="status muted">
              {{ c.done ? 'Đã hoàn thành' : `Đang học · ${c.progress}%` }}
            </div>
          </div>
        </div>
        <div v-else class="muted">Chưa có khóa học nào.</div>
      </section>

      <!-- Practice Exams -->
      <section class="card">
        <div class="section-head">
          <h2>Practice Exams</h2>
          <button class="ghost" aria-label="view more" @click="openExamsList">›</button>
        </div>

        <ul class="exams" v-if="previewExams.length">
          <li class="exam-row" v-for="e in previewExams" :key="String(e.id)">
            <label class="checkbox"><input type="checkbox" disabled /><span></span></label>
            <div class="exam-main">
              <div class="exam-title">{{ e.title }}</div>
              <div class="muted small">
                Khối {{ e.grade }} · {{ toMin(e.duration) }} phút · Đạt ≥ {{ e.pass }} câu
              </div>
            </div>
            <button class="btn-outline" @click="openExamDetail(e.id)">Làm bài</button>
          </li>
        </ul>
        <div v-else class="muted small" style="padding: 6px 2px">Hiện chưa có đề phù hợp.</div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { courseService, type CourseSummary } from '@/services/course.service'
import { useExamStore } from '@/store/exam.store'
// ✅ CÁCH IMPORT ĐÚNG
import * as echarts from 'echarts/core'

// Import các loại biểu đồ bạn cần (ví dụ: BarChart, LineChart, PieChart)
import { BarChart } from 'echarts/charts'

// Import các component cần thiết (ví dụ: Title, Tooltip, Grid)
import { TitleComponent, TooltipComponent, GridComponent } from 'echarts/components'

// Import renderer (dùng Canvas hoặc SVG)
import { CanvasRenderer } from 'echarts/renderers'

// Đăng ký các component đã import
echarts.use([TitleComponent, TooltipComponent, GridComponent, BarChart, CanvasRenderer])
type CourseCard = CourseSummary & { progress: number; done: boolean }

const router = useRouter()
const errMsg = ref('')

// ===== Courses =====
const featured = ref<CourseCard[]>([])
const resumeCourse = ref<CourseCard | null>(null)

async function fetchCourses() {
  try {
    const { items } = await courseService.list({
      page: 1,
      pageSize: 12,
      status: 'published',
      sortBy: 'updatedAt',
      sortDir: 'descending',
    })
    const mapped: CourseCard[] = (items || []).map((c) => {
      const p = (Number(c.id) * 13) % 100
      return { ...c, progress: p, done: p >= 100 }
    })
    featured.value = mapped.slice(0, 6)
    resumeCourse.value = mapped.find((c) => c.progress > 0 && c.progress < 100) || mapped[0] || null
  } catch (e: any) {
    errMsg.value = `courseService.list lỗi: ${e?.message || String(e)}`
  }
}

// ===== Exams =====
const examStore = useExamStore()
const previewExams = computed(() => {
  const list: any[] = (examStore.exams as any[]) || []
  if (!list.length) return []
  const grade = resumeCourse.value?.grade
  const prioritized = grade
    ? [...list.filter((e) => e.grade === grade), ...list.filter((e) => e.grade !== grade)]
    : list.slice()
  return prioritized.slice(0, 2)
})

function toMin(s: number) {
  return Math.round((Number(s) || 0) / 60)
}

// ===== Navigation helpers with fallback =====
function hasRoute(name: string) {
  return router.hasRoute(name as any)
}
function goToCourses() {
  if (hasRoute('MyCourses')) router.push({ name: 'MyCourses' })
  else router.push('/student/courses') // đổi path theo router của bạn
}
function openCourse(id: number) {
  if (hasRoute('MyCourses')) router.push({ name: 'MyCourses', query: { highlight: String(id) } })
  else router.push({ path: '/student/courses', query: { highlight: String(id) } })
}
function onResume() {
  if (!resumeCourse.value) return
  openCourse(Number(resumeCourse.value.id))
}
function openExamsList() {
  if (hasRoute('student-exams')) router.push({ name: 'student-exams' })
  else router.push('/student/exams') // đổi path đúng với router của bạn
}
function openExamDetail(id: number | string) {
  if (hasRoute('student-exam-detail')) router.push({ name: 'student-exam-detail', params: { id } })
  else router.push(`/student/exams/${id}`)
}

onMounted(async () => {
  await fetchCourses()
  try {
    await examStore.fetchExams()
  } catch (e: any) {
    errMsg.value = `examStore.fetchExams lỗi: ${e?.message || String(e)}`
  }
})
</script>

<style>
:root {
  --bg: #f6f7fb;
  --card: #fff;
  --text: #0f172a;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #42b983;
}
.student-dashboard {
  min-height: 100vh;
  background: var(--bg);
  color: var(--text);
}
.container {
  padding: 20px 16px 40px;
  max-width: 980px;
  margin: 0 auto;
  display: grid;
  gap: 16px;
}
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 14px;
  box-shadow: 0 1px 0 rgba(16, 24, 40, 0.02);
  padding: 14px;
}
.err {
  border: 1px solid #fecaca;
  background: #fff1f2;
  color: #7f1d1d;
  border-radius: 12px;
  padding: 12px;
}
.err-title {
  font-weight: 700;
  margin-bottom: 6px;
}
.err-pre {
  white-space: pre-wrap;
  font-family: ui-monospace, Menlo, monospace;
  font-size: 12px;
}
.hero .hero-head {
  font-weight: 600;
  font-size: 20px;
  margin-bottom: 12px;
}
.hero-body {
  background: #0b2952;
  color: #e6eefc;
  border-radius: 12px;
  padding: 16px;
}
.hero-title {
  font-size: 18px;
  font-weight: 700;
}
.hero-sub {
  margin-top: 6px;
  opacity: 0.9;
}
.hero-progress {
  margin-top: 14px;
  display: flex;
  align-items: center;
}
.hero-progress .spacer {
  flex: 1;
}
.btn-primary {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 110px;
  height: 44px;
  padding: 0 16px;
  border-radius: 10px;
  background: #fff !important;
  color: #0b2952 !important;
  border: 1px solid #c9d9ff !important;
  font-weight: 700;
  font-size: 14px;
}
.btn-primary:hover {
  background: #f6f9ff !important;
  border-color: #b7cbff !important;
}
.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}
.section-head h2 {
  font-size: 16px;
  font-weight: 700;
}
.ghost {
  background: transparent;
  border: none;
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}
.courses {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}
.course-card {
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px;
  cursor: pointer;
  background: #fff;
}
.course-card:hover {
  background: #fafafa;
}
.course-card .thumb {
  width: 100%;
  height: 90px;
  object-fit: cover;
  border-radius: 8px;
  margin-bottom: 8px;
}
.course-card .title {
  font-weight: 600;
}
.progress-line {
  margin-top: 8px;
  height: 6px;
  background: #eef2f7;
  border-radius: 999px;
  overflow: hidden;
}
.progress-line .bar {
  height: 100%;
  background: var(--accent);
}
.status {
  margin-top: 6px;
  font-size: 12px;
}
.exams {
  display: grid;
  gap: 10px;
}
.exam-row {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  gap: 10px;
  align-items: center;
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 10px;
}
.checkbox {
  position: relative;
  width: 18px;
  height: 18px;
  display: grid;
  place-items: center;
}
.checkbox input {
  position: absolute;
  inset: 0;
  opacity: 0;
  cursor: default;
}
.checkbox span {
  width: 16px;
  height: 16px;
  border: 1px solid var(--line);
  border-radius: 4px;
  background: #fff;
}
.exam-title {
  font-weight: 700;
}
.btn-outline {
  background: transparent;
  border: 1px solid var(--line);
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 700;
}
.muted {
  color: var(--muted);
}
.small {
  font-size: 12px;
}
@media (max-width: 900px) {
  .courses {
    grid-template-columns: repeat(2, 1fr);
  }
}
@media (max-width: 640px) {
  .courses {
    grid-template-columns: 1fr;
  }
}
</style>
