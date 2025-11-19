<template>
  <div class="exam-taking-page">
    <div class="exam-container">
      <!-- Header -->
      <div class="exam-header">
        <div class="header-left">
          <h1 class="exam-title">{{ examTitle }}</h1>
          <p class="exam-meta">{{ totalQuestions }} câu hỏi</p>
        </div>
      </div>

      <!-- Progress Bar -->
      <div class="progress-bar">
        <div class="progress-fill" :style="{ width: progress + '%' }"></div>
      </div>

      <!-- Question -->
      <div class="question-section">
        <div class="question-header">
          <span class="question-number">Câu {{ currentIndex + 1 }}/{{ totalQuestions }}</span>
          <span v-if="currentQuestion.score" class="question-score"
            >{{ currentQuestion.score }} điểm</span
          >
        </div>

        <div class="question-text">{{ currentQuestion.text }}</div>

        <!-- Single Choice -->
        <div v-if="currentQuestion.type === 'single'" class="choices">
          <div
            v-for="choice in currentQuestion.choices"
            :key="choice.id"
            class="choice-item"
            :class="{ selected: isSelected(choice.id) }"
            @click="selectSingleChoice(choice.id)"
          >
            <div class="choice-radio"></div>
            <div class="choice-text">{{ choice.text }}</div>
          </div>
        </div>

        <!-- Multiple Choice -->
        <div v-if="currentQuestion.type === 'multi'" class="choices">
          <div
            v-for="choice in currentQuestion.choices"
            :key="choice.id"
            class="choice-item"
            :class="{ selected: isSelected(choice.id) }"
            @click="toggleMultiChoice(choice.id)"
          >
            <div class="choice-checkbox"></div>
            <div class="choice-text">{{ choice.text }}</div>
          </div>
        </div>

        <!-- True/False -->
        <div v-if="currentQuestion.type === 'boolean'" class="boolean-choices">
          <button
            class="boolean-btn"
            :class="{ selected: answers[currentQuestion.id] === true }"
            @click="selectBoolean(true)"
          >
            Đúng
          </button>
          <button
            class="boolean-btn"
            :class="{ selected: answers[currentQuestion.id] === false }"
            @click="selectBoolean(false)"
          >
            Sai
          </button>
        </div>

        <!-- Fill in Blanks -->
        <div v-if="currentQuestion.type === 'fill'" class="fill-inputs">
          <div v-for="i in currentQuestion.blanks" :key="i" class="fill-item">
            <label>Chỗ trống {{ i }}:</label>
            <input
              v-model="fillAnswers[i - 1]"
              type="text"
              placeholder="Nhập câu trả lời..."
              @input="updateFillAnswer"
            />
          </div>
        </div>

        <!-- Match Pairs -->
        <div v-if="currentQuestion.type === 'match'" class="match-section">
          <div v-for="(pair, idx) in currentQuestion.pairs" :key="idx" class="match-item">
            <div class="match-left">{{ pair.left }}</div>
            <select v-model="matchAnswers[idx]" class="match-select" @change="updateMatchAnswer">
              <option value="">-- Chọn --</option>
              <option v-for="p in currentQuestion.pairs" :key="p.right" :value="p.right">
                {{ p.right }}
              </option>
            </select>
          </div>
        </div>

        <!-- Order Items -->
        <div v-if="currentQuestion.type === 'order'" class="order-section">
          <div v-for="(item, idx) in orderItems" :key="idx" class="order-item">
            <span class="order-number">{{ idx + 1 }}</span>
            <span class="order-text">{{ item }}</span>
            <div class="order-controls">
              <button @click="moveUp(idx)" :disabled="idx === 0" class="order-btn">↑</button>
              <button
                @click="moveDown(idx)"
                :disabled="idx === orderItems.length - 1"
                class="order-btn"
              >
                ↓
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Navigation -->
      <div class="navigation">
        <button class="nav-btn prev" @click="prevQuestion" :disabled="currentIndex === 0">
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
              d="M15 19l-7-7 7-7"
            />
          </svg>
          Câu trước
        </button>

        <button
          class="nav-btn next"
          @click="nextQuestion"
          :disabled="currentIndex === totalQuestions - 1"
        >
          Câu sau
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
              d="M9 5l7 7-7 7"
            />
          </svg>
        </button>
      </div>

      <!-- Question Map -->
      <div class="question-map">
        <div class="map-title">Danh sách câu hỏi</div>
        <div class="map-grid">
          <button
            v-for="(q, idx) in questions"
            :key="q.id"
            class="map-item"
            :class="{
              current: idx === currentIndex,
              answered: isAnswered(q.id),
            }"
            @click="goToQuestion(idx)"
          >
            {{ idx + 1 }}
          </button>
        </div>
      </div>

      <!-- Submit -->
      <div class="submit-section">
        <button class="submit-btn" @click="submitExam">Nộp bài</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { examService } from '@/services/exam.service'

