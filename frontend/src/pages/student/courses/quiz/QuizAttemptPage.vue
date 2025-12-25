<template>
  <div class="quiz-shell">
    <!-- ===== Top bar ===== -->
    <header class="topbar">
      <div class="topbar-left">
        <button class="icon-btn" @click="goBack" title="Quay lại">←</button>

        <div class="topbar-title">
          <div class="title">{{ quizTitle || 'Bài kiểm tra' }}</div>
          <div class="sub">
            Câu <b>{{ index + 1 }}</b> / <b>{{ questionsOrder.length }}</b>
            <span class="dot" v-if="saving">•</span>
            <span v-if="saving" class="muted">Đang lưu…</span>
            <span v-else-if="savedAt" class="muted">• Đã lưu</span>
          </div>
        </div>
      </div>

      <div class="topbar-right">
        <div v-if="timeLimitSeconds" class="pill timer">⏱ {{ timeLeftDisplay }}</div>

        <button class="btn danger" @click="openSubmitConfirm" :disabled="finishing || !attemptId">
          {{ finishing ? 'Đang nộp…' : 'Nộp bài' }}
        </button>
      </div>
    </header>

    <!-- ===== Layout ===== -->
    <div class="layout">
      <!-- Sidebar -->
      <aside class="sidebar">
        <div class="sidebar-card">
          <div class="sidebar-head">
            <div class="sidebar-title">Danh sách câu</div>
            <div class="sidebar-sub">{{ answeredSet.size }}/{{ questionsOrder.length }} đã làm</div>
          </div>

          <div class="grid">
            <button
              v-for="(qid, i) in questionsOrder"
              :key="qid"
              class="qdot"
              :class="{ active: i === index, done: answeredSet.has(String(qid)) }"
              @click="goTo(i)"
              :title="`Câu ${i + 1}`"
            >
              {{ i + 1 }}
            </button>
          </div>

          <div class="sidebar-note">
            <div class="legend">
              <span class="legend-dot done"></span>
              <span>Đã trả lời</span>
            </div>
            <div class="legend">
              <span class="legend-dot active"></span>
              <span>Đang làm</span>
            </div>
          </div>
        </div>
      </aside>

      <!-- Main -->
      <main class="main">
        <!-- Loading -->
        <div v-if="pageLoading" class="card skeleton">
          <div class="sk-line w40"></div>
          <div class="sk-line w80"></div>
          <div class="sk-line w70"></div>
          <div class="sk-line w90"></div>
        </div>

        <!-- Question -->
        <div v-else class="card">
          <div class="qhead">
            <span class="badge">{{ typeToVI(q?.type) }}</span>
            <span v-if="q?.isLocked" class="lock">🔒 Đã khóa</span>
          </div>

          <div class="qcontent" v-html="safeHtml(q?.content || '')"></div>

          <!-- Media (nếu có) -->
          <div v-if="q?.media?.length" class="media">
            <div v-for="(m, mi) in q.media" :key="mi" class="media-item">
              <img v-if="m.type === 'image' && m.url" :src="m.url" :alt="m.caption || 'image'" />
              <div v-if="m.caption" class="media-cap">{{ m.caption }}</div>
            </div>
          </div>

          <!-- ===== Answers ===== -->
          <!-- Single + True/False -->
          <div v-if="q && isSingleType(q.type)" class="answers">
            <label
              v-for="op in q.options"
              :key="op.id"
              class="ans"
              :class="{ selected: selectedId === op.id, disabled: q.isLocked }"
            >
              <input
                type="radio"
                :name="'q-' + q.id"
                :value="op.id"
                v-model="selectedId"
                :disabled="q.isLocked"
                @change="onChanged"
              />
              <span class="ans-text" v-html="safeHtml(op.text)"></span>
            </label>
          </div>

          <!-- Multi -->
          <div v-else-if="q && q.type === 'multiple_choice_multi'" class="answers">
            <label
              v-for="op in q.options"
              :key="op.id"
              class="ans"
              :class="{ selected: selectedIds.includes(op.id), disabled: q.isLocked }"
            >
              <input
                type="checkbox"
                :value="op.id"
                v-model="selectedIds"
                :disabled="q.isLocked"
                @change="onChanged"
              />
              <span class="ans-text" v-html="safeHtml(op.text)"></span>
            </label>
          </div>

          <!-- Text -->
          <div v-else-if="q" class="text-area">
            <textarea
              v-model="textAnswer"
              :disabled="q.isLocked"
              placeholder="Nhập câu trả lời…"
              @input="onTextInput"
            />
            <div class="hint">Hệ thống sẽ tự lưu sau khi bạn dừng gõ ~0.8s.</div>
          </div>

          <!-- Footer nav -->
          <div class="qnav">
            <button class="btn ghost" @click="goPrev" :disabled="index === 0 || navBusy">
              ← Trước
            </button>

            <div class="qnav-mid">
              <span v-if="navBusy" class="muted">Đang tải…</span>
              <span v-else class="muted">Bạn có thể chuyển câu, dữ liệu sẽ được lưu tự động.</span>
            </div>

            <button
              class="btn primary"
              @click="goNext"
              :disabled="isLast || navBusy"
              title="Ở câu cuối sẽ tự mở xác nhận nộp"
            >
              Sau →
            </button>
          </div>

          <!-- Last hint -->
          <div v-if="isLast" class="last-tip">
            Bạn đang ở câu cuối. Hãy bấm <b>Nộp bài</b> để kết thúc.
          </div>
        </div>
      </main>
    </div>

    <!-- ===== Confirm submit modal ===== -->
    <div v-if="showConfirmSubmit" class="overlay" @click.self="closeSubmitConfirm">
      <div class="modal">
        <div class="modal-title">Xác nhận nộp bài</div>
        <div class="modal-desc">
          Bạn đã làm <b>{{ answeredSet.size }}</b> / <b>{{ questionsOrder.length }}</b> câu.
          <br />
          Sau khi nộp, bạn sẽ <b>không sửa được</b> nữa.
        </div>

        <div class="modal-actions">
          <button class="btn ghost" @click="closeSubmitConfirm" :disabled="finishing">Hủy</button>
          <button class="btn danger" @click="confirmSubmit" :disabled="finishing">
            {{ finishing ? 'Đang nộp…' : 'Xác nhận nộp' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ===== Result popup ===== -->
    <div v-if="showResultPopup" class="overlay" @click.self="showResultPopup = false">
      <div class="modal big">
        <div class="modal-title">Kết quả bài làm</div>

        <div class="result-summary">
          <div class="sum-card">
            <div class="sum-label">Điểm</div>
            <div class="sum-value">{{ submitResult?.score }} / {{ submitResult?.max_score }}</div>
          </div>
          <div class="sum-card">
            <div class="sum-label">Tỷ lệ</div>
            <div class="sum-value">{{ Math.round(submitResult?.percentage || 0) }}%</div>
          </div>
          <div class="sum-card">
            <div class="sum-label">Kết quả</div>
            <div class="sum-value" :class="submitResult?.is_passed ? 'ok' : 'bad'">
              {{ submitResult?.is_passed ? 'Đạt' : 'Chưa đạt' }}
            </div>
          </div>
          <div class="sum-card" v-if="submitResult?.time_taken_seconds != null">
            <div class="sum-label">Thời gian</div>
            <div class="sum-value">{{ submitResult?.time_taken_seconds }}s</div>
          </div>
        </div>

        <div class="result-list">
          <div
            v-for="(it, i) in submitResult?.items || []"
            :key="it.question_id"
            class="result-item"
          >
            <div class="ri-top">
              <div class="ri-title">
                Câu {{ i + 1 }}: <span v-html="safeHtml(it.question_text)"></span>
              </div>
              <div class="ri-pill" :class="it.is_correct ? 'ok' : 'bad'">
                {{ it.is_correct ? 'Đúng' : 'Sai' }}
              </div>
            </div>

            <div class="ri-meta">Loại: {{ typeToVI(it.question_type) }}</div>

            <div class="ri-row">
              <b>Bạn trả lời:</b>
              <span>{{ formatUserAnswer(it) }}</span>
            </div>

            <div class="ri-row">
              <b>Đáp án đúng:</b>
              <span>{{ formatCorrectAnswer(it) }}</span>
            </div>

            <div class="ri-foot" :class="it.is_correct ? 'ok' : 'bad'">
              {{ it.feedback }} • {{ it.score }} / {{ it.max_score }} điểm
            </div>
          </div>
        </div>

        <div class="modal-actions">
          <button class="btn ghost" @click="showResultPopup = false">Đóng</button>
          <button class="btn primary" @click="goBack">Về khóa học</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/config/axios'

/** ===== Types (nhẹ) ===== */
type QType =
  | 'multiple_choice_single'
  | 'multiple_choice_multi'
  | 'true_false'
  | 'short_answer'
  | 'fill_in_the_blank'
  | 'essay'
  | 'matching'
  | 'ordering'
  | 'numeric'
  | string

type Option = { id: string; text: string }
type Media = { type: string; url?: string; file_path?: string; caption?: string }

type NormalizedQuestion = {
  id: string
  type: QType
  content: string
  options: Option[]
  media: Media[]
  isLocked: boolean
  currentAnswer: { selected_id: string | null; selected_ids: string[]; text: string }
}

/** ===== Router ===== */
const route = useRoute()
const router = useRouter()

/** ===== State ===== */
const pageLoading = ref(true)
const navBusy = ref(false)
const saving = ref(false)
const savedAt = ref<number | null>(null)
const finishing = ref(false)

const quizTitle = ref('')
const quizId = ref<string | null>(null)
const attemptId = ref<string | null>(null)
const questionsOrder = ref<string[]>([])
const index = ref(0)

const q = ref<NormalizedQuestion | null>(null)

/** ===== Answer state ===== */
const selectedId = ref<string | null>(null)
const selectedIds = ref<string[]>([])
const textAnswer = ref('')

/** ===== Progress ===== */
const answeredSet = ref(new Set<string>())

/** ===== Modals ===== */
const showConfirmSubmit = ref(false)
const showResultPopup = ref(false)
const submitResult = ref<any>(null)

/** ===== Timer (optional) ===== */
const timeLimitSeconds = ref<number | null>(null)
const timeStart = ref<number | null>(null)
const timeLeft = ref<number | null>(null)
let timerHandle: any = null

const timeLeftDisplay = computed(() => {
  const t = Math.max(0, timeLeft.value ?? 0)
  const mm = String(Math.floor(t / 60)).padStart(2, '0')
  const ss = String(t % 60).padStart(2, '0')
  return `${mm}:${ss}`
})

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
      openSubmitConfirm()
    }
  }
  tick()
  timerHandle = setInterval(tick, 1000)
}

