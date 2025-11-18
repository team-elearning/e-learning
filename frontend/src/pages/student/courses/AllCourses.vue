<template>
  <div class="all-courses-page">
    <div class="all-courses">
      <header class="page-header">
        <div>
          <p class="breadcrumb">Khoá học của tôi · Tất cả khoá học</p>
          <h1>Tất cả khoá học</h1>
          <p class="lead">Danh sách toàn bộ khoá học đang có trên hệ thống.</p>
        </div>
        <div class="actions">
          <router-link class="ghost" :to="{ name: 'MyCourses' }">Quay lại</router-link>
          <button class="primary" type="button" @click="load" :disabled="loading">Làm mới</button>
        </div>
      </header>

      <div class="filters">
        <div class="search">
          <svg viewBox="0 0 24 24"><path d="M21 21l-4.3-4.3" /><circle cx="11" cy="11" r="7" /></svg>
          <input v-model.trim="q" placeholder="Tìm kiếm khoá học..." />
        </div>
        <select v-model="grade" class="select">
          <option value="">Tất cả khối</option>
          <option v-for="g in [1, 2, 3, 4, 5]" :key="g" :value="g">Khối {{ g }}</option>
        </select>
        <select v-model="subject" class="select">
          <option value="">Tất cả môn</option>
          <option v-for="s in subjectOptions" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>
        <div class="count" v-if="filtered.length">
          {{ filtered.length }} / {{ totalCount }} khoá
        </div>
      </div>

      <div class="grid" v-if="!loading">
        <article v-for="c in filtered" :key="c.id" class="card" @click="openDetail(c.id)">
          <div class="thumb">
            <img :src="c.thumbnail" :alt="c.title" />
          </div>
          <div class="meta">
            <div class="title">{{ c.title }}</div>
            <div class="info">
              <span class="pill">Khối {{ c.grade }}</span>
              <span class="pill muted">{{ subjectLabel(c.subject) }}</span>
              <span class="pill muted">Bài học: {{ c.lessonsCount }}</span>
            </div>
          </div>
        </article>
      </div>

      <div v-else class="empty">Đang tải khoá học...</div>
      <div v-if="!loading && !filtered.length" class="empty">Không tìm thấy khoá học phù hợp.</div>
      <div v-if="err" class="empty err">{{ err }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  courseService,
  type CourseStatus,
  type CourseSummary,
  type Subject,
} from '@/services/course.service'

const router = useRouter()

const q = ref('')
const grade = ref<number | ''>('')
const subject = ref<Subject | ''>('')
const loading = ref(false)
const err = ref('')
const all = ref<CourseSummary[]>([])
const totalCount = ref(0)

const subjectOptions = [
  { value: 'math', label: 'Toán' },
  { value: 'vietnamese', label: 'Tiếng Việt' },
  { value: 'english', label: 'Tiếng Anh' },
  { value: 'science', label: 'Khoa học' },
  { value: 'history', label: 'Lịch sử' },
]

function subjectLabel(s: Subject) {
  return subjectOptions.find((x) => x.value === s)?.label || s
}

function matchesText(c: CourseSummary, k: string) {
  const key = k.toLowerCase()
  return (
    c.title.toLowerCase().includes(key) ||
    String(c.id).includes(key) ||
    c.teacherName.toLowerCase().includes(key)
  )
}

const filtered = computed(() => {
  let list = all.value.slice()
  if (q.value) list = list.filter((c) => matchesText(c, q.value))
  if (grade.value) list = list.filter((c) => c.grade === grade.value)
  if (subject.value) list = list.filter((c) => c.subject === subject.value)
  return list
})

async function load() {
  try {
    loading.value = true
    err.value = ''
    const { items, total } = await courseService.list({
      page: 1,
      pageSize: 200,
      status: 'published' as CourseStatus,
      sortBy: 'updatedAt' as const,
      sortDir: 'descending' as const,
    })
    all.value = items || []
    totalCount.value = total || all.value.length
  } catch (e: any) {
    err.value = e?.message || 'Không tải được danh sách khoá học'
  } finally {
    loading.value = false
  }
}

function openDetail(id: number | string) {
  if (router.hasRoute('student-course-detail'))
    router.push({ name: 'student-course-detail', params: { id } })
  else router.push(`/student/courses/${id}`)
}

onMounted(load)
</script>

<style scoped>
.all-courses-page {
  background: var(--bg, #f6f7fb);
  min-height: 100vh;
  color: var(--text, #0f172a);
}
.all-courses {
  max-width: 1200px;
  margin: 0 auto;
  padding: 22px 18px 28px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}
.breadcrumb {
  color: #6b7280;
  font-weight: 600;
  font-size: 13px;
}
h1 {
  font-size: 28px;
  font-weight: 800;
  margin-top: 4px;
}
.lead {
  color: var(--muted, #6b7280);
  margin-top: 4px;
}
.actions {
  display: flex;
  gap: 10px;
  align-items: center;
}
.ghost,
.primary {
  border-radius: 10px;
  padding: 9px 14px;
  font-weight: 700;
  border: 1px solid var(--line, #e5e7eb);
  background: #fff;
  cursor: pointer;
}
.primary {
  background: var(--accent, #16a34a);
  border-color: var(--accent, #16a34a);
  color: #fff;
}
.ghost:hover {
  background: #f3f4f6;
}
.primary:hover {
  filter: brightness(0.98);
}
.primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
.filters {
  margin-top: 18px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}
.search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid var(--line, #e5e7eb);
  padding: 8px 12px;
  border-radius: 10px;
  flex: 1;
  min-width: 240px;
}
.search input {
  border: 0;
  outline: 0;
  width: 100%;
  color: var(--text, #0f172a);
}
.search svg {
  width: 18px;
  height: 18px;
  stroke: #9ca3af;
  fill: none;
  stroke-width: 2;
}
.select {
  border: 1px solid var(--line, #e5e7eb);
  border-radius: 10px;
  padding: 8px 10px;
  min-width: 140px;
}
.count {
  font-weight: 700;
  color: var(--accent, #16a34a);
}
.grid {
  margin-top: 18px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 14px;
}
.card {
  background: #fff;
  border: 1px solid var(--line, #e5e7eb);
  border-radius: 18px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 120ms ease, box-shadow 120ms ease;
  display: flex;
  flex-direction: column;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
}
.thumb img {
  width: 100%;
  height: 140px;
  object-fit: cover;
  display: block;
}
.meta {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.title {
  font-weight: 800;
  line-height: 1.4;
}
.info {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}
.pill {
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(22, 163, 74, 0.12);
  color: #166534;
  font-weight: 700;
  font-size: 12px;
}
.pill.muted {
  background: #f3f4f6;
  color: #4b5563;
}
.empty {
  padding: 32px 12px;
  text-align: center;
  color: var(--muted, #6b7280);
}
.err {
  color: #b91c1c;
}
</style>
