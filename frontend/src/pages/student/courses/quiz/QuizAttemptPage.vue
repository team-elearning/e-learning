<template>
  <div class="quiz-page">
    <div class="topbar">
      <div class="left">
        <button class="btn ghost" @click="goBack">← Quay lại</button>
        <div class="title">
          <div class="h">{{ quizTitle || 'Bài kiểm tra' }}</div>
          <div class="sub">
            Câu {{ currentIndex + 1 }}/{{ questionsOrder.length }}
            <span v-if="saving" class="dot">•</span>
            <span v-if="saving">Đang lưu…</span>
            <span v-else-if="savedAt">• Đã lưu</span>
          </div>
        </div>
      </div>

      <div class="right">
        <div class="timer" v-if="timeLimitSeconds">⏱ {{ timeLeftDisplay }}</div>
        <button class="btn danger" @click="finishQuiz" :disabled="finishing || !attemptId">
          <span v-if="finishing">Đang nộp…</span>
          <span v-else>Nộp bài</span>
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">
      <div class="card">Đang chuẩn bị bài làm…</div>
    </div>

    <div v-else class="content">
      <!-- Pagination -->
      <div class="nav">
        <button
          v-for="(qid, idx) in questionsOrder"
          :key="qid"
          class="pill"
          :class="{ active: idx === currentIndex, done: answeredSet.has(String(qid)) }"
          @click="goToIndex(idx)"
        >
          {{ idx + 1 }}
        </button>
      </div>

      <!-- Question -->
      <div class="card" v-if="question">
        <div class="qhead">
          <div class="qtype">{{ question.question_type }}</div>
        </div>

        <div
          class="prompt"
          v-html="safeHtml(question.prompt || question.prompt_text || question.promptHtml || '')"
        ></div>

        <!-- MULTIPLE CHOICE SINGLE -->
        <div v-if="qType === 'multiple_choice_single'" class="options">
          <label
            v-for="op in question.options || []"
            :key="op.id"
            class="opt"
            :class="{ selected: selectedId === op.id, locked: isLocked }"
          >
            <input
              type="radio"
              :name="'q-' + question.id"
              :value="op.id"
              v-model="selectedId"
              :disabled="isLocked"
              @change="onAnswerChanged"
            />
            <span class="txt" v-html="safeHtml(op.text)"></span>
          </label>
        </div>

        <!-- MULTIPLE CHOICE MULTI -->
        <div v-else-if="qType === 'multiple_choice_multi'" class="options">
          <label
            v-for="op in question.options || []"
            :key="op.id"
            class="opt"
            :class="{ selected: selectedIds.includes(op.id), locked: isLocked }"
          >
            <input
              type="checkbox"
              :value="op.id"
              v-model="selectedIds"
              :disabled="isLocked"
              @change="onAnswerChanged"
            />
            <span class="txt" v-html="safeHtml(op.text)"></span>
          </label>
        </div>

        <!-- TRUE / FALSE -->
        <div v-else-if="qType === 'true_false'" class="options">
          <label class="opt" :class="{ selected: selectedId === 'true', locked: isLocked }">
            <input
              type="radio"
              :name="'q-' + question.id"
              value="true"
              v-model="selectedId"
              :disabled="isLocked"
              @change="onAnswerChanged"
            />
            Đúng
          </label>

          <label class="opt" :class="{ selected: selectedId === 'false', locked: isLocked }">
            <input
              type="radio"
              :name="'q-' + question.id"
              value="false"
              v-model="selectedId"
              :disabled="isLocked"
              @change="onAnswerChanged"
            />
            Sai
          </label>
        </div>

        <!-- SHORT ANSWER -->
        <div v-else-if="qType === 'short_answer'" class="text">
          <textarea
            v-model="textAnswer"
            :disabled="isLocked"
            placeholder="Nhập câu trả lời…"
            @input="onTextInput"
          />
        </div>

        <!-- FALLBACK -->
        <div v-else class="muted">
          Chưa hỗ trợ UI cho loại câu hỏi:
          <b>{{ qType }}</b>
        </div>

        <!-- Actions -->
        <div class="actions">
          <button class="btn" @click="prev" :disabled="currentIndex === 0">← Câu trước</button>
          <button class="btn" @click="next" :disabled="currentIndex >= questionsOrder.length - 1">
            Câu tiếp →
          </button>
        </div>
      </div>

      <div v-else class="card">Không tải được câu hỏi.</div>
    </div>
    <!-- RESULT POPUP -->
    <div v-if="showResultPopup" class="result-overlay">
      <div class="result-modal">
        <h2>Kết quả bài làm</h2>

        <div class="summary">
          <div>
            <b>Điểm:</b>
            {{ resultData?.score }} / {{ resultData?.max_score }}
          </div>
          <div>
            <b>Tỷ lệ:</b>
            {{ Math.round(resultData?.percentage || 0) }}%
          </div>
          <div>
            <b>Kết quả:</b>
            <span :class="resultData?.is_passed ? 'pass' : 'fail'">
              {{ resultData?.is_passed ? 'Đạt' : 'Chưa đạt' }}
            </span>
          </div>
        </div>

        <hr />

        <div class="details">
          <div
            v-for="(item, idx) in resultData?.items || []"
            :key="item.question_id"
            class="result-item"
          >
            <div class="q-title">Câu {{ idx + 1 }}: {{ item.question_text }}</div>

            <div class="q-score">Điểm: {{ item.score }} / {{ item.max_score }}</div>

            <div class="q-feedback" :class="item.is_correct ? 'correct' : 'incorrect'">
              {{ item.feedback }}
            </div>
          </div>
        </div>

        <div class="actions">
          <button class="btn" @click="showResultPopup = false">Đóng</button>
          <button class="btn primary" @click="goBack">Quay lại khóa học</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/config/axios'