/** ===== Helpers ===== */
const QUESTION_TYPE_VI: Record<string, string> = {
  multiple_choice_single: 'Chọn 1 đáp án',
  multiple_choice_multi: 'Chọn nhiều đáp án',
  true_false: 'Đúng / Sai',
  short_answer: 'Điền câu trả lời',
  fill_in_the_blank: 'Điền từ',
  essay: 'Tự luận',
  matching: 'Nối cặp',
  ordering: 'Sắp xếp',
  numeric: 'Số học',
}
function typeToVI(t?: string) {
  const key = String(t || '').trim()
  return QUESTION_TYPE_VI[key] || key || '—'
}
function isSingleType(t?: string) {
  return t === 'multiple_choice_single' || t === 'true_false'
}
function safeHtml(html: string) {
  // Nếu backend đã sanitize ok thì dùng v-html được.
  // Production: dùng DOMPurify.
  return html
}

const isLast = computed(() => index.value >= questionsOrder.value.length - 1)

/** ===== Cache ===== */
const questionCache = new Map<string, NormalizedQuestion>()

/** ===== API calls ===== */
async function getBlockDetail(blockId: string) {
  const { data } = await api.get(`/content/blocks/${blockId}/`)
  return data
}

async function startOrResumeAttempt(quiz_id: string, course_id?: string) {
  // nếu backend đang ignore course_id thì thôi, còn nếu cần thì append query
  const qs = course_id ? `?course_id=${encodeURIComponent(course_id)}` : ''
  const { data } = await api.get(`/progress/quizzes/${quiz_id}/attempt/${qs}`)
  return data
}