const router = useRouter()
const route = useRoute()

const examId = computed(() => route.params.examId as string)
const examTitle = ref('Đề thi')
const questions = ref<any[]>([])
const currentIndex = ref(0)
const answers = ref<Record<string, any>>({})
const attemptId = ref('')

// Fill answers
const fillAnswers = ref<string[]>([])
const matchAnswers = ref<string[]>([])
const orderItems = ref<string[]>([])

const totalQuestions = computed(() => questions.value.length)
const currentQuestion = computed(() => questions.value[currentIndex.value] || {})
const progress = computed(() => {
  const answered = Object.keys(answers.value).filter((id) => isAnswered(id)).length
  return totalQuestions.value > 0 ? (answered / totalQuestions.value) * 100 : 0
})

const loadExam = async () => {
  try {
    const attempt = await examService.startAttempt(examId.value)
    attemptId.value = attempt.id
    examTitle.value = `Đề luyện tập #${examId.value}`
    questions.value = attempt.questions
    answers.value = attempt.answers || {}
    loadQuestionData()
  } catch (error) {
    console.error('Failed to load exam, fallback to mock:', error)
    const mock = buildMockAttempt()
    attemptId.value = mock.id
    examTitle.value = mock.title
    questions.value = mock.questions
    answers.value = {}
    loadQuestionData()
  }
}

const isSelected = (choiceId: string): boolean => {
  const answer = answers.value[currentQuestion.value.id]
  if (Array.isArray(answer)) {
    return answer.includes(choiceId)
  }
  return answer === choiceId
}

const selectSingleChoice = (choiceId: string) => {
  const qid = currentQuestion.value.id
  const current = answers.value[qid]

  if (Array.isArray(current) && current.length === 1 && current[0] === choiceId) {
    // Unselect if clicking the same choice
    answers.value[qid] = []
  } else {
    // Select new choice
    answers.value[qid] = [choiceId]
  }
}

const toggleMultiChoice = (choiceId: string) => {
  const qid = currentQuestion.value.id
  const current = answers.value[qid]

  if (!Array.isArray(current)) {
    answers.value[qid] = [choiceId]
  } else {
    const index = current.indexOf(choiceId)
    if (index > -1) {
      current.splice(index, 1)
    } else {
      current.push(choiceId)
    }
  }
}

const selectBoolean = (value: boolean) => {
  answers.value[currentQuestion.value.id] = value
}

const updateFillAnswer = () => {
  answers.value[currentQuestion.value.id] = fillAnswers.value.slice()
}

const updateMatchAnswer = () => {
  answers.value[currentQuestion.value.id] = matchAnswers.value.slice()
}

const moveUp = (idx: number) => {
  if (idx > 0) {
    const temp = orderItems.value[idx]
    orderItems.value[idx] = orderItems.value[idx - 1]
    orderItems.value[idx - 1] = temp
    answers.value[currentQuestion.value.id] = orderItems.value.slice()
  }
}

const moveDown = (idx: number) => {
  if (idx < orderItems.value.length - 1) {
    const temp = orderItems.value[idx]
    orderItems.value[idx] = orderItems.value[idx + 1]
    orderItems.value[idx + 1] = temp
    answers.value[currentQuestion.value.id] = orderItems.value.slice()
  }
}

const isAnswered = (questionId: string): boolean => {
  const answer = answers.value[questionId]
  if (answer === undefined || answer === null) return false
  if (Array.isArray(answer)) return answer.length > 0
  if (typeof answer === 'boolean') return true
  if (typeof answer === 'string') return answer.trim() !== ''
  return false
}

