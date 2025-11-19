<template>
  <div class="lp-page">
    <div class="lp-layout">
      <header class="lp-header">
        <div>
          <p class="lp-breadcrumb">Lộ trình học</p>
          <h1>Khoá học khối {{ gradeLabel }}</h1>
          <p class="lp-lead">Danh sách khoá phù hợp cho khối {{ gradeLabel }}.</p>
        </div>
        <div class="lp-actions">
          <router-link class="ghost" :to="{ name: 'student-learning-path' }">← Chọn lộ trình</router-link>
          <button class="primary" type="button" @click="load" :disabled="loading">
            {{ loading ? 'Đang tải...' : 'Làm mới' }}
          </button>
        </div>
      </header>

      <div v-if="err" class="lp-error">{{ err }}</div>

      <div v-else-if="loading" class="lp-grid">
        <div v-for="i in 6" :key="i" class="lp-card skeleton"></div>
      </div>

      <div v-else class="lp-grid">
        <article
          v-for="c in courses"
          :key="c.id"
          class="lp-card"
          @click="openDetail(c.id)"
        >
          <img :src="c.thumbnail" :alt="c.title" class="thumb" />
          <div class="meta">
            <h3 class="title">{{ c.title }}</h3>
            <p class="sub">Khối {{ c.grade }} • {{ subjectLabel(c.subject) }}</p>
            <p class="info">{{ c.lessonsCount }} bài học · GV {{ c.teacherName }}</p>
          </div>
        </article>
      </div>

      <div v-if="!loading && !courses.length && !err" class="lp-empty">
        Không có khoá học phù hợp cho khối này.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { courseService, type CourseSummary, type Subject, type Grade } from '@/services/course.service'

const route = useRoute()
const router = useRouter()

const grade = computed<Grade | undefined>(() => {
  const g = Number(route.params.grade)
  return g >= 1 && g <= 5 ? (g as Grade) : undefined
})
const gradeLabel = computed(() => (grade.value ? grade.value : ''))

const courses = ref<CourseSummary[]>([])
const loading = ref(false)
const err = ref('')

function subjectLabel(s: Subject) {
  const map: Record<Subject, string> = {
    math: 'Toán',
    vietnamese: 'Tiếng Việt',
    english: 'Tiếng Anh',
    science: 'Khoa học',
    history: 'Lịch sử',
  }
  return map[s] || s
}

async function load() {
  try {
    loading.value = true
    err.value = ''
    const { items } = await courseService.list({
      page: 1,
      pageSize: 120,
      status: 'published',
      sortBy: 'updatedAt',
      sortDir: 'descending',
      grade: grade.value,
    })
    courses.value = (items || []).filter((c) =>
      grade.value ? c.grade === grade.value : true,
    )
  } catch (e: any) {
    err.value = e?.message || 'Không tải được danh sách khoá học'
    courses.value = []
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
.lp-page {
  background: #f6f7fb;
  min-height: 100vh;
  color: #0f172a;
}
.lp-layout {
  max-width: 1200px;
  margin: 0 auto;
  padding: 22px 18px 28px;
}
.lp-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
  margin-bottom: 16px;
}
.lp-breadcrumb {
  color: #6b7280;
  font-weight: 700;
  font-size: 13px;
}
h1 {
  font-size: 28px;
  font-weight: 800;
  margin: 6px 0 4px;
}
.lp-lead {
  color: #6b7280;
  margin: 0;
}
.lp-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}
.ghost,
.primary {
  border-radius: 10px;
  padding: 9px 14px;
  font-weight: 700;
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
.lp-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 14px;
  margin-top: 10px;
}
.lp-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
  display: flex;
  flex-direction: column;
}
.lp-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
}
.thumb {
  width: 100%;
  height: 140px;
  object-fit: cover;
}
.meta {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.title {
  font-size: 15px;
  font-weight: 800;
}
.sub {
  font-size: 13px;
  color: #4b5563;
}
.info {
  font-size: 12px;
  color: #6b7280;
}
.lp-empty {
  margin-top: 12px;
  text-align: center;
  color: #6b7280;
}
.lp-error {
  margin-top: 12px;
  padding: 12px;
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #b91c1c;
  border-radius: 10px;
}
.skeleton {
  background: #f3f4f6;
  border: 1px solid #e5e7eb;
  min-height: 180px;
}
</style>
