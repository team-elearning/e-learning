<template>
  <div class="detail-page" v-if="course">
    <div class="hero">
      <div class="hero-text">
        <p class="crumb">
          Khóa học · Khối {{ course.grade }} · {{ subjectLabel(course.subject, course.subjectName) }}
        </p>
        <h1>{{ course.title }}</h1>
        <p class="lead">{{ course.description || 'Khoá học giúp bạn nắm vững kiến thức theo lộ trình.' }}</p>
        <div class="tags">
          <span class="pill">Khối {{ course.grade }}</span>
          <span class="pill muted">{{ course.lessonsCount }} bài học</span>
          <span class="pill muted">GV {{ course.teacherName }}</span>
        </div>
      </div>
      <div :class="['hero-thumb', { loaded: heroLoaded }]">
        <img
          :src="heroSrc || course.thumbnail"
          :alt="course.title"
          loading="lazy"
          @load="onHeroLoad"
          @error="onHeroError"
        />
      </div>
    </div>

    <div class="layout">
      <section class="card">
        <h3>Nội dung khóa học</h3>
        <div class="sections">
          <article v-for="(sec, idx) in course.sections" :key="sec.id" class="section">
            <div class="sec-head">
              <div class="sec-title">{{ idx + 1 }}. {{ sec.title }}</div>
              <div class="sec-meta">{{ sec.lessons?.length || 0 }} bài</div>
            </div>
            <ul class="lessons">
              <li v-for="(l, li) in sec.lessons" :key="l.id">
                <span class="l-idx">{{ li + 1 }}</span>
                <span class="l-title">{{ l.title }}</span>
                <span class="l-type">{{ typeLabel(l.type) }}</span>
                <span class="l-time">{{ formatDuration(l.durationMinutes) }}</span>
              </li>
            </ul>
          </article>
        </div>
      </section>

      <aside class="side card">
        <h4>Thông tin</h4>
        <ul class="info">
          <li><span>Khối:</span> <b>{{ course.grade }}</b></li>
          <li><span>Môn:</span> <b>{{ subjectLabel(course.subject, course.subjectName) }}</b></li>
          <li><span>Bài học:</span> <b>{{ course.lessonsCount }}</b></li>
          <li><span>Giáo viên:</span> <b>{{ course.teacherName }}</b></li>
        </ul>
        <button class="primary block" @click="enroll">Đăng ký ngay</button>
        <button class="ghost block" @click="goBack">Quay lại</button>
      </aside>
    </div>
  </div>

  <div v-else-if="loading" class="center">Đang tải khoá học...</div>
  <div v-else class="center err">{{ err || 'Không tìm thấy khoá học' }}</div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { courseService, type CourseDetail, type Lesson, resolveMediaUrl } from '@/services/course.service'

const route = useRoute()
const router = useRouter()

const course = ref<CourseDetail | null>(null)
const loading = ref(false)
const err = ref('')
const heroLoaded = ref(false)
const heroSrc = ref('')

const SUBJECT_LABELS: Record<string, string> = {
  math: 'Toán',
  vietnamese: 'Tiếng Việt',
  english: 'Tiếng Anh',
  science: 'Khoa học',
  history: 'Lịch sử',
}

function subjectLabel(subject?: CourseDetail['subject'], subjectName?: string | null) {
  if (subjectName) return subjectName
  if (!subject) return '—'
  if (typeof subject === 'string') return SUBJECT_LABELS[subject] || subject
  return '—'
}

function typeLabel(t: Lesson['type']) {
  return t === 'video' ? 'Video' : t === 'pdf' ? 'Tài liệu' : 'Quiz'
}

function formatDuration(min?: number) {
  if (!min) return '—'
  return `${min}’`
}

async function load() {
  try {
    loading.value = true
    err.value = ''
    const id = route.params.id as any
    course.value = await courseService.detail(id)
    heroSrc.value =
      (await resolveMediaUrl(course.value?.thumbnail)) || course.value?.thumbnail || ''
    heroLoaded.value = false
  } catch (e: any) {
    err.value = e?.message || 'Không thể tải khoá học'
    course.value = null
  } finally {
    loading.value = false
  }
}

function onHeroLoad() {
  heroLoaded.value = true
}
function onHeroError(event: Event) {
  const img = event.target as HTMLImageElement | null
  if (img) img.style.opacity = '0'
  heroLoaded.value = true
}