async function fetchQuestion(attempt_id: string, question_id: string) {
  const { data } = await api.get(`/progress/attempts/${attempt_id}/questions/${question_id}/`)
  return data
}

async function putDraft(attempt_id: string, question_id: string, payload: any) {
  await api.put(`/progress/attempts/${attempt_id}/questions/${question_id}/draft/`, payload)
}

async function finishAttempt(attempt_id: string) {
  const { data } = await api.post(`/progress/quizzes/attempts/${attempt_id}/finish/`, {})
  return data
}

/** ===== Normalize (chịu được các response prompt: text/content/options/media) ===== */
function normalizeQuestion(raw: any): NormalizedQuestion {
  const type: QType = raw?.type ?? raw?.question_type ?? ''

  const prompt = raw?.prompt ?? {}
  const content = String(prompt?.content ?? prompt?.text ?? raw?.prompt_text ?? '').trim()

  let options: Option[] = []
  if (type === 'multiple_choice_single' || type === 'multiple_choice_multi') {
    options = Array.isArray(prompt?.options) ? prompt.options : []
  }
  if (type === 'true_false') {
    options = [
      { id: 'true', text: 'Đúng' },
      { id: 'false', text: 'Sai' },
    ]
  }

  const media: Media[] = Array.isArray(prompt?.media) ? prompt.media : []

  // current_answer có thể: {} hoặc {answer_data:{...}} hoặc trực tiếp {selected_id/text...}
  const ca = raw?.current_answer ?? {}
  const answer_data = ca?.answer_data ?? ca ?? {}

  return {
    id: String(raw?.id ?? ''),
    type,
    content,
    options,
    media,
    isLocked: Boolean(raw?.submission_result),
    currentAnswer: {
      selected_id: answer_data?.selected_id ?? null,
      selected_ids: Array.isArray(answer_data?.selected_ids) ? answer_data.selected_ids : [],
      text: typeof answer_data?.text === 'string' ? answer_data.text : '',
    },
  }
}

