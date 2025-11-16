<!-- src/pages/teacher/exams/ExamCreate.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="mx-auto max-w-screen-xl px-4 py-6 sm:px-6 md:px-10">
      <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 class="text-2xl font-semibold">Tạo bài kiểm tra</h1>
          <p class="text-sm text-slate-500">Nhập thông tin đề và danh sách câu hỏi</p>
        </div>
        <div class="flex gap-2">
          <button type="button" class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50" @click="router.back()">
            Quay lại
          </button>
          <button
            type="button"
            class="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-60"
            :disabled="saving"
            @click="submit"
          >
            {{ saving ? 'Đang lưu…' : 'Lưu đề' }}
          </button>
        </div>
      </div>

      <form class="grid gap-4 md:grid-cols-3" @submit.prevent="submit">
        <section class="md:col-span-2 space-y-4">
          <div class="rounded-2xl border border-slate-200 bg-white p-4 space-y-4">
            <div class="grid gap-3 md:grid-cols-2">
              <label class="space-y-1">
                <span class="text-sm font-medium text-slate-700">Tên đề <b class="text-rose-600">*</b></span>
                <input
                  v-model.trim="form.title"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-400/30"
                  placeholder="Ví dụ: Kiểm tra Toán tuần 3"
                />
              </label>
              <label class="space-y-1">
                <span class="text-sm font-medium text-slate-700">Khối lớp</span>
                <select v-model="form.level" class="select-base">
                  <option v-for="lv in levels" :key="lv" :value="lv">{{ lv }}</option>
                </select>
              </label>
              <label class="space-y-1">
                <span class="text-sm font-medium text-slate-700">Thời lượng (phút)</span>
                <input
                  v-model.number="form.durationMin"
                  type="number"
                  min="1"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-400/30"
                />
              </label>
              <label class="space-y-1">
                <span class="text-sm font-medium text-slate-700">Điểm đạt</span>
                <input
                  v-model.number="form.passScore"
                  type="number"
                  min="0"
                  step="0.5"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-400/30"
                />
              </label>
              <label class="space-y-1">
                <span class="text-sm font-medium text-slate-700">Trạng thái</span>
                <select v-model="form.status" class="select-base">
                  <option value="draft">Nháp</option>
                  <option value="published">Phát hành ngay</option>
                </select>
              </label>
              <label class="space-y-1">
                <span class="text-sm font-medium text-slate-700">Mô tả</span>
                <textarea
                  v-model.trim="form.description"
                  rows="3"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-400/30"
                  placeholder="Tóm tắt nội dung bài kiểm tra"
                />
              </label>
            </div>
          </div>

          <div class="rounded-2xl border border-slate-200 bg-white p-4">
            <div class="mb-3 flex items-center justify-between">
              <div>
                <h2 class="text-base font-semibold">Danh sách câu hỏi</h2>
                <p class="text-xs text-slate-500">Hỗ trợ câu hỏi trắc nghiệm 1 đáp án, nhiều đáp án, Đúng/Sai và điền từ</p>
              </div>
              <button
                type="button"
                class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
                @click="addQuestion()"
              >
                + Thêm câu hỏi
              </button>
            </div>

            <div v-if="!questions.length" class="rounded-xl border border-dashed p-6 text-center text-slate-500">
              Chưa có câu hỏi nào. Nhấn “Thêm câu hỏi” để bắt đầu.
            </div>

            <div v-for="(q, idx) in questions" :key="q.id" class="mb-3 rounded-xl border border-slate-200 p-3 shadow-sm">
              <div class="flex items-center justify-between gap-3">
                <div class="flex flex-wrap items-center gap-2 text-sm">
                  <span class="rounded-lg bg-slate-100 px-2 py-1 font-semibold text-slate-700">Câu {{ idx + 1 }}</span>
                  <select v-model="q.type" class="rounded-lg border px-2 py-1 text-sm" @change="onTypeChange(q)">
                    <option v-for="t in availableTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
                  </select>
                  <label class="flex items-center gap-1 text-xs text-slate-600">
                    <span>Điểm:</span>
                    <input v-model.number="q.score" type="number" min="0.5" step="0.5" class="w-16 rounded border px-2 py-1 text-sm" />
                  </label>
                </div>
                <button type="button" class="text-sm text-rose-600 hover:underline" @click="removeQuestion(idx)">Xoá</button>
              </div>

              <label class="mt-2 block space-y-1">
                <span class="text-sm font-medium text-slate-700">Nội dung câu hỏi</span>
                <textarea
                  v-model.trim="q.text"
                  rows="2"
                  class="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-400/30"
                  placeholder="Nhập nội dung câu hỏi"
                />
              </label>

              <div v-if="q.type === 'single' || q.type === 'multi'" class="mt-3 space-y-2">
                <div class="flex items-center justify-between text-sm">
                  <span class="font-medium text-slate-700">Phương án</span>
                  <button type="button" class="text-sky-600 hover:underline" @click="addChoice(q)">+ Thêm phương án</button>
                </div>
                <div v-for="(c, cIdx) in q.choices" :key="c.id" class="flex items-center gap-2">
                  <input
                    :type="q.type === 'single' ? 'radio' : 'checkbox'"
                    :name="'ans-' + q.id"
                    class="h-4 w-4"
                    :value="c.id"
                    :checked="isChoiceChecked(q, c.id)"
                    @change="toggleChoice(q, c.id, $event)"
                  />
                  <input
                    v-model.trim="c.text"
                    class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-400/30"
                    :placeholder="`Phương án ${cIdx + 1}`"
                  />
                  <button type="button" class="text-xs text-rose-600 hover:underline" @click="removeChoice(q, cIdx)">Xoá</button>
                </div>
              </div>

              <div v-else-if="q.type === 'boolean'" class="mt-3 space-x-3 text-sm">
                <label class="inline-flex items-center gap-2">
                  <input type="radio" :name="'bool-' + q.id" value="true" class="h-4 w-4" :checked="q.boolAnswer === true" @change="q.boolAnswer = true" />
                  <span>Đúng</span>
                </label>
                <label class="inline-flex items-center gap-2">
                  <input type="radio" :name="'bool-' + q.id" value="false" class="h-4 w-4" :checked="q.boolAnswer === false" @change="q.boolAnswer = false" />
                  <span>Sai</span>
                </label>
              </div>

              <div v-else-if="q.type === 'fill'" class="mt-3 space-y-2">
                <label class="flex items-center gap-2 text-sm text-slate-700">
                  <span>Số chỗ trống:</span>
                  <input v-model.number="q.blanks" type="number" min="1" class="w-16 rounded border px-2 py-1 text-sm" @change="syncFillAnswers(q)" />
                </label>
                <div class="space-y-2">
                  <label v-for="(ans, aIdx) in q.fillAnswers" :key="'f-'+aIdx" class="flex items-center gap-2 text-sm">
                    <span class="w-16 text-slate-500">Ô {{ aIdx + 1 }}</span>
                    <input
                      v-model.trim="q.fillAnswers[aIdx]"
                      class="flex-1 rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none focus:border-sky-400 focus:ring-2 focus:ring-sky-400/30"
                      placeholder="Đáp án"
                    />
                  </label>
                </div>
              </div>
            </div>
          </div>
        </section>

        <aside class="space-y-3">
          <div class="rounded-2xl border border-slate-200 bg-white p-4 space-y-2">
            <h3 class="text-base font-semibold">Tóm tắt</h3>
            <p class="text-sm text-slate-600">{{ questions.length }} câu hỏi · Tổng điểm {{ totalScore }}</p>
            <label class="flex items-center justify-between text-sm">
              <span>Trộn thứ tự câu hỏi</span>
              <input v-model="form.shuffleQuestions" type="checkbox" class="h-4 w-4" />
            </label>
            <label class="flex items-center justify-between text-sm">
              <span>Trộn đáp án trắc nghiệm</span>
              <input v-model="form.shuffleChoices" type="checkbox" class="h-4 w-4" />
            </label>
            <p class="text-xs text-slate-500">Có thể đổi lại sau khi chỉnh sửa đề.</p>
          </div>

          <div v-if="errors.length" class="rounded-2xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700 space-y-1">
            <div class="font-semibold">Cần kiểm tra:</div>
            <ul class="list-disc pl-5 space-y-1">
              <li v-for="err in errors" :key="err">{{ err }}</li>
            </ul>
          </div>

          <button
            type="submit"
            class="w-full rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700 disabled:opacity-60"
            :disabled="saving"
          >
            {{ saving ? 'Đang lưu…' : 'Lưu bài kiểm tra' }}
          </button>
        </aside>
      </form>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { examService, type Level, type QType, type Question } from '@/services/exam.service'