/**
 * Route khuyến nghị:
 * /student/quiz?block_id=...&course_id=...
 * hoặc /quiz?quiz_id=...&course_id=...
 *
 * Flow chuẩn:
 * 1) Nếu có block_id => GET /content/blocks/{block_id}/ lấy quiz_id
 * 2) GET /quizzes/{quiz_id}/attempt/?course_id=...
 * 3) Load câu: GET /attempts/{attempt_id}/questions/{question_id}/
 * 4) Draft: PUT /attempts/{attempt_id}/questions/{question_id}/draft/
 * 5) Finish: POST /attempts/{attempt_id}/finish/
 */

const route = useRoute()
const router = useRouter()

// ---------- UI state ----------
const loading = ref(true)
const finishing = ref(false)
const saving = ref(false)
const savedAt = ref<number | null>(null)

// ---------- attempt state ----------
const quizId = ref<string | null>(null)
const quizTitle = ref<string>('')
const attemptId = ref<string | null>(null)
const questionsOrder = ref<string[]>([])
const currentIndex = ref<number>(0)

// cache question responses (optional)
const qCache = new Map<string, any>()
const answeredSet = ref(new Set<string>())

// ---------- question state ----------
const question = ref<any>(null)

// local answer state (tùy type)
const selectedId = ref<string | null>(null)
const selectedIds = ref<string[]>([])
const textAnswer = ref<string>('')

// server lock state (đã chấm / đã submit từng câu)
const isLocked = computed(() => Boolean(question.value?.submission_result))

// ---------- Timer ----------
const timeLimitSeconds = ref<number | null>(null)
const timeStart = ref<number | null>(null) // ms
const timeLeft = ref<number | null>(null) // seconds

const timeLeftDisplay = computed(() => {
  const t = timeLeft.value ?? 0
  const mm = String(Math.floor(t / 60)).padStart(2, '0')
  const ss = String(t % 60).padStart(2, '0')
  return `${mm}:${ss}`
})

const showResultPopup = ref(false)
const resultData = ref<any>(null)

let timerHandle: any = null

function startTimer() {
  if (!timeLimitSeconds.value || !timeStart.value) return
  if (timerHandle) clearInterval(timerHandle)

  const tick = () => {
    const elapsed = Math.floor((Date.now() - timeStart.value!) / 1000)
    const left = Math.max(0, timeLimitSeconds.value! - elapsed)
    timeLeft.value = left
    if (left <= 0) {
      clearInterval(timerHandle)
      timerHandle = null
      // auto-submit
      finishQuiz()
    }
  }

  tick()
  timerHandle = setInterval(tick, 1000)
}

// ---------- utils ----------
function safeHtml(html: string) {
  // Demo nhanh: nếu backend đã sanitize thì dùng v-html ok.
  // Production: dùng DOMPurify.
  return html
}

function debounce<T extends (...args: any[]) => void>(fn: T, wait = 600) {
  let t: any = null
  return (...args: Parameters<T>) => {
    clearTimeout(t)
    t = setTimeout(() => fn(...args), wait)
  }
}

// ---------- API ----------
async function getBlockDetail(blockId: string) {
  const { data } = await api.get(`/content/blocks/${blockId}/`)
  return data
}

async function startOrResumeAttempt(quiz_id: string, course_id?: string) {
  const qs = course_id ? `?course_id=${encodeURIComponent(course_id)}` : ''
  const { data } = await api.get(`/progress/quizzes/${quiz_id}/attempt/`)
  return data
}

