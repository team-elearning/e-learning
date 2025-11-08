<!-- src/pages/teacher/exams/SubmissionView.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="mx-auto w-full max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <!-- Header -->
      <div class="mb-5 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p class="text-sm text-slate-500">Đề #{{ examId }} • Bài nộp #{{ submissionId }}</p>
          <h1 class="text-xl font-semibold sm:text-2xl">Bài làm học sinh</h1>
        </div>
        <div class="flex gap-2">
          <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50" @click="goBack">
            ← Quay lại danh sách
          </button>
        </div>
      </div>

      <!-- Skeleton -->
      <div v-if="loading" class="space-y-2">
        <div v-for="i in 5" :key="'skel-'+i" class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="mb-2 h-4 w-48 animate-pulse rounded bg-slate-200"></div>
          <div class="h-3 w-3/4 animate-pulse rounded bg-slate-100"></div>
        </div>
      </div>

      <template v-else>
        <!-- Thông tin chung -->
        <div class="mb-5 grid gap-3 md:grid-cols-2">
          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <h3 class="mb-2 font-semibold">Thông tin học sinh</h3>
            <div class="grid grid-cols-2 gap-y-1 text-sm">
              <div class="text-slate-500">Họ tên</div><div class="font-medium">{{ info.studentName }}</div>
              <div class="text-slate-500">Lớp</div><div class="font-medium">{{ info.classCode }}</div>
              <div class="text-slate-500">Nộp lúc</div><div class="font-medium">{{ info.submittedAt }}</div>
              <div class="text-slate-500">Trạng thái</div>
              <div>
                <span
                  class="rounded-full border px-2 py-0.5 text-xs"
                  :class="info.status==='graded'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                    : 'bg-amber-50 text-amber-700 border-amber-200'"
                >
                  {{ info.status==='graded' ? 'Đã chấm' : 'Chưa chấm' }}
                </span>
              </div>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <h3 class="mb-2 font-semibold">Kết quả</h3>
            <div class="grid grid-cols-2 gap-y-1 text-sm">
              <div class="text-slate-500">Điểm</div><div class="font-semibold">{{ result.scoreText }}</div>
              <div class="text-slate-500">Số câu đúng</div><div class="font-medium">{{ result.correct }}/{{ result.total }}</div>
              <div class="text-slate-500">Đạt</div>
              <div class="font-medium" :class="result.passed ? 'text-emerald-600' : 'text-rose-600'">
                {{ result.passed ? 'ĐẠT' : 'CHƯA ĐẠT' }}
              </div>
            </div>
          </div>
        </div>

        <!-- Danh sách câu hỏi/đáp án -->
        <div class="rounded-2xl border border-slate-200 bg-white">
          <div class="border-b px-4 py-3 text-sm text-slate-600">Chi tiết câu hỏi</div>
          <div v-for="(q, i) in questions" :key="q.id" class="border-t px-4 py-4">
            <div class="mb-2 flex items-start justify-between gap-3">
              <div class="min-w-0">
                <div class="text-sm text-slate-500">Câu {{ i + 1 }} · {{ q.typeLabel }}</div>
                <div class="font-medium mt-0.5">{{ q.text }}</div>
              </div>
              <div class="shrink-0 text-sm">
                <span class="rounded-full border px-2 py-0.5"
                      :class="q.correct ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                                        : 'bg-rose-50 text-rose-700 border-rose-200'">
                  {{ q.correct ? 'Đúng' : 'Sai' }} · {{ q.score }}/{{ q.max }}
                </span>
              </div>
            </div>

            <div class="mt-2 grid gap-1 text-sm text-slate-700">
              <div class="text-slate-500">Trả lời:</div>
              <div class="font-medium">{{ q.answerView }}</div>
              <div class="text-slate-500 mt-1">Đáp án đúng:</div>
              <div class="font-medium">{{ q.goldView }}</div>
            </div>
          </div>

          <div v-if="!questions.length" class="p-6 text-center text-slate-500">
            Không có dữ liệu câu hỏi (mock).
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { examService } from '@/services/exam.service' // lấy đề (detail)

// ===== Route params (/teacher/exams/:examId/submissions/:submissionId)
const route = useRoute()
const router = useRouter()
const examId = computed(() => {
  const n = Number(route.params.examId); return Number.isFinite(n) && n > 0 ? n : 1
})
const submissionId = computed(() => Number(route.params.submissionId) || 0)

type RowStatus = 'pending' | 'graded'
type Row = {
  id: number
  examId: number
  studentName: string
  classCode: string
  submittedAt: string
  score: number | null
  status: RowStatus
}