type ExamStatus = 'draft' | 'published'
type DraftChoice = { id: string; text: string }
type DraftQuestion = {
  id: string
  type: QType
  text: string
  score: number
  choices: DraftChoice[]
  correctChoices: string[]
  boolAnswer: boolean
  blanks: number
  fillAnswers: string[]
}

const router = useRouter()

const levels: Level[] = ['Lớp 1', 'Lớp 2', 'Lớp 3', 'Lớp 4', 'Lớp 5']
const availableTypes: { value: QType; label: string }[] = [
  { value: 'single', label: '1 đáp án' },
  { value: 'multi', label: 'Nhiều đáp án' },
  { value: 'boolean', label: 'Đúng / Sai' },
  { value: 'fill', label: 'Điền từ' },
]

const form = reactive({
  title: '',
  level: levels[1] as Level,
  durationMin: 30,
  passScore: 12,
  status: 'draft' as ExamStatus,
  description: '',
  shuffleQuestions: true,
  shuffleChoices: true,
})

const questions = reactive<DraftQuestion[]>([])
const errors = ref<string[]>([])
const saving = ref(false)

const totalScore = computed(() => questions.reduce((sum, q) => sum + Number(q.score || 0), 0))

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 8)}`
}

function makeQuestion(type: QType = 'single'): DraftQuestion {
  const baseChoices: DraftChoice[] = [
    { id: uid('c'), text: 'Phương án A' },
    { id: uid('c'), text: 'Phương án B' },
    { id: uid('c'), text: 'Phương án C' },
    { id: uid('c'), text: 'Phương án D' },
  ]
  return {
    id: uid('q'),
    type,
    text: '',
    score: 1,
    choices: type === 'single' || type === 'multi' ? baseChoices : [],
    correctChoices: type === 'multi' ? [baseChoices[0].id, baseChoices[1].id] : [baseChoices[0].id],
    boolAnswer: true,
    blanks: 1,
    fillAnswers: [''],
  }
}

function addQuestion(type: QType = 'single') {
  questions.push(makeQuestion(type))
}

function removeQuestion(idx: number) {
  questions.splice(idx, 1)
}

function onTypeChange(q: DraftQuestion) {
  if (q.type === 'single' || q.type === 'multi') {
    if (!q.choices.length) {
      q.choices = makeQuestion(q.type).choices
    }
    if (!q.correctChoices.length && q.choices[0]) {
      q.correctChoices = [q.choices[0].id]
    }
  } else if (q.type === 'boolean') {
    q.correctChoices = []
    q.choices = []
    q.boolAnswer = true
  } else if (q.type === 'fill') {
    q.correctChoices = []
    q.choices = []
    q.blanks = Math.max(1, q.blanks || 1)
    syncFillAnswers(q)
  }
}

function addChoice(q: DraftQuestion) {
  q.choices.push({ id: uid('c'), text: `Phương án ${q.choices.length + 1}` })
}

function removeChoice(q: DraftQuestion, idx: number) {
  const removed = q.choices.splice(idx, 1)[0]
  if (removed) {
    q.correctChoices = q.correctChoices.filter((id) => id !== removed.id)
  }
  if (!q.correctChoices.length && q.choices[0]) {
    q.correctChoices = [q.choices[0].id]
  }
}

function isChoiceChecked(q: DraftQuestion, id: string) {
  return q.correctChoices.includes(id)
}

function toggleChoice(q: DraftQuestion, id: string, ev: Event) {
  const checked = (ev.target as HTMLInputElement).checked
  if (q.type === 'single') {
    q.correctChoices = checked ? [id] : []
  } else {
    const set = new Set(q.correctChoices)
    if (checked) set.add(id)
    else set.delete(id)
    q.correctChoices = Array.from(set)
  }
}

function syncFillAnswers(q: DraftQuestion) {
  const blanks = Math.max(1, Math.floor(q.blanks || 1))
  q.blanks = blanks
  if (q.fillAnswers.length < blanks) {
    while (q.fillAnswers.length < blanks) q.fillAnswers.push('')
  } else {
    q.fillAnswers.splice(blanks)
  }
}

function mapQuestion(q: DraftQuestion): Question {
  const base = { id: q.id, text: q.text.trim(), score: Number(q.score) || 1 }
  if (q.type === 'single' || q.type === 'multi') {
    const answer = (q.type === 'single' ? q.correctChoices.slice(0, 1) : q.correctChoices.slice()).filter(Boolean)
    return {
      ...base,
      type: q.type,
      choices: q.choices.map((c) => ({ id: c.id, text: c.text.trim() || c.id })),
      answer,
    }
  }
  if (q.type === 'boolean') {
    return { ...base, type: 'boolean', answer: q.boolAnswer }
  }
  // fill
  const blanks = Math.max(1, Math.floor(q.blanks || 1))
  const answers = q.fillAnswers.slice(0, blanks).map((a) => a.trim())
  return { ...base, type: 'fill', blanks, answer: answers }
}

function validate(): Question[] | null {
  const errs: string[] = []
  if (!form.title.trim()) errs.push('Điền tên đề thi')
  if (!questions.length) errs.push('Thêm ít nhất 1 câu hỏi')

  const mapped: Question[] = []
  questions.forEach((q, idx) => {
    if (!q.text.trim()) errs.push(`Câu ${idx + 1}: chưa có nội dung`)
    if (!q.score || q.score <= 0) errs.push(`Câu ${idx + 1}: điểm phải > 0`)

    if (q.type === 'single' || q.type === 'multi') {
      if (q.choices.length < 2) errs.push(`Câu ${idx + 1}: cần ≥2 phương án`)
      if (!q.correctChoices.length) errs.push(`Câu ${idx + 1}: chọn đáp án đúng`)
    }
    if (q.type === 'fill') {
      if (!q.fillAnswers.slice(0, q.blanks).every((a) => a.trim())) {
        errs.push(`Câu ${idx + 1}: điền đáp án cho mọi ô trống`)
      }
    }

    mapped.push(mapQuestion(q))
  })

  errors.value = errs
  if (errs.length) return null
  return mapped
}

async function submit() {
  const mapped = validate()
  if (!mapped || saving.value) return

  saving.value = true
  try {
    const res = await examService.create({
      title: form.title.trim(),
      level: form.level,
      durationSec: Math.max(1, Math.floor(form.durationMin || 1)) * 60,
      passScore: Math.max(0, Number(form.passScore) || 0),
      status: form.status,
      description: form.description?.trim() || undefined,
      shuffleChoices: form.shuffleChoices,
      shuffleQuestions: form.shuffleQuestions,
      questions: mapped,
    })
    router.push({ name: 'teacher-exam-detail', params: { id: res.id } })
  } catch (e: any) {
    errors.value = [e?.message || 'Không thể lưu bài kiểm tra']
  } finally {
    saving.value = false
  }
}

// mặc định có 1 câu hỏi để điền nhanh
addQuestion('single')
</script>

<style scoped>
.select-base{
  @apply w-full rounded-xl border border-slate-200 bg-white px-3 pr-8 py-2 text-sm leading-6 outline-none;
  @apply focus:ring-2 focus:ring-sky-500/30 focus:border-sky-400;
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
  background-image: none;
}
</style>
