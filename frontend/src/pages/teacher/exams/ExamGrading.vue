<!-- src/pages/teacher/exams/ExamGrading.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <!-- Header -->
      <div class="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 class="text-xl font-semibold sm:text-2xl">Chấm bài · {{ header }}</h1>

        <!-- Tools -->
        <div class="grid grid-cols-1 gap-2 sm:auto-cols-fr sm:grid-flow-col">
          <label class="sr-only" for="search">Tìm theo tên/lớp</label>
          <div class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" aria-hidden="true">
              <circle cx="11" cy="11" r="8" stroke-width="2" />
              <path d="M21 21l-4.3-4.3" stroke-width="2" />
            </svg>
            <input
              id="search"
              v-model.trim="q"
              type="text"
              placeholder="Tìm theo tên/lớp…"
              class="w-full bg-transparent text-sm outline-none placeholder:text-slate-400"
              @input="debouncedFilter()"
            />
          </div>

          <select
            v-model="only"
            class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm"
            @change="touchFilterToken()"
          >
            <option value="all">Tất cả</option>
            <option value="pending">Chưa chấm</option>
            <option value="graded">Đã chấm</option>
          </select>
        </div>
      </div>

      <!-- Skeleton -->
      <div v-if="loading" class="space-y-2">
        <div v-for="i in 6" :key="'skel-'+i" class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="mb-2 h-4 w-40 animate-pulse rounded bg-slate-200"></div>
          <div class="h-3 w-3/4 animate-pulse rounded bg-slate-100"></div>
        </div>
      </div>

      <!-- Content -->
      <template v-else>
        <!-- Mobile: Card list -->
        <div class="grid grid-cols-1 gap-3 md:hidden">
          <article
            v-for="s in filtered"
            :key="s.id"
            class="rounded-2xl border border-slate-200 bg-white p-4"
          >
            <div class="flex items-start justify-between gap-3">
              <div class="min-w-0">
                <h3 class="font-semibold truncate" :title="s.studentName">{{ s.studentName }}</h3>
                <p class="mt-0.5 text-sm text-slate-500">
                  Lớp: <span class="font-medium">{{ s.classCode }}</span>
                </p>
              </div>
              <span
                class="shrink-0 rounded-full border px-2 py-0.5 text-xs"
                :class="s.status==='graded'
                         ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                         : 'bg-amber-50 text-amber-700 border-amber-200'"
              >
                {{ s.status === 'graded' ? 'Đã chấm' : 'Chưa chấm' }}
              </span>
            </div>

            <div class="mt-3 grid grid-cols-2 gap-2 text-sm text-slate-600">
              <div class="space-y-1">
                <div class="text-slate-500">Nộp lúc</div>
                <div class="font-medium leading-5">{{ s.submittedAt }}</div>
              </div>
              <div class="space-y-1">
                <div class="text-slate-500">Điểm</div>
                <div class="font-semibold">{{ s.score ?? '—' }}</div>
              </div>
            </div>

            <div class="mt-4 grid grid-cols-2 gap-2">
              <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50">Xem bài</button>
              <button
                class="rounded-xl bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-700"
              >
                {{ s.status === 'graded' ? 'Sửa điểm' : 'Chấm điểm' }}
              </button>
            </div>
          </article>

          <p v-if="!filtered.length" class="p-6 text-center text-slate-500">
            Không có bài nộp phù hợp.
          </p>
        </div>

        <!-- Desktop: Table -->
        <div class="hidden md:block rounded-2xl border border-slate-200 bg-white">
          <div class="overflow-x-auto">
            <table class="w-full table-fixed">
              <thead class="sticky top-0 z-10 bg-slate-50 text-left text-sm text-slate-600">
                <tr>
                  <th class="p-3 w-[28%]">Học sinh</th>
                  <th class="p-3 w-[12%]">Lớp</th>
                  <th class="p-3 w-[24%]">Thời gian nộp</th>
                  <th class="p-3 w-[10%]">Điểm</th>
                  <th class="p-3 w-[14%]">Trạng thái</th>
                  <th class="p-3 w-[22%]">Thao tác</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="s in filtered" :key="s.id" class="border-t text-sm">
                  <td class="p-3 font-medium truncate" :title="s.studentName">{{ s.studentName }}</td>
                  <td class="p-3 truncate">{{ s.classCode }}</td>
                  <td class="p-3 truncate" :title="s.submittedAt">{{ s.submittedAt }}</td>
                  <td class="p-3">{{ s.score ?? '—' }}</td>
                  <td class="p-3">
                    <span
                      class="rounded-full border px-2 py-0.5 text-xs whitespace-nowrap"
                      :class="s.status==='graded'
                               ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                               : 'bg-amber-50 text-amber-700 border-amber-200'"
                    >
                      {{ s.status === 'graded' ? 'Đã chấm' : 'Chưa chấm' }}
                    </span>
                  </td>
                  <td class="p-3">
                    <!-- NGĂN QUẤN DÒNG + Cố định bề rộng nút -->
                    <div class="flex flex-nowrap items-center gap-2">
                      <button
                        class="rounded-xl border px-3 py-1.5 text-sm hover:bg-slate-50 whitespace-nowrap min-w-[96px]"
                      >
                        Xem bài
                      </button>
                      <button
                        class="rounded-xl bg-sky-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-sky-700 whitespace-nowrap min-w-[96px]"
                      >
                        {{ s.status === 'graded' ? 'Sửa điểm' : 'Chấm điểm' }}
                      </button>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>

            <p v-if="!filtered.length" class="p-6 text-center text-slate-500">
              Không có bài nộp phù hợp.
            </p>
          </div>
        </div>
      </template>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