/** ===== Hydrate UI from question ===== */
function hydrateFromQuestion(nq: NormalizedQuestion) {
  selectedId.value = nq.currentAnswer.selected_id
  selectedIds.value = [...nq.currentAnswer.selected_ids]
  textAnswer.value = nq.currentAnswer.text

  // đánh dấu answeredSet
  const has =
    (selectedId.value && String(selectedId.value).length > 0) ||
    (selectedIds.value && selectedIds.value.length > 0) ||
    (textAnswer.value && textAnswer.value.trim().length > 0)
  if (has) answeredSet.value.add(String(nq.id))
}

/** ===== Load question with cache ===== */
async function loadQuestionByIndex(i: number) {
  if (!attemptId.value) return
  const qid = questionsOrder.value[i]
  if (!qid) return

  navBusy.value = true
  try {
    // Cache hit
    if (questionCache.has(qid)) {
      q.value = questionCache.get(qid)!
      hydrateFromQuestion(q.value)
      // prefetch sau khi hiển thị
      prefetchNext(i)
      return
    }

    // Fetch
    const raw = await fetchQuestion(attemptId.value, qid)
    const nq = normalizeQuestion(raw)
    questionCache.set(qid, nq)
    q.value = nq
    hydrateFromQuestion(nq)

    prefetchNext(i)
  } finally {
    navBusy.value = false
  }
}

function prefetchNext(i: number) {
  if (!attemptId.value) return
  const nextIndex = i + 1
  if (nextIndex >= questionsOrder.value.length) return
  const nextQid = questionsOrder.value[nextIndex]
  if (!nextQid || questionCache.has(nextQid)) return

  fetchQuestion(attemptId.value, nextQid)
    .then((raw: any) => {
      questionCache.set(nextQid, normalizeQuestion(raw))
    })
    .catch(() => {
      // ignore prefetch errors
    })
}