async function getQuestion(attempt_id: string, question_id: string) {
  const cacheKey = `${attempt_id}:${question_id}`
  if (qCache.has(cacheKey)) return qCache.get(cacheKey)
  const { data } = await api.get(`/progress/attempts/${attempt_id}/questions/${question_id}/`)
  qCache.set(cacheKey, data)
  return data
}

async function draftAnswer(attempt_id: string, question_id: string, answer_data: any) {
  await api.put(`/progress/attempts/${attempt_id}/questions/${question_id}/draft/`, { answer_data })
}

async function finishAttempt(attempt_id: string) {
  const { data } = await api.post(`/progress/quizzes/attempts/${attempt_id}/finish/`, {})
  return data
}

// ---------- type helpers ----------
const qType = computed(() => {
  const q = question.value || {}
  return String(q.question_type || q.type || q.questionType || '').trim()
})
const isSingleChoice = computed(
  () => qType.value === 'multiple_choice_single' || qType.value === 'true_false',
)
const isMultiChoice = computed(() => qType.value === 'multiple_choice_multi')
const isText = computed(() => ['short_answer', 'fill_in_the_blank', 'essay'].includes(qType.value))

// ---------- load question + hydrate current_answer ----------
async function loadQuestionByIndex(idx: number) {
  if (!attemptId.value) return
  const qid = questionsOrder.value[idx]
  if (!qid) return

  const data = await getQuestion(attemptId.value, qid)
  question.value = data
  console.log('QUESTION RAW:', data)
  console.log('qType:', qType.value, 'question_type:', data?.question_type, 'type:', data?.type)

  // hydrate answer from current_answer (resume)
  const curAns = data?.current_answer?.answer_data || data?.current_answer || null
  selectedId.value = null
  selectedIds.value = []
  textAnswer.value = ''

  if (curAns) {
    if (curAns.selected_id) selectedId.value = curAns.selected_id
    if (Array.isArray(curAns.selected_ids)) selectedIds.value = [...curAns.selected_ids]
    if (typeof curAns.text === 'string') textAnswer.value = curAns.text
  }

  // mark answered if has draft data
  if (curAns && (curAns.selected_id || curAns.selected_ids?.length || curAns.text?.trim?.())) {
    answeredSet.value.add(String(qid))
  }
}

// ---------- autosave handlers ----------
const doDraft = debounce(async () => {
  if (!attemptId.value || !question.value) return
  if (isLocked.value) return

  const qid = String(question.value.id)

  let answer_data: any = {}
  if (isSingleChoice.value) answer_data = { selected_id: selectedId.value }
  else if (isMultiChoice.value) answer_data = { selected_ids: selectedIds.value }
  else if (isText.value) answer_data = { text: (textAnswer.value || '').trim() }

  saving.value = true
  try {
    await draftAnswer(attemptId.value, qid, answer_data)
    savedAt.value = Date.now()

    // mark answered (nếu có dữ liệu)
    const has =
      (answer_data.selected_id && String(answer_data.selected_id).length > 0) ||
      (Array.isArray(answer_data.selected_ids) && answer_data.selected_ids.length > 0) ||
      (typeof answer_data.text === 'string' && answer_data.text.length > 0)

    if (has) answeredSet.value.add(qid)
  } finally {
    saving.value = false
  }
}, 700)

function onAnswerChanged() {
  doDraft()
}

function onTextInput() {
  doDraft()
}

// ---------- navigation ----------
function goToIndex(idx: number) {
  if (idx < 0 || idx >= questionsOrder.value.length) return
  currentIndex.value = idx
}

function prev() {
  goToIndex(currentIndex.value - 1)
}
function next() {
  goToIndex(currentIndex.value + 1)
}

function goBack() {
  router.back()
}

// ---------- finish ----------
async function finishQuiz() {
  if (!attemptId.value || finishing.value) return
  finishing.value = true

  try {
    const res = await finishAttempt(attemptId.value)

    // lưu dữ liệu kết quả
    resultData.value = res
    showResultPopup.value = true
  } catch (e: any) {
    alert('Nộp bài thất bại. Thử lại nhé.')
  } finally {
    finishing.value = false
  }
}