const prevQuestion = () => {
  if (currentIndex.value > 0) {
    currentIndex.value--
    loadQuestionData()
  }
}

const nextQuestion = () => {
  if (currentIndex.value < totalQuestions.value - 1) {
    currentIndex.value++
    loadQuestionData()
  }
}

const goToQuestion = (idx: number) => {
  currentIndex.value = idx
  loadQuestionData()
}

const loadQuestionData = () => {
  const q = currentQuestion.value
  if (q.type === 'fill') {
    fillAnswers.value = answers.value[q.id] || Array(q.blanks || 0).fill('')
  } else if (q.type === 'match') {
    const len = q.pairs?.length || 0
    matchAnswers.value = answers.value[q.id] || Array(len).fill('')
  } else if (q.type === 'order') {
    orderItems.value = answers.value[q.id] || (q.items ? q.items.slice() : [])
  }
}

const submitExam = async () => {
  if (!confirm('Bạn có chắc muốn nộp bài?')) return

  try {
    const result = await examService.submit(examId.value, attemptId.value, answers.value)

    alert(
      `Bạn đã hoàn thành bài thi!\nĐiểm: ${result.totalScore}/${result.maxScore}\nSố câu đúng: ${result.correctCount}/${result.totalCount}`,
    )

    router.push({ name: 'student-exam-result', params: { id: examId.value } })
  } catch (error) {
    console.error('Failed to submit exam:', error)
    alert('Không thể nộp bài. Vui lòng thử lại!')
  }
}

onMounted(() => {
  loadExam()
})

function buildMockAttempt() {
  const baseChoices = (n: number) =>
    Array.from({ length: n }, (_, i) => ({ id: `c${i + 1}`, text: `Phương án ${i + 1}` }))
  const qs = [
    {
      id: 'm1',
      type: 'boolean',
      text: 'Trái đất quay quanh Mặt trời?',
      score: 1,
    },
    {
      id: 'm2',
      type: 'single',
      text: 'Chọn đáp án đúng',
      score: 1,
      choices: baseChoices(4),
    },
    {
      id: 'm3',
      type: 'multi',
      text: 'Chọn tất cả đáp án đúng',
      score: 2,
      choices: baseChoices(5),
    },
    {
      id: 'm4',
      type: 'fill',
      text: 'Điền hai từ còn thiếu',
      score: 2,
      blanks: 2,
    },
    {
      id: 'm5',
      type: 'match',
      text: 'Ghép cặp quốc gia - thủ đô',
      score: 2,
      pairs: [
        { left: 'Việt Nam', right: 'Hà Nội' },
        { left: 'Nhật Bản', right: 'Tokyo' },
      ],
    },
    {
      id: 'm6',
      type: 'order',
      text: 'Sắp xếp các bước',
      score: 2,
      items: ['Bước 1', 'Bước 2', 'Bước 3', 'Bước 4'],
    },
  ]
  return {
    id: 'mock_' + Math.random().toString(36).slice(2, 7),
    title: 'Đề luyện tập (mock)',
    questions: qs,
  }
}
</script>

<style scoped>
.exam-taking-page {
  min-height: 100vh;
  background: #ffffff;
  padding: 2rem 0;
}

.exam-container {
  max-width: 900px;
  margin: 0 auto;
  padding: 0 1.5rem;
}

/* Header */
.exam-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #f3f4f6;
}

.header-left {
  flex: 1;
}

.exam-title {
  font-size: 1.75rem;
  font-weight: 700;
  color: #1a1a1a;
  margin: 0 0 0.25rem 0;
}

.exam-meta {
  font-size: 0.875rem;
  color: #6b7280;
  margin: 0;
}

/* Progress Bar */
.progress-bar {
  height: 6px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
  margin-bottom: 2rem;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #10b981, #059669);
  transition: width 0.3s ease;
}

