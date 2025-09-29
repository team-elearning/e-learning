<!-- src/pages/teacher/exams/ExamDetail.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <!-- Đang tải -->
    <main v-if="loading" class="mx-auto max-w-screen-md px-6 py-16">
      <div class="mb-4 h-7 w-64 animate-pulse rounded bg-slate-200"></div>
      <div class="mb-8 h-4 w-80 animate-pulse rounded bg-slate-100"></div>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="rounded-2xl border border-slate-200 bg-white p-4 md:col-span-2 space-y-2">
          <div v-for="i in 6" :key="'skel-q-'+i" class="rounded-xl border p-3">
            <div class="mb-2 flex items-center justify-between">
              <div class="h-4 w-40 animate-pulse rounded bg-slate-200"></div>
              <div class="h-3 w-16 animate-pulse rounded bg-slate-100"></div>
            </div>
            <div class="h-4 w-3/4 animate-pulse rounded bg-slate-100"></div>
          </div>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-4 space-y-2">
          <div class="h-5 w-32 animate-pulse rounded bg-slate-200"></div>
          <div v-for="i in 5" :key="'skel-r-'+i" class="h-4 w-48 animate-pulse rounded bg-slate-100"></div>
        </div>
      </div>
    </main>

    <!-- Có dữ liệu -->
    <main v-else-if="exam" class="w-full mx-auto max-w-screen-xl px-6 py-8 md:px-10">
      <div class="mb-5 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-semibold">{{ exam.title }}</h1>
          <div class="mt-1 text-sm text-slate-500">
            Khoá: <span class="font-medium text-slate-700">{{ exam.course }}</span> ·
            {{ exam.durationMin }} phút · {{ exam.totalQuestions }} câu hỏi
          </div>
        </div>
        <div class="flex gap-2">
          <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50" @click="toGrading">Chấm bài</button>
          <button class="rounded-2xl bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-700">
            Sửa đề
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <!-- Questions -->
        <div class="rounded-2xl border border-slate-200 bg-white p-4 md:col-span-2">
          <h2 class="mb-3 text-base font-semibold">Danh sách câu hỏi</h2>
          <ul class="space-y-2 text-sm">
            <li v-for="q in questions" :key="q.no" class="rounded-xl border p-3">
              <div class="flex items-center justify-between">
                <div class="font-medium">Câu {{ q.no }} · {{ q.type.toUpperCase() }}</div>
                <div class="text-xs text-slate-500">{{ q.points }} điểm</div>
              </div>
              <p class="mt-1">{{ q.text }}</p>
            </li>
          </ul>
        </div>

        <!-- Overview -->
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <h2 class="mb-3 text-base font-semibold">Tổng quan</h2>
          <ul class="space-y-2 text-sm">
            <li>• Lịch làm bài: <span class="font-medium text-slate-700">{{ exam.scheduledAt }}</span></li>
            <li>
              • Trạng thái:
              <span
                class="ml-1 rounded-full border px-2 py-0.5 text-xs"
                :class="exam.status==='published'
                         ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                         : 'bg-amber-50 text-amber-700 border-amber-200'"
              >
                {{ exam.status === 'published' ? 'Đã phát hành' : 'Nháp' }}
              </span>
            </li>
            <li>• Bài nộp: <span class="font-medium text-slate-700">{{ exam.submissions }}</span></li>
            <li>• Điểm trung bình: <span class="font-medium text-slate-700">{{ exam.avgScore }}</span></li>
            <li>• Cập nhật: <span class="font-medium text-slate-700">{{ exam.updatedAt }}</span></li>
          </ul>
        </div>
      </div>
    </main>

    <!-- Không tìm thấy -->
    <main v-else class="mx-auto max-w-screen-md px-6 py-16 text-center">
      <h1 class="text-xl font-semibold">Không tìm thấy đề</h1>
      <p class="mt-2 text-slate-500">Vui lòng quay lại danh sách bài kiểm tra.</p>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/** View models */
type ExamStatus = 'published' | 'draft'
type ExamVM = {
  id: number
  title: string
  course: string     // dùng level từ service nếu không có course
  durationMin: number
  totalQuestions: number
  status: ExamStatus
  submissions: number
  avgScore: number | string
  updatedAt: string
  scheduledAt: string
}
type QVM = { no: number; type: string; points: number; text: string }