function enroll() {
  const id = route.params.id
  if (router.hasRoute('student-payments-cart'))
    router.push({ name: 'student-payments-cart', query: { add: String(id) } })
  else router.push({ path: '/student/payments/cart', query: { add: String(id) } })
}

function goBack() {
  if (window.history.length > 1) window.history.back()
  else router.push({ name: 'MyCourses' })
}

onMounted(load)
</script>

<style scoped>
.detail-page {
  background: #f6f7fb;
  min-height: 100vh;
  color: #0f172a;
}
.hero {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 340px;
  gap: 18px;
  max-width: 1180px;
  margin: 0 auto;
  padding: 22px 18px 10px;
}
.hero-text h1 {
  margin: 6px 0 4px;
  font-size: 30px;
  font-weight: 800;
}
.crumb {
  color: #6b7280;
  font-weight: 700;
  font-size: 13px;
  margin: 0;
}
.lead {
  color: #6b7280;
  margin: 0 0 8px;
}
.hero-thumb {
  width: 100%;
  height: 220px;
  border-radius: 16px;
  border: 1px solid #e5e7eb;
  background: #fff;
  overflow: hidden;
  position: relative;
}
.hero-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.25s ease;
  display: block;
}
.hero-thumb.loaded img {
  opacity: 1;
}
.hero-thumb::before,
.hero-thumb::after {
  content: '';
  position: absolute;
  inset: 0;
}
.hero-thumb::before {
  background: rgba(255, 255, 255, 0.35);
}
.hero-thumb::after {
  width: 34px;
  height: 34px;
  border: 4px solid #cbd5f5;
  border-top-color: #16a34a;
  border-radius: 999px;
  animation: spin 0.9s linear infinite;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.hero-thumb.loaded::before,
.hero-thumb.loaded::after {
  opacity: 0;
  visibility: hidden;
}
@keyframes spin {
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}
.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin: 8px 0 10px;
}
.pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: #dcfce7;
  color: #166534;
  font-weight: 700;
  font-size: 12px;
}
.pill.muted {
  background: #f3f4f6;
  color: #4b5563;
}
.layout {
  max-width: 1180px;
  margin: 0 auto;
  padding: 0 18px 28px;
  display: grid;
  grid-template-columns: minmax(0, 2fr) 360px;
  gap: 14px;
}
.card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 14px 16px;
}
.card h3 {
  margin: 0 0 10px;
  font-size: 18px;
  font-weight: 800;
}
.sections {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.section {
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  padding: 10px;
}
.sec-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}
.sec-title {
  font-weight: 800;
}
.sec-meta {
  color: #6b7280;
  font-size: 13px;
}
.lessons {
  list-style: none;
  padding: 0;
  margin: 8px 0 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.lessons li {
  display: grid;
  grid-template-columns: 32px 1fr 90px 60px;
  align-items: center;
  gap: 8px;
  padding: 8px 10px;
  border-radius: 10px;
  background: #f8fafc;
}
.l-idx {
  font-weight: 800;
  color: #475569;
}
.l-title {
  font-weight: 700;
}
.l-type {
  font-size: 12px;
  color: #4b5563;
}
.l-time {
  font-size: 12px;
  color: #6b7280;
}
.side h4 {
  margin: 0 0 10px;
  font-size: 16px;
  font-weight: 800;
}
.info {
  list-style: none;
  padding: 0;
  margin: 0 0 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.info li {
  display: flex;
  justify-content: space-between;
  color: #4b5563;
}
.info b {
  color: #0f172a;
}
.ghost,
.primary {
  border-radius: 10px;
  padding: 10px 14px;
  font-weight: 800;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
}
.ghost {
  color: #16a34a;
  border-color: #16a34a;
}
.ghost:hover {
  background: #f3f4f6;
}
.primary {
  background: #16a34a;
  border-color: #15803d;
  color: #fff;
  box-shadow: 0 3px 0 #15803d;
}
.primary:hover {
  background: #15803d;
  box-shadow: 0 2px 0 #166534;
}
.block {
  width: 100%;
  text-align: center;
  margin-top: 8px;
}
.center {
  padding: 40px 20px;
  text-align: center;
  color: #6b7280;
}
.err {
  color: #b91c1c;
}
@media (max-width: 1024px) {
  .hero {
    grid-template-columns: 1fr;
  }
  .layout {
    grid-template-columns: 1fr;
  }
  .hero-thumb {
    height: 180px;
  }
}
</style>