/** ===== Build answer_data ===== */
function buildAnswerData() {
  if (!q.value) return {}

  if (q.value.type === 'multiple_choice_single' || q.value.type === 'true_false') {
    return { selected_id: selectedId.value }
  }
  if (q.value.type === 'multiple_choice_multi') {
    return { selected_ids: selectedIds.value }
  }
  return { text: (textAnswer.value || '').trim() }
}

/** ===== Save draft (queue-friendly) ===== */
const saveDraftDebounced = debounce(async () => {
  await saveDraftInternal()
}, 800)

async function saveDraftInternal() {
  if (!attemptId.value || !q.value) return
  if (q.value.isLocked) return

  const answer_data = buildAnswerData()

  // has?
  const has =
    (answer_data as any).selected_id ||
    ((answer_data as any).selected_ids && (answer_data as any).selected_ids.length > 0) ||
    ((answer_data as any).text && String((answer_data as any).text).length > 0)

  // nếu rỗng thì không lưu
  if (!has) return

  saving.value = true
  try {
    await putDraft(attemptId.value, q.value.id, {
      question_type: q.value.type,
      answer_data,
    })

    savedAt.value = Date.now()
    answeredSet.value.add(String(q.value.id))

    // update cache currentAnswer để quay lại không cần gọi lại API
    const qid = questionsOrder.value[index.value]
    if (qid && questionCache.has(qid)) {
      const cur = questionCache.get(qid)!
      questionCache.set(qid, {
        ...cur,
        currentAnswer: {
          selected_id: (answer_data as any).selected_id ?? null,
          selected_ids: (answer_data as any).selected_ids ?? [],
          text: (answer_data as any).text ?? '',
        },
      })
    }
  } finally {
    saving.value = false
  }
}

function onChanged() {
  // radio/checkbox: lưu luôn (debounce nhẹ cho UX)
  saveDraftDebounced()
}
function onTextInput() {
  saveDraftDebounced()
}

/** ===== Navigation ===== */
async function goTo(i: number) {
  if (i < 0 || i >= questionsOrder.value.length) return
  // flush draft của câu hiện tại trước khi đi
  await flushDraft()
  index.value = i
}

async function goPrev() {
  if (index.value <= 0) return
  await goTo(index.value - 1)
}

async function goNext() {
  if (isLast.value) {
    openSubmitConfirm()
    return
  }
  await goTo(index.value + 1)
}

async function flushDraft() {
  // flush debounce (nếu đang pending) + save cuối
  saveDraftDebounced.flush?.()
  await saveDraftInternal()
}

/** ===== Submit ===== */
function openSubmitConfirm() {
  showConfirmSubmit.value = true
}
function closeSubmitConfirm() {
  showConfirmSubmit.value = false
}
async function confirmSubmit() {
  showConfirmSubmit.value = false
  await finishQuiz()
}

async function finishQuiz() {
  if (!attemptId.value || finishing.value) return
  finishing.value = true
  try {
    await flushDraft()
    const res = await finishAttempt(attemptId.value)
    submitResult.value = res
    showResultPopup.value = true
  } catch (e) {
    alert('Nộp bài thất bại. Thử lại nhé.')
  } finally {
    finishing.value = false
  }
}

/** ===== Format result ===== */
function formatUserAnswer(it: any) {
  const a = it?.user_answer_data ?? {}
  if (typeof a?.text === 'string' && a.text.trim()) return a.text
  if (a?.selected_id) return it?.user_answer_text || a.selected_id
  if (Array.isArray(a?.selected_ids) && a.selected_ids.length)
    return it?.user_answer_text || a.selected_ids.join(', ')
  return it?.user_answer_text || 'Chưa trả lời'
}