const loading = ref(true)
const info = ref<Row>({
  id: submissionId.value,
  examId: examId.value,
  studentName: '—',
  classCode: '—',
  submittedAt: new Date().toLocaleString(),
  score: null,
  status: 'pending',
})

const result = ref({ scoreText: '—', correct: 0, total: 0, passed: false })

type QView = {
  id: string | number
  text: string
  typeLabel: string
  score: number
  max: number
  correct: boolean
  answerView: string
  goldView: string
}
const questions = ref<QView[]>([])

// ======= Mock submissions giống trang Grading (đảm bảo luôn có dữ liệu)
function makeMockRows(examIdInput: number): Row[] {
  const eid = Number.isFinite(examIdInput) && examIdInput > 0 ? examIdInput : 1
  const total = (eid % 7) + 9
  return Array.from({ length: total }).map((_, i) => {
    const sid = eid * 1000 + i + 1
    const graded = (i + eid) % 3 !== 0
    const score = graded ? Math.round(((6 + ((i + eid) % 5)) + 0.1) * 10) / 10 : null
    const cls = `L${(eid % 4) + 1}${String((i % 3) + 1).padStart(2, '0')}`
    const name = `HS ${(eid % 9) + 1}${String(i + 1).padStart(2, '0')}`
    const submittedAt = new Date(Date.now() - (i + 1) * 36e5).toLocaleString()
    return { id: sid, examId: eid, studentName: name, classCode: cls, submittedAt, score, status: graded ? 'graded' : 'pending' }
  })
}

function goBack() {
  router.push({ name: 'teacher-exam-grading', params: { id: String(examId.value) } })
}

function calcSummary() {
  const total = questions.value.length || 0
  const correct = questions.value.filter(q => q.correct).length
  const sum = questions.value.reduce((s, q) => s + q.score, 0)
  const max = questions.value.reduce((s, q) => s + q.max, 0)
  result.value = {
    scoreText: `${sum.toFixed(1)} / ${max}`,
    correct,
    total,
    passed: sum >= max * 0.6,
  }
}

async function load() {
  loading.value = true
  try {
    // 1) Lấy thông tin submission từ mock local
    const subs = makeMockRows(examId.value)
    const found = subs.find(s => Number(s.id) === submissionId.value)
    if (found) info.value = found

    // 2) Lấy đề thi từ service mock và dựng câu hỏi hiển thị
    const d = await examService.detail(examId.value)

    questions.value = d.questions.slice(0, 10).map((q: any, idx: number) => {
      const typeLabel =
        q.type === 'single' ? 'Trắc nghiệm 1 đáp án'
        : q.type === 'multi' ? 'Chọn nhiều đáp án'
        : q.type === 'boolean' ? 'Đúng/Sai'
        : q.type === 'fill' ? 'Điền từ'
        : q.type === 'match' ? 'Nối cặp'
        : 'Sắp xếp'

      const goldView =
        q.type === 'single' || q.type === 'multi' ? (q.answer || []).join(', ')
        : q.type === 'boolean' ? (q.answer ? 'Đúng' : 'Sai')
        : q.type === 'fill' ? (q.answer || []).join(' | ')
        : q.type === 'match' ? (q.pairs || []).map((p: any) => `${p.left} → ${p.right}`).join(' ; ')
        : (q.answer || []).join(' → ')

      // giả lập trả lời: nửa đúng nửa sai
      let answerView = ''
      let correct = idx % 2 === 0
      if (q.type === 'single') {
        const pick = correct ? q.answer[0] : (q.choices[1]?.id ?? q.answer[0])
        answerView = String(pick)
      } else if (q.type === 'multi') {
        answerView = correct ? (q.answer || []).join(', ') : (q.choices || []).slice(0, 2).map((c: any) => c.id).join(', ')
      } else if (q.type === 'boolean') {
        answerView = correct ? (q.answer ? 'Đúng' : 'Sai') : (!q.answer ? 'Đúng' : 'Sai')
      } else if (q.type === 'fill') {
        answerView = correct ? (q.answer || []).join(' | ') : '… | …'
      } else if (q.type === 'match') {
        answerView = correct
          ? (q.pairs || []).map((p: any) => `${p.left} → ${p.right}`).join(' ; ')
          : (q.pairs || []).map((p: any) => `${p.left} → ???`).join(' ; ')
      } else { // order
        answerView = correct ? (q.answer || []).join(' → ') : (q.items || q.answer || []).slice().reverse().join(' → ')
      }

      const score = correct ? q.score : 0

      return {
        id: q.id,
        text: q.text,
        typeLabel,
        score,
        max: q.score,
        correct,
        answerView,
        goldView,
      } as QView
    })

    calcSummary()
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
table th, table td { word-break: break-word; }
</style>
