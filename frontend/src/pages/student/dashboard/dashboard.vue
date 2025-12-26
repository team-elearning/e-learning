<!-- src/pages/student/dashboard/dashboard.vue -->
<template>
  <div class="student-dashboard">
    <div class="container">
      <!-- ERROR -->
      <div v-if="errMsg" class="err">
        <div class="err-title">Đã xảy ra lỗi khi tải Dashboard</div>
        <pre class="err-pre">{{ errMsg }}</pre>
      </div>

      <!-- CONTINUE LEARNING -->
      <section
        class="hero hero-cover"
        :style="
          resumeCourse?.thumbnail
            ? { backgroundImage: `url(${thumbSource(resumeCourse.id, resumeCourse.thumbnail)})` }
            : {}
        "
      >
        <div class="hero-inner">
          <div class="hero-body" v-if="resumeCourse">
            <div class="hero-title">{{ resumeCourse.title }}</div>
            <div class="hero-sub">
              {{ resumeCourse.done ? 'Đã hoàn thành' : `Đang học · ${resumeCourse.progress}%` }}
            </div>

            <div class="hero-progress">
              <span>Tiến độ</span>
              <div class="spacer" />
              <button class="btn-primary" @click="onResume">Vào học tiếp</button>
            </div>
          </div>
        </div>
      </section>

      <!-- MAIN GRID -->
      <section class="dashboard-grid">
        <!-- LEFT: MY COURSES -->
        <div class="left-col">
          <section class="card">
            <div class="section-head">
              <h2>Khóa học của tôi</h2>
              <button class="ghost" @click="goToCourses">›</button>
            </div>

            <div class="courses" v-if="featured.length">
              <div
                class="course-card"
                v-for="c in featured"
                :key="String(c.id)"
                @click="goToPlayer(c.id)"
              >
                <div :class="['thumb', { loaded: isThumbLoaded(c.id) }]">
                  <img
                    :src="thumbSource(c.id, c.thumbnail)"
                    :alt="c.title"
                    loading="lazy"
                    @load="markThumbLoaded(c.id)"
                    @error="(e) => handleThumbError(e, c.id)"
                  />
                  <div v-if="isThumbMissing(c.id)" class="thumb-empty">Không có ảnh</div>
                </div>

                <div class="title">{{ c.title }}</div>

                <div
                  class="progress-line"
                  :style="{ '--progress-target': ((c.done ? 100 : c.progress) || 0) + '%' }"
                >
                  <div class="bar"></div>
                </div>

                <div class="status muted">
                  {{ c.done ? 'Đã hoàn thành' : `Đang học · ${c.progress}%` }}
                </div>
              </div>
            </div>

            <div v-else class="muted">Bạn chưa đăng ký khóa học nào.</div>
          </section>
        </div>

        <!-- RIGHT: AI RECOMMEND -->
        <div class="right-col">
          <section class="card">
            <div class="section-head">
              <h2>🎯 Gợi ý cho bạn</h2>
            </div>

            <div v-if="aiLoading" class="muted">🤖 Đang phân tích sở thích học tập…</div>

            <div v-else-if="aiRecommend.length" class="ai-list">
              <div class="ai-course" v-for="c in aiRecommend" :key="c.id" @click="openDetail(c.id)">
                <img :src="c.thumbnail_url || PLACEHOLDER" />
                <div class="ai-info">
                  <div class="title">{{ c.title }}</div>
                  <div class="status muted">{{ c.subject?.title }} · Lớp {{ c.grade }}</div>
                </div>
              </div>
            </div>

            <div v-else class="muted">Học thêm vài khóa để nhận gợi ý phù hợp hơn nhé 🙂</div>
          </section>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  courseService,
  type CourseSummary,
  type ID,
  resolveMediaUrl,
} from '@/services/course.service'
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
const thumbLoaded = ref<Record<string, boolean>>({})
const thumbSrc = ref<Record<string, string>>({})
const thumbMissing = ref<Record<string, boolean>>({})
const PLACEHOLDER =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 225" width="400" height="225">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop stop-color="#e2e8f0" offset="0%"/>
          <stop stop-color="#cbd5e1" offset="100%"/>
        </linearGradient>
      </defs>
      <rect width="400" height="225" fill="url(#g)"/>
      <text x="200" y="118" font-size="22" font-family="Arial, sans-serif" fill="#475569" text-anchor="middle">Không có ảnh</text>
    </svg>`,
  )

async function fetchCourses() {
  try {
    const enrolled = await courseService.listMyEnrolled()

    const mapped: CourseCard[] = (enrolled || []).map((c: any) => {
      const pct = Math.round(c.my_progress?.percent_completed ?? 0)
      const done = Boolean(c.my_progress?.is_completed) || pct >= 100

      return {
        ...c,
        grade: Number(c.grade), // ⚠️ QUAN TRỌNG
        progress: done ? 100 : pct,
        done,
      }
    })

    await Promise.all(mapped.map((c) => ensureThumb(c.id, c.thumbnail)))

    // Hiển thị list My Courses
    featured.value = mapped.slice(0, 6)

    // ✅ FIX 1: chọn course đang học GẦN NHẤT (75%)
    resumeCourse.value =
      mapped
        .filter((c) => c.progress > 0 && c.progress < 100)
        .sort(
          (a, b) =>
            new Date(b.my_progress?.last_accessed_at || 0).getTime() -
            new Date(a.my_progress?.last_accessed_at || 0).getTime(),
        )[0] || null
  } catch (e: any) {
    errMsg.value = `courseService.list lỗi: ${e?.message || String(e)}`
  }
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
  goToPlayer(resumeCourse.value.id)
}

function openExamsList() {
  if (hasRoute('student-practice')) router.push({ name: 'student-practice' })
  else router.push('/student/practice')
}
function openExamDetail(id: number | string) {
  if (hasRoute('student-practice-taking'))
    router.push({ name: 'student-practice-taking', params: { examId: id } })
  else router.push(`/student/practice/${id}/taking`)
}

function markThumbLoaded(id: ID) {
  thumbLoaded.value = { ...thumbLoaded.value, [String(id)]: true }
}
function isThumbLoaded(id: ID) {
  return Boolean(thumbLoaded.value[String(id)])
}
function isThumbMissing(id: ID) {
  return Boolean(thumbMissing.value[String(id)])
}
function markThumbMissing(id: ID) {
  const key = String(id)
  thumbMissing.value = { ...thumbMissing.value, [key]: true }
  thumbSrc.value = { ...thumbSrc.value, [key]: PLACEHOLDER }
  thumbLoaded.value = { ...thumbLoaded.value, [key]: true }
}
function handleThumbError(event: Event, id: ID) {
  const img = event.target as HTMLImageElement | null
  if (img) img.style.opacity = '0'
  markThumbMissing(id)
}
async function ensureThumb(id: ID, url?: string | null) {
  const key = String(id)
  if (!url) {
    markThumbMissing(id)
    return
  }
  if (thumbSrc.value[key]) return
  try {
    const resolved = await resolveMediaUrl(url)
    if (resolved) {
      thumbSrc.value = { ...thumbSrc.value, [key]: resolved }
    } else {
      markThumbMissing(id)
    }
  } catch (error) {
    console.warn('Không thể tải thumbnail dashboard', error)
    markThumbMissing(id)
  }
}
function thumbSource(id: ID, fallback?: string | null) {
  return thumbSrc.value[String(id)] || fallback || PLACEHOLDER
}

// AI gợi ý khóa học
// ===== AI Recommend For Me =====
const aiRecommend = ref<any[]>([])
const aiLoading = ref(false)

async function fetchAIRecommend() {
  aiLoading.value = true
  try {
    const token = localStorage.getItem('accessToken')

    const res = await fetch('/api/personalization/ai/recommend-for-me/', {
      headers: {
        Authorization: `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
    })

    if (!res.ok) throw new Error('Unauthorized')

    const data = await res.json()
    aiRecommend.value = Array.isArray(data) ? data : []
  } catch (e) {
    console.warn('[AI recommend] error', e)
    aiRecommend.value = []
  } finally {
    aiLoading.value = false
  }
}