function formatCorrectAnswer(it: any) {
  const t = it?.question_type
  if (t === 'short_answer' || t === 'fill_in_the_blank') {
    const arr = it?.correct_answer_data?.accepted_texts
    if (Array.isArray(arr) && arr.length) return arr.join(' / ')
  }
  if (t === 'true_false') {
    // backend đang trả correct_answer_text là "Đúng/Sai"
    if (it?.correct_answer_text) return it.correct_answer_text
    const v = it?.correct_answer_data?.correct_value
    if (typeof v === 'boolean') return v ? 'Đúng' : 'Sai'
  }
  if (it?.correct_answer_text) return it.correct_answer_text
  return '—'
}

/** ===== Init ===== */
onMounted(async () => {
  pageLoading.value = true
  try {
    const blockId = (route.query.block_id as string) || ''
    const courseId = (route.query.course_id as string) || undefined

    if (!blockId) throw new Error('NO_BLOCK_ID')

    const block = await getBlockDetail(blockId)
    quizId.value = block?.payload?.quiz_id || block?.payload?.quizId || null
    quizTitle.value = block?.title || block?.payload?.title || 'Bài kiểm tra'

    if (!quizId.value) throw new Error('NO_QUIZ_ID')

    const attempt = await startOrResumeAttempt(quizId.value, courseId)
    attemptId.value = attempt?.attempt_id || attempt?.id || null
    questionsOrder.value = attempt?.questions_order || []
    timeLimitSeconds.value = attempt?.time_limit_seconds || null

    const ts = attempt?.time_start ? new Date(attempt.time_start).getTime() : Date.now()
    timeStart.value = Number.isFinite(ts) ? ts : Date.now()

    if (!attemptId.value) throw new Error('NO_ATTEMPT_ID')
    if (!Array.isArray(questionsOrder.value) || questionsOrder.value.length === 0)
      throw new Error('NO_QUESTIONS')

    index.value = 0
    await loadQuestionByIndex(0)

    startTimer()
  } catch (e) {
    console.error(e)
    alert('Không thể mở bài kiểm tra.')
    router.back()
  } finally {
    pageLoading.value = false
  }
})

watch(index, async (i) => {
  await loadQuestionByIndex(i)
})

/** ===== Router back ===== */
function goBack() {
  router.back()
}

/** ===== Debounce with flush ===== */
function debounce<T extends (...args: any[]) => any>(fn: T, wait = 600) {
  let t: any = null
  const wrapped: any = (...args: Parameters<T>) => {
    clearTimeout(t)
    t = setTimeout(() => fn(...args), wait)
  }
  wrapped.flush = () => {
    clearTimeout(t)
    return fn()
  }
  return wrapped as T & { flush: () => any }
}
</script>

<style scoped>
/* ===== Base ===== */
.quiz-shell {
  min-height: 100vh;
  background: radial-gradient(1200px 600px at 20% 0%, #eef2ff 0%, #f8fafc 55%, #f1f5f9 100%);
  color: #0f172a;
}

/* ===== Topbar ===== */
.topbar {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 14px 18px;
  background: rgba(255, 255, 255, 0.75);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid rgba(15, 23, 42, 0.08);
}

.topbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.icon-btn {
  width: 40px;
  height: 40px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #fff;
  cursor: pointer;
  font-weight: 900;
}

.topbar-title .title {
  font-weight: 900;
  font-size: 16px;
}

.topbar-title .sub {
  font-size: 13px;
  color: #475569;
  margin-top: 2px;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dot {
  margin: 0 6px;
}

.muted {
  color: #64748b;
}

/* ===== Layout ===== */
.layout {
  display: grid;
  grid-template-columns: 280px 1fr;
  gap: 18px;
  padding: 18px;
  max-width: 1200px;
  margin: 0 auto;
}

/* ===== Sidebar ===== */
.sidebar-card {
  position: sticky;
  top: 78px;
  background: rgba(255, 255, 255, 0.8);
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 18px;
  padding: 14px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
}

.sidebar-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}

.sidebar-title {
  font-weight: 900;
}

.sidebar-sub {
  font-size: 12px;
  color: #64748b;
}

.grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 8px;
  padding: 8px 0 6px;
}