type RowStatus = 'pending' | 'graded'
type Row = {
  id: number
  studentName: string
  classCode: string
  submittedAt: string
  score: number | null
  status: RowStatus
}

const route = useRoute()
const id = ref<number>(Number(route.params.id))

const header = ref(`Đề #${id.value}`)
const loading = ref(true)
const rows = ref<Row[]>([])

const q = ref('')
const only = ref<'all' | RowStatus>('all')

type DetailFn = (id: string | number) => Promise<any>
let detailFn: DetailFn | undefined

async function tryInitService() {
  try {
    const mod = await import('@/services/exam.service')
    if (mod?.examService?.detail) detailFn = mod.examService.detail as DetailFn
  } catch {}
}

function makeMockRows(examId: number): Row[] {
  const total = (examId % 7) + 9
  return Array.from({ length: total }).map((_, i) => {
    const sid = examId * 1000 + i + 1
    const graded = (i + examId) % 3 !== 0
    const score = graded ? Math.round(((6 + ((i + examId) % 5)) + 0.1) * 10) / 10 : null
    const cls = `L${(examId % 4) + 1}${String((i % 3) + 1).padStart(2, '0')}`
    const name = `HS ${(examId % 9) + 1}${String(i + 1).padStart(2, '0')}`
    const submittedAt = new Date(Date.now() - (i + 1) * 36e5).toLocaleString()
    return { id: sid, studentName: name, classCode: cls, submittedAt, score, status: graded ? 'graded' : 'pending' }
  })
}

let loadToken = 0
async function load(examId = id.value) {
  const token = ++loadToken
  loading.value = true
  try {
    if (detailFn) {
      try {
        const d = await detailFn(examId)
        if (token === loadToken && d?.title) header.value = String(d.title)
      } catch {}
    } else header.value = `Đề #${examId}`

    const data = makeMockRows(examId)
    if (token !== loadToken) return
    rows.value = data
  } finally {
    if (token === loadToken) loading.value = false
  }
}

/** Debounce filter */
let ft: number | null = null
const filterToken = ref(0)
function debouncedFilter() {
  if (ft) window.clearTimeout(ft)
  ft = window.setTimeout(() => { filterToken.value++ }, 250) as unknown as number
}
function touchFilterToken() { filterToken.value++ }

/** Filtering */
const filtered = computed(() => {
  void filterToken.value
  const key = q.value.toLowerCase()
  let arr = rows.value
  if (only.value !== 'all') arr = arr.filter(s => s.status === only.value)
  if (key) {
    arr = arr.filter(s =>
      s.studentName.toLowerCase().includes(key) ||
      s.classCode.toLowerCase().includes(key)
    )
  }
  return arr
})

onMounted(async () => {
  await tryInitService()
  await load(id.value)
})
watch(() => route.params.id, (nv) => {
  id.value = Number(nv)
  load(id.value)
})
onBeforeUnmount(() => { if (ft) window.clearTimeout(ft) })
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
table th, table td, h3 { word-break: break-word; }
@media (hover: none) {
  .hover\:bg-slate-50:hover { background: inherit; }
  .hover\:bg-sky-700:hover { background: rgb(3 105 161); }
}
</style>