function openDetail(id: number | string) {
  if (router.hasRoute('student-course-detail'))
    router.push({ name: 'student-course-detail', params: { id } })
  else router.push(`/student/courses/${id}`)
}

onMounted(async () => {
  await fetchCourses()
  await fetchAIRecommend()
})
async function goToPlayer(courseId: number | string) {
  try {
    const detail = await courseService.detail(courseId)

    let firstLessonId: number | string | null = null

    for (const section of detail.sections || []) {
      if (section.lessons && section.lessons.length > 0) {
        firstLessonId = section.lessons[0].id
        break
      }
    }

    if (!firstLessonId) {
      // fallback: không có lesson thì vào detail
      router.push(`/student/courses/${courseId}`)
      return
    }

    router.push(`/student/courses/${courseId}/player/${firstLessonId}`)
  } catch (e) {
    console.error('goToPlayer error', e)
    router.push(`/student/courses/${courseId}`)
  }
}
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
  width: 1600px;
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
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 8px;
  background: #f3f4f6;
}
.thumb-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
  color: #475569;
  font-weight: 600;
  font-size: 14px;
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
  --progress-target: 0%;
}
.progress-line .bar {
  height: 100%;
  background: var(--accent);
  width: var(--progress-target, 0%);
  animation: fillProgress 0.9s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
/* override thumb loader */
.course-card .thumb {
  position: relative;
}
.course-card .thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.25s ease;
}
.course-card .thumb.loaded img {
  opacity: 1;
}
.course-card .thumb::before,
.course-card .thumb::after {
  content: '';
  position: absolute;
  inset: 0;
}
.course-card .thumb::before {
  background: rgba(255, 255, 255, 0.35);
}
.course-card .thumb::after {
  width: 20px;
  height: 20px;
  border: 3px solid #cbd5f5;
  border-top-color: #16a34a;
  border-radius: 999px;
  animation: dash-spin 0.9s linear infinite;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.course-card .thumb.loaded::before,
.course-card .thumb.loaded::after {
  opacity: 0;
  visibility: hidden;
}
@keyframes fillProgress {
  from {
    width: 0;
  }
  to {
    width: var(--progress-target, 0%);
  }
}

@keyframes dash-spin {
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
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
.dashboard-grid {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 16px;
}

/* LEFT */
.left-col .courses {
  grid-template-columns: repeat(3, 1fr);
}

/* RIGHT */
.right-col {
  position: sticky;
  top: 16px;
  height: fit-content;
}

.ai-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.ai-course {
  display: flex;
  gap: 10px;
  padding: 10px;
  border-radius: 10px;
  border: 1px solid var(--line);
  cursor: pointer;
}

.ai-course:hover {
  background: #fafafa;
}

.ai-course img {
  width: 72px;
  height: 48px;
  border-radius: 6px;
  object-fit: cover;
}

.ai-course .title {
  font-weight: 700;
  font-size: 14px;
}

/* RESPONSIVE */
@media (max-width: 900px) {
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}
/* ===== HERO CONTINUE LEARNING (VIP) ===== */
.hero-cover {
  position: relative;
  padding: 28px;
  border-radius: 18px;
  overflow: hidden;
  background-size: cover;
  background-position: center;
}

/* blur nền ảnh */
.hero-cover::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.7);
  backdrop-filter: blur(18px);
  z-index: 0;
}

/* card nổi */
.hero-inner {
  position: relative;
  z-index: 1;
  max-width: 100%;
}

.hero-cover .hero-body {
  /* background: linear-gradient(135deg, #0b2952, #0f3b73); */
  /* background: linear-gradient(135deg, #51b3d8b8, #567191); */
  background: linear-gradient(135deg, #19262bb8, #2d538300);
  border-radius: 16px;
  padding: 28px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.35);
  color: #e6eefc;
}

/* chữ */
.hero-cover .hero-title {
  font-size: 22px;
  font-weight: 800;
}

.hero-cover .hero-sub {
  margin-top: 6px;
  font-size: 14px;
  opacity: 0.9;
}

/* footer */
.hero-cover .hero-progress {
  margin-top: 18px;
  display: flex;
  align-items: center;
}

/* nút */
.hero-cover .btn-primary {
  background: #fff !important;
  color: #0b2952 !important;
  border-radius: 999px;
  padding: 10px 22px;
  font-weight: 800;
}
</style>