.qdot {
  height: 36px;
  border-radius: 12px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #fff;
  cursor: pointer;
  font-weight: 900;
}

.qdot.done {
  background: #e0f2fe;
  border-color: rgba(2, 132, 199, 0.25);
}

.qdot.active {
  background: #2563eb;
  color: #fff;
  border-color: #2563eb;
  box-shadow: 0 10px 25px rgba(37, 99, 235, 0.25);
}

.sidebar-note {
  margin-top: 10px;
  display: grid;
  gap: 6px;
}

.legend {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #475569;
  font-size: 13px;
}
.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 999px;
  border: 1px solid rgba(15, 23, 42, 0.18);
  background: #fff;
}
.legend-dot.done {
  background: #e0f2fe;
  border-color: rgba(2, 132, 199, 0.25);
}
.legend-dot.active {
  background: #2563eb;
  border-color: #2563eb;
}

/* ===== Main card ===== */
.card {
  background: #fff;
  border: 1px solid rgba(15, 23, 42, 0.08);
  border-radius: 22px;
  padding: 22px;
  box-shadow: 0 18px 45px rgba(15, 23, 42, 0.08);
}

.qhead {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  border-radius: 999px;
  background: #eef2ff;
  color: #3730a3;
  font-weight: 800;
  font-size: 12px;
}

.lock {
  font-size: 13px;
  color: #b45309;
  background: #fffbeb;
  border: 1px solid #fde68a;
  padding: 6px 10px;
  border-radius: 999px;
}

.qcontent {
  font-size: 17px;
  line-height: 1.65;
  color: #0f172a;
  margin-bottom: 14px;
}

.media {
  display: grid;
  gap: 10px;
  margin: 12px 0 18px;
}
.media-item img {
  width: 100%;
  max-width: 520px;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.12);
}
.media-cap {
  font-size: 13px;
  color: #475569;
  margin-top: 6px;
}

/* ===== Answers ===== */
.answers {
  display: grid;
  gap: 12px;
  margin-top: 10px;
}

.ans {
  display: flex;
  gap: 12px;
  align-items: flex-start;
  padding: 14px 14px;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #fff;
  cursor: pointer;
  transition:
    transform 0.12s ease,
    box-shadow 0.12s ease,
    border-color 0.12s ease;
}

.ans:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 30px rgba(15, 23, 42, 0.12);
  border-color: rgba(37, 99, 235, 0.35);
}

.ans.selected {
  border-color: #2563eb;
  background: #eff6ff;
  box-shadow: 0 18px 35px rgba(37, 99, 235, 0.2);
}

.ans.disabled {
  opacity: 0.75;
  cursor: not-allowed;
}

.ans input {
  margin-top: 3px;
}

.ans-text {
  line-height: 1.5;
}

/* ===== Text ===== */
.text-area textarea {
  width: 100%;
  min-height: 150px;
  padding: 14px;
  border-radius: 16px;
  border: 1px solid rgba(15, 23, 42, 0.18);
  font-size: 15px;
  line-height: 1.6;
  outline: none;
  resize: vertical;
}
.text-area textarea:focus {
  border-color: rgba(37, 99, 235, 0.55);
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14);
}
.text-area textarea:disabled {
  background: #f8fafc;
}

.hint {
  margin-top: 8px;
  color: #64748b;
  font-size: 13px;
}

/* ===== Nav ===== */
.qnav {
  display: grid;
  grid-template-columns: auto 1fr auto;
  align-items: center;
  gap: 10px;
  margin-top: 18px;
  padding-top: 14px;
  border-top: 1px solid rgba(15, 23, 42, 0.08);
}
.qnav-mid {
  text-align: center;
  font-size: 13px;
}

.last-tip {
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: 14px;
  background: #f1f5f9;
  border: 1px solid rgba(15, 23, 42, 0.08);
  color: #334155;
  font-size: 13px;
}