// ---------- init ----------
onMounted(async () => {
  loading.value = true
  try {
    const courseId = (route.query.course_id as string) || undefined
    const blockId = (route.query.block_id as string) || undefined
    const directQuizId = (route.query.quiz_id as string) || undefined

    // 1) Resolve quiz_id
    if (directQuizId) {
      quizId.value = directQuizId
    } else if (blockId) {
      const block = await getBlockDetail(blockId)
      quizId.value = block?.payload?.quiz_id || block?.payload?.quizId || null
      quizTitle.value = block?.title || block?.payload?.title || 'Bài kiểm tra'
    }

    if (!quizId.value) throw new Error('NO_QUIZ_ID')

    // 2) Start/Resume attempt
    const attempt = await startOrResumeAttempt(quizId.value, courseId)
    attemptId.value = attempt?.attempt_id || attempt?.id || null
    questionsOrder.value = attempt?.questions_order || []
    timeLimitSeconds.value = attempt?.time_limit_seconds || null

    // time_start có thể là ISO string
    if (attempt?.time_start) {
      const ts = new Date(attempt.time_start).getTime()
      timeStart.value = Number.isFinite(ts) ? ts : Date.now()
    } else {
      timeStart.value = Date.now()
    }

    if (!attemptId.value) {
      throw new Error('NO_ATTEMPT_ID')
    }

    if (!Array.isArray(questionsOrder.value)) {
      throw new Error('INVALID_QUESTIONS_ORDER')
    }

    // 3) Load first question
    currentIndex.value = 0
    await loadQuestionByIndex(0)

    // 4) Start timer
    startTimer()
  } catch (e: any) {
    console.error(e)
    alert('Không thể mở bài kiểm tra.')
    router.back()
  } finally {
    loading.value = false
  }
})

// when index changes -> load question
watch(currentIndex, async (idx) => {
  if (!attemptId.value) return
  await loadQuestionByIndex(idx)
})
</script>

<style scoped>
.quiz-page {
  min-height: 100vh;
  background: #0b1220;
  color: #e5e7eb;
  padding: 14px;
}
.topbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  max-width: 1100px;
  margin: 0 auto 12px auto;
  padding: 12px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  background: rgba(0, 0, 0, 0.35);
}
.left {
  display: flex;
  align-items: center;
  gap: 10px;
}
.title .h {
  font-weight: 900;
  font-size: 16px;
}
.title .sub {
  opacity: 0.85;
  font-size: 13px;
}
.right {
  display: flex;
  align-items: center;
  gap: 10px;
}
.timer {
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.08);
  font-weight: 900;
}
.dot {
  margin: 0 6px;
}

.content {
  max-width: 1100px;
  margin: 0 auto;
}
.loading {
  max-width: 1100px;
  margin: 0 auto;
  display: grid;
  place-items: center;
  min-height: 50vh;
}
.card {
  background: #ffffff;
  color: #0f172a;
  border-radius: 14px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.nav {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}
.pill {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  font-weight: 900;
}
.pill.active {
  outline: 2px solid #16a34a;
}
.pill.done {
  background: #e8f2ff;
}

.qhead {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}
.qtype {
  font-weight: 900;
  font-size: 12px;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  padding: 4px 10px;
  border-radius: 999px;
}
.prompt {
  font-size: 15px;
  line-height: 1.6;
  margin-bottom: 12px;
}

.options {
  display: grid;
  gap: 10px;
}
.opt {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  background: #fff;
}
.opt.selected {
  border-color: #0ea5e9;
  background: #f0f9ff;
}
.opt.locked {
  opacity: 0.75;
  cursor: not-allowed;
}
.opt input {
  margin-top: 3px;
}
.txt {
  line-height: 1.5;
}

.text textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  resize: vertical;
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 14px;
}

.btn {
  padding: 10px 14px;
  border-radius: 12px;
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #0f172a;
  font-weight: 900;
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn.ghost {
  background: transparent;
  border-color: rgba(255, 255, 255, 0.25);
  color: #e5e7eb;
}
.btn.danger {
  background: #ef4444;
  border-color: #ef4444;
  color: #fff;
}
.muted {
  color: #64748b;
}
.result-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}
.result-modal {
  background: #ffffff;
  width: 520px;
  max-height: 80vh;
  overflow-y: auto;
  border-radius: 12px;
  padding: 24px;
  color: #1f2937; /* xám đậm */
}

.result-modal h2 {
  font-size: 20px;
  font-weight: 700;
  margin-bottom: 12px;
}

.summary div {
  margin-bottom: 6px;
  color: #374151; /* xám vừa */
}

.pass {
  color: #16a34a; /* xanh dịu */
  font-weight: 600;
}

.fail {
  color: #dc2626; /* đỏ nhưng không gắt */
  font-weight: 600;
}

.result-item {
  margin-bottom: 14px;
  padding: 10px 0;
  border-bottom: 1px solid #e5e7eb;
}

.q-title {
  font-weight: 600;
  color: #111827;
  margin-bottom: 4px;
}

.q-score {
  font-size: 13px;
  color: #6b7280;
}

.q-feedback {
  margin-top: 4px;
  font-size: 14px;
}

.q-feedback.correct {
  color: #15803d; /* xanh đậm */
}

.q-feedback.incorrect {
  color: #b91c1c; /* đỏ trầm */
}

.actions {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
}
</style>
