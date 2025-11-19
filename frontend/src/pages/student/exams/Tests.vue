<template>
  <div class="exams-page-ui">
    <div class="container">
      <!-- Header -->
      <div class="header">
        <h1 class="title">Danh sách đề thi</h1>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>Đang tải...</p>
      </div>

      <!-- Error -->
      <div v-else-if="error" class="error-message">
        {{ error }}
      </div>

      <!-- Exam Grid -->
      <div v-else class="exams-grid">
        <div v-for="exam in exams" :key="exam.id" class="exam-card" @click="goToExam(exam.id)">
          <div class="card-header">
            <div class="exam-icon">
              <svg
                xmlns="http://www.w3.org/2000/svg"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <div class="level-badge" :class="`level-${exam.level}`">
              {{ getLevelText(exam.level) }}
            </div>
          </div>

          <div class="card-body">
            <h3 class="exam-title">{{ exam.title }}</h3>

            <div class="exam-meta">
              <div class="meta-item">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>{{ getDuration(exam.durationSec) }} phút</span>
              </div>
              <div class="meta-item">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <span>{{ exam.questionsCount }} câu</span>
              </div>
            </div>
          </div>

          <div class="card-footer">
            <button class="start-btn">Bắt đầu làm bài</button>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-if="!loading && !error && exams.length === 0" class="empty-state">
        <svg
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        <p>Chưa có đề thi nào</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { examService, type ExamSummary, type Level } from '@/services/exam.service'

const router = useRouter()

const exams = ref<ExamSummary[]>([])
const loading = ref(false)
const error = ref('')

const getLevelText = (level: Level): string => {
  return level
}

const getDuration = (durationSec: number): number => {
  return Math.floor(durationSec / 60)
}

const goToExam = (examId: string | number) => {
  router.push({ name: 'student-test-taking', params: { id: examId } })
}

const loadExams = async () => {
  try {
    loading.value = true
    error.value = ''
    const data = await examService.list()
    exams.value = data
  } catch (e: any) {
    error.value = e?.message || 'Không thể tải danh sách đề thi'
    exams.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadExams()
})
</script>

<style scoped>
.exams-page-ui {
  min-height: 100vh;
  background: #f8fafc;
  padding: 32px 0 40px;
  --accent: #16a34a;
  --accent-dark: #15803d;
  --accent-soft: #dcfce7;
  --muted: #6b7280;
  --line: #e5e7eb;
  --text: #0f172a;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 18px;
}

/* Header */
.header {
  text-align: center;
  margin-bottom: 30px;
}

.title {
  font-size: 32px;
  font-weight: 800;
  color: var(--text);
  margin: 0;
}

/* Loading */
.loading {
  text-align: center;
  padding: 4rem 0;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e5e7eb;
  border-top-color: var(--accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.loading p {
  color: var(--muted);
  font-size: 1rem;
}

/* Error */
.error-message {
  text-align: center;
  padding: 2rem;
  background: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 0.5rem;
  color: #dc2626;
}

/* Exams Grid */
.exams-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 1.5rem;
}

.exam-card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  overflow: hidden;
  transition: all 0.2s;
  cursor: pointer;
  display: flex;
  flex-direction: column;
}

.exam-card:hover {
  border-color: var(--accent);
  box-shadow: 0 8px 20px rgba(22, 163, 74, 0.12);
  transform: translateY(-2px);
}

.card-header {
  padding: 18px 20px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 1px solid #f3f4f6;
}

.exam-icon {
  width: 40px;
  height: 40px;
  background: #f0fdf4;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--accent);
}

.exam-icon svg {
  width: 24px;
  height: 24px;
}

.level-badge {
  padding: 6px 12px;
  border-radius: 9999px;
  font-size: 12px;
  font-weight: 700;
  text-transform: uppercase;
}

.level-1 {
  background: #dbeafe;
  color: #1e40af;
}

.level-2 {
  background: #fef3c7;
  color: #b45309;
}

.level-3 {
  background: #fee2e2;
  color: #dc2626;
}

.card-body {
  padding: 18px 20px 12px;
  flex: 1;
}

.exam-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--text);
  margin: 0 0 8px 0;
}

.exam-description {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0 0 1rem 0;
  line-height: 1.5;
}

.exam-meta {
  display: flex;
  gap: 1rem;
  margin-top: auto;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  font-size: 0.875rem;
  color: #6b7280;
}

.meta-item svg {
  width: 16px;
  height: 16px;
}

.card-footer {
  padding: 16px 20px 20px;
  border-top: 1px solid #f3f4f6;
}

.start-btn {
  width: 100%;
  padding: 12px 14px;
  background: var(--accent);
  color: #fff;
  border: 1px solid var(--accent-dark);
  border-radius: 10px;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.16s ease;
  box-shadow: 0 3px 0 var(--accent-dark);
}

.start-btn:hover {
  background: var(--accent-dark);
  box-shadow: 0 2px 0 #166534;
}

/* Empty State */
.empty-state {
  text-align: center;
  padding: 4rem 2rem;
  color: #9ca3af;
}

.empty-state svg {
  width: 64px;
  height: 64px;
  margin: 0 auto 1rem;
  opacity: 0.5;
}

.empty-state p {
  font-size: 1.125rem;
  margin: 0;
}

/* Responsive */
@media (max-width: 768px) {
  .exams-grid {
    grid-template-columns: 1fr;
  }

  .title {
    font-size: 1.5rem;
  }
}
</style>