/* ===== Buttons ===== */
.btn {
  border: 1px solid rgba(15, 23, 42, 0.14);
  background: #fff;
  border-radius: 14px;
  padding: 10px 14px;
  font-weight: 900;
  cursor: pointer;
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}
.btn.ghost {
  background: transparent;
}
.btn.primary {
  background: #2563eb;
  border-color: #2563eb;
  color: #fff;
  box-shadow: 0 14px 30px rgba(37, 99, 235, 0.22);
}
.btn.danger {
  background: #ef4444;
  border-color: #ef4444;
  color: #fff;
  box-shadow: 0 14px 30px rgba(239, 68, 68, 0.22);
}

.pill {
  border-radius: 999px;
  padding: 8px 10px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  background: #fff;
}
.timer {
  font-weight: 900;
}

/* ===== Overlay / Modal ===== */
.overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  background: rgba(2, 6, 23, 0.55);
  display: grid;
  place-items: center;
  padding: 14px;
}

.modal {
  width: 440px;
  max-width: calc(100vw - 24px);
  background: #fff;
  border-radius: 18px;
  border: 1px solid rgba(15, 23, 42, 0.12);
  box-shadow: 0 30px 90px rgba(2, 6, 23, 0.35);
  padding: 16px;
}
.modal.big {
  width: 820px;
  max-height: 85vh;
  overflow: auto;
}

.modal-title {
  font-weight: 1000;
  font-size: 16px;
  margin-bottom: 10px;
}

.modal-desc {
  color: #334155;
  line-height: 1.55;
  margin-bottom: 14px;
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

/* ===== Result ===== */
.result-summary {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
  margin: 10px 0 14px;
}
.sum-card {
  border: 1px solid rgba(15, 23, 42, 0.1);
  background: #f8fafc;
  border-radius: 16px;
  padding: 12px;
}
.sum-label {
  font-size: 12px;
  color: #64748b;
  margin-bottom: 4px;
  font-weight: 800;
}
.sum-value {
  font-size: 16px;
  font-weight: 1000;
}
.sum-value.ok {
  color: #15803d;
}
.sum-value.bad {
  color: #b91c1c;
}

.result-list {
  display: grid;
  gap: 12px;
}

.result-item {
  border: 1px solid rgba(15, 23, 42, 0.1);
  border-radius: 16px;
  padding: 12px;
  background: #fff;
}

.ri-top {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 10px;
}
.ri-title {
  font-weight: 1000;
}
.ri-pill {
  padding: 6px 10px;
  border-radius: 999px;
  font-weight: 1000;
  font-size: 12px;
  border: 1px solid rgba(15, 23, 42, 0.12);
}
.ri-pill.ok {
  background: #ecfdf5;
  color: #166534;
  border-color: rgba(22, 101, 52, 0.18);
}
.ri-pill.bad {
  background: #fef2f2;
  color: #991b1b;
  border-color: rgba(153, 27, 27, 0.18);
}

.ri-meta {
  color: #64748b;
  font-size: 13px;
  margin-top: 4px;
}

.ri-row {
  margin-top: 8px;
  font-size: 14px;
  color: #0f172a;
}

.ri-foot {
  margin-top: 10px;
  font-weight: 900;
}
.ri-foot.ok {
  color: #15803d;
}
.ri-foot.bad {
  color: #b91c1c;
}

/* ===== Skeleton ===== */
.skeleton {
  display: grid;
  gap: 12px;
}
.sk-line {
  height: 14px;
  border-radius: 999px;
  background: linear-gradient(90deg, #eef2ff 0%, #f1f5f9 40%, #eef2ff 80%);
  animation: shimmer 1.2s infinite linear;
}
.w40 {
  width: 40%;
}
.w70 {
  width: 70%;
}
.w80 {
  width: 80%;
}
.w90 {
  width: 90%;
}

@keyframes shimmer {
  0% {
    filter: brightness(1);
  }
  50% {
    filter: brightness(0.92);
  }
  100% {
    filter: brightness(1);
  }
}

/* ===== Responsive ===== */
@media (max-width: 980px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .sidebar-card {
    position: relative;
    top: 0;
  }
  .grid {
    grid-template-columns: repeat(10, 1fr);
  }
  .result-summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