/** Router & state */
const route = useRoute()
const router = useRouter()
const id = ref<number>(Number(route.params.id))

const loading = ref(true)
const exam = ref<ExamVM | null>(null)
const questions = ref<QVM[]>([])

/** Optional service (không sửa service) */
type DetailFn = (id: string | number) => Promise<any>
let detailFn: DetailFn | undefined

async function tryInitService() {
  try {
    const mod = await import('@/services/exam.service')
    if (mod?.examService?.detail) {
      detailFn = mod.examService.detail as DetailFn
    }
  } catch {
    // fallback mock
  }
}

/** Map ExamDetail (service) -> ExamVM/QVM */
function mapFromService(d: any): { exam: ExamVM; questions: QVM[] } {
  const durationMin = Math.max(1, Math.round((Number(d.durationSec) || 0) / 60))
  const st: ExamStatus = d.status === 'published' ? 'published' : 'draft'
  const vm: ExamVM = {
    id: Number(d.id),
    title: String(d.title || `Đề #${d.id}`),
    course: String(d.level || '—'),
    durationMin,
    totalQuestions: Number(d.questionsCount || (d.questions?.length ?? 0)),
    status: st,
    submissions: (Number(d.id) * 13) % 120,
    avgScore: ((60 + (Number(d.id) % 40)) / 10).toFixed(1),
    updatedAt: new Date(d.updatedAt || Date.now()).toLocaleString(),
    scheduledAt: new Date(Date.now() + (Number(d.id) % 5) * 864e5).toLocaleString()
  }
  const qs: QVM[] = (d.questions || []).map((q: any, i: number) => ({
    no: i + 1,
    type: String(q.type || 'single'),
    points: Number(q.score || 1),
    text: String(q.text || `Câu hỏi #${i + 1}`)
  }))
  return { exam: vm, questions: qs }
}

/** Mock khi không có service */
function mockDetail(examId: number): { exam: ExamVM; questions: QVM[] } {
  const published = examId % 3 !== 1
  const vm: ExamVM = {
    id: examId,
    title: `Đề kiểm tra #${examId}`,
    course: `Khoá ${(examId % 6) + 1}`,
    durationMin: 20 + (examId % 6) * 5,
    totalQuestions: 24,
    status: published ? 'published' : 'draft',
    submissions: (examId * 13) % 120,
    avgScore: ((60 + (examId % 40)) / 10).toFixed(1),
    updatedAt: new Date(Date.now() - examId * 36e5).toLocaleString(),
    scheduledAt: new Date(Date.now() + (examId % 5) * 864e5).toLocaleString()
  }
  const types = ['single', 'multi', 'boolean', 'fill', 'match', 'order']
  const qs: QVM[] = Array.from({ length: vm.totalQuestions }).map((_, i) => ({
    no: i + 1,
    type: types[(i + examId) % types.length],
    points: 1 + ((i + examId) % 3),
    text: `Nội dung câu hỏi mẫu số ${i + 1}`
  }))
  return { exam: vm, questions: qs }
}

/** Fetch detail (chống race) */
let loadToken = 0
async function load(currentId = id.value) {
  const token = ++loadToken
  loading.value = true
  try {
    const examId = Number(currentId)
    if (!Number.isFinite(examId) || examId <= 0) {
      exam.value = null
      questions.value = []
      return
    }

    if (!detailFn) {
      const mapped = mockDetail(examId)
      if (token !== loadToken) return
      exam.value = mapped.exam
      questions.value = mapped.questions
      return
    }

    const d = await detailFn(examId)
    if (token !== loadToken) return
    const mapped = mapFromService(d)
    exam.value = mapped.exam
    questions.value = mapped.questions
  } catch {
    if (token === loadToken) {
      exam.value = null
      questions.value = []
    }
  } finally {
    if (token === loadToken) loading.value = false
  }
}

/** Actions */
function toGrading() {
  router.push({ path: `/teacher/exams/${id.value}/grading` })
}

/** Lifecycle */
onMounted(async () => {
  await tryInitService()
  await load(id.value)
})

watch(() => route.params.id, (nv) => {
  id.value = Number(nv)
  load(id.value)
})
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
</style>