/* Question Section */
.question-section {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 2rem;
  margin-bottom: 2rem;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.question-number {
  font-size: 0.875rem;
  font-weight: 600;
  color: #10b981;
  padding: 0.375rem 0.75rem;
  background: #f0fdf4;
  border-radius: 0.375rem;
}

.question-score {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6b7280;
}

.question-text {
  font-size: 1.125rem;
  font-weight: 500;
  color: #1a1a1a;
  line-height: 1.6;
  margin-bottom: 1.5rem;
}

/* Choices */
.choices {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.choice-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
}

.choice-item:hover {
  border-color: #10b981;
  background: #f0fdf4;
}

.choice-item.selected {
  border-color: #10b981;
  background: #f0fdf4;
}

.choice-radio,
.choice-checkbox {
  width: 20px;
  height: 20px;
  border: 2px solid #d1d5db;
  flex-shrink: 0;
  transition: all 0.2s;
}

.choice-radio {
  border-radius: 50%;
}

.choice-checkbox {
  border-radius: 0.25rem;
}

.choice-item.selected .choice-radio,
.choice-item.selected .choice-checkbox {
  border-color: #10b981;
  background: #10b981;
}

.choice-text {
  flex: 1;
  font-size: 1rem;
  color: #374151;
}

/* Boolean */
.boolean-choices {
  display: flex;
  gap: 1rem;
}

.boolean-btn {
  flex: 1;
  padding: 1rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  background: white;
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
  transition: all 0.2s;
}

.boolean-btn:hover {
  border-color: #10b981;
  background: #f0fdf4;
}

.boolean-btn.selected {
  border-color: #10b981;
  background: #10b981;
  color: white;
}

/* Fill */
.fill-inputs {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.fill-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.fill-item label {
  font-size: 0.875rem;
  font-weight: 600;
  color: #374151;
}

.fill-item input {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1rem;
  transition: border-color 0.2s;
}

.fill-item input:focus {
  outline: none;
  border-color: #10b981;
}

/* Match */
.match-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.match-item {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1rem;
  align-items: center;
}

.match-left {
  padding: 0.75rem;
  background: #f3f4f6;
  border-radius: 0.5rem;
  font-weight: 500;
}

.match-select {
  padding: 0.75rem;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-size: 1rem;
  cursor: pointer;
}

.match-select:focus {
  outline: none;
  border-color: #10b981;
}

/* Order */
.order-section {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.order-item {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding: 0.75rem;
  background: #f3f4f6;
  border-radius: 0.5rem;
}

.order-number {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #10b981;
  color: white;
  border-radius: 50%;
  font-weight: 600;
  font-size: 0.875rem;
}

.order-text {
  flex: 1;
  font-weight: 500;
}

.order-controls {
  display: flex;
  gap: 0.5rem;
}

.order-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.order-btn:hover:not(:disabled) {
  background: #10b981;
  border-color: #10b981;
  color: white;
}

.order-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Navigation */
.navigation {
  display: flex;
  justify-content: space-between;
  margin-bottom: 2rem;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: white;
  border: 2px solid #10b981;
  border-radius: 0.5rem;
  color: #10b981;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn svg {
  width: 20px;
  height: 20px;
}

.nav-btn:hover:not(:disabled) {
  background: #10b981;
  color: white;
}

.nav-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* Question Map */
.question-map {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 2rem;
}

.map-title {
  font-size: 1rem;
  font-weight: 600;
  color: #374151;
  margin-bottom: 1rem;
}

.map-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(48px, 1fr));
  gap: 0.5rem;
}

.map-item {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: white;
  border: 2px solid #e5e7eb;
  border-radius: 0.5rem;
  font-weight: 600;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
}

.map-item:hover {
  border-color: #10b981;
}

.map-item.current {
  border-color: #10b981;
  background: #10b981;
  color: white;
}

.map-item.answered {
  border-color: #10b981;
  color: #10b981;
}

.map-item.answered.current {
  background: #10b981;
  color: white;
}

/* Submit */
.submit-section {
  text-align: center;
}

.submit-btn {
  padding: 1rem 3rem;
  background: #10b981;
  border: none;
  border-radius: 0.5rem;
  color: white;
  font-size: 1.125rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
}

.submit-btn:hover {
  background: #059669;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
}

/* Responsive */
@media (max-width: 768px) {
  .exam-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .match-item {
    grid-template-columns: 1fr;
  }

  .navigation {
    flex-direction: column;
    gap: 0.75rem;
  }

  .nav-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
