<!-- src/pages/teacher/exams/Exams.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <!-- Header -->
      <div class="mb-4 sm:mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 class="text-xl font-semibold sm:text-2xl">Bài kiểm tra</h1>
        <button
          class="w-full sm:w-auto rounded-xl bg-sky-600 px-4 py-2.5 font-semibold text-white hover:bg-sky-700 active:bg-sky-800"
          @click="createExam"
        >
          + Tạo bài kiểm tra
        </button>
      </div>

      <!-- Tools -->
      <div class="mb-5 grid grid-cols-1 gap-2 sm:gap-3 md:grid-cols-3">
        <!-- Search -->
        <div class="md:col-span-2">
          <label class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2.5">
            <svg viewBox="0 0 24 24" class="h-5 w-5 shrink-0 text-slate-400" fill="none" stroke="currentColor" aria-hidden="true">
              <circle cx="11" cy="11" r="8" stroke-width="2" />
              <path d="M21 21l-4.3-4.3" stroke-width="2" />
            </svg>
            <input
              v-model.trim="q"
              type="text"
              placeholder="Tìm đề theo tên/khoá…"
              class="w-full bg-transparent outline-none text-sm sm:text-base"
              @input="debouncedFetch"
            />
          </label>
        </div>

        <!-- Filters -->
        <div class="grid grid-cols-2 gap-2">
          <!-- Status -->
          <div class="relative">
            <select
              v-model="status"
              class="select-base"
              @change="fetchList(1)"
            >
              <option value="">Tất cả trạng thái</option>
              <option value="published">Đã phát hành</option>
              <option value="draft">Nháp</option>
            </select>
            <span class="select-chevron" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 111.04 1.08l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.31a.75.75 0 01.02-1.1z" clip-rule="evenodd"/>
              </svg>
            </span>
          </div>

          <!-- Sort -->
          <div class="relative">
            <select
              v-model="sort"
              class="select-base"
              @change="fetchList(1)"
            >
              <option value="updated">Mới cập nhật</option>
              <option value="title">A → Z</option>
              <option value="subs">Bài nộp nhiều</option>
            </select>
            <span class="select-chevron" aria-hidden="true">
              <svg viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 111.04 1.08l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.31a.75.75 0 01.02-1.1z" clip-rule="evenodd"/>
              </svg>
            </span>
          </div>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="grid grid-cols-1 gap-3 sm:gap-4">
        <div
          v-for="i in pageSize"
          :key="'skel-'+i"
          class="flex items-center gap-3 sm:gap-4 rounded-2xl border border-slate-200 bg-white p-3 sm:p-4"
        >
          <div class="h-12 w-12 sm:h-16 sm:w-16 rounded-xl bg-slate-200 animate-pulse"></div>
          <div class="min-w-0 flex-1">
            <div class="h-4 w-44 sm:w-56 rounded bg-slate-200 animate-pulse mb-2"></div>
            <div class="h-3 w-60 sm:w-80 rounded bg-slate-100 animate-pulse"></div>
          </div>
          <div class="h-8 w-20 sm:w-24 rounded bg-slate-100 animate-pulse"></div>
        </div>
      </div>

      <!-- List -->
      <div v-else-if="items.length" class="grid grid-cols-1 gap-3 sm:gap-4">
        <article
          v-for="e in items"
          :key="e.id"
          class="flex flex-wrap items-center gap-3 sm:gap-4 rounded-2xl border border-slate-200 bg-white p-3 sm:p-4 hover:shadow-sm transition-shadow"
        >
          <div class="grid h-12 w-12 sm:h-16 sm:w-16 place-items-center rounded-xl bg-slate-100 text-base sm:text-lg font-semibold text-slate-600">
            {{ e.totalQuestions }}
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-2">
              <h3 class="truncate font-semibold text-slate-900">{{ e.title }}</h3>
              <span
                class="rounded-full border px-2 py-0.5 text-xs"
                :class="e.status==='published'
                         ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                         : 'bg-amber-50 text-amber-700 border-amber-200'"
              >
                {{ e.status === 'published' ? 'Đã phát hành' : 'Nháp' }}
              </span>
            </div>
            <div class="mt-1 text-xs sm:text-sm text-slate-500">
              Khoá: <span class="font-medium text-slate-700">{{ e.course }}</span> ·
              {{ e.durationMin }} phút · {{ e.submissions }} bài nộp ·
              Điểm TB {{ e.avgScore }} · Cập nhật {{ e.updatedAt }}
            </div>
          </div>

          <div class="flex shrink-0 gap-2 w-full sm:w-auto">
            <button
              class="flex-1 sm:flex-none rounded-xl border px-3 py-2 text-sm hover:bg-slate-50 active:bg-slate-100"
              @click="openDetail(e.id)"
            >
              Chi tiết
            </button>
            <button
              class="flex-1 sm:flex-none rounded-xl border px-3 py-2 text-sm hover:bg-slate-50 active:bg-slate-100"
              @click="openGrading(e.id)"
            >
              Chấm
            </button>
          </div>
        </article>
      </div>

      <p v-else class="mt-10 text-center text-slate-500">Không có đề phù hợp.</p>

      <!-- Pager -->
      <div v-if="!loading && totalPages > 1" class="mt-6">
        <!-- Compact pager for small screens -->
        <div v-if="isCompact" class="flex items-center justify-center gap-2">
          <button
            class="rounded-xl border px-3 py-2 text-sm disabled:opacity-50"
            :disabled="page<=1"
            @click="fetchList(page-1)"
            aria-label="Trang trước"
          >
            ‹
          </button>
          <span class="text-sm text-slate-600">Trang {{ page }} / {{ totalPages }}</span>
          <button
            class="rounded-xl border px-3 py-2 text-sm disabled:opacity-50"
            :disabled="page>=totalPages"
            @click="fetchList(page+1)"
            aria-label="Trang sau"
          >
            ›
          </button>
        </div>

        <!-- Full pager for medium+ screens -->
        <div v-else class="flex items-center justify-center gap-2">
          <button class="rounded-xl border px-3 py-2 text-sm disabled:opacity-50" :disabled="page<=1" @click="fetchList(page-1)">‹</button>
          <div class="flex max-w-full overflow-x-auto whitespace-nowrap rounded-xl">
            <button
              v-for="p in pagesToShow"
              :key="p.key"
              class="mx-0.5 rounded-xl border px-3 py-2 text-sm"
              :class="{ 'bg-sky-600 text-white border-sky-600': p.num===page, 'opacity-70 cursor-default': p.sep }"
              :disabled="p.sep"
              @click="!p.sep && fetchList(p.num!)"
            >
              {{ p.text }}
            </button>
          </div>
          <button class="rounded-xl border px-3 py-2 text-sm disabled:opacity-50" :disabled="page>=totalPages" @click="fetchList(page+1)">›</button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { useRouter } from 'vue-router'

/** ===== Types ===== */
type ExamStatus = 'published' | 'draft'
type ExamRow = {
  id: number
  title: string
  course: string
  status: ExamStatus
  totalQuestions: number
  durationMin: number
  submissions: number
  avgScore: number
  updatedAt: string
}

/** ===== Router ===== */
const router = useRouter()

/** ===== State (filters + paging) ===== */
const q = ref('')
const status = ref<'' | ExamStatus>('')        // '' = tất cả
const sort = ref<'updated' | 'title' | 'subs'>('updated')

const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const loading = ref(true)
const items = ref<ExamRow[]>([])

/** ===== Responsive helpers ===== */
const isCompact = ref(false)
function updateCompactFlag() {
  isCompact.value = window.innerWidth < 640
}

/** ===== Service adapter (không sửa service) ===== */
type ServiceList = (params?: { level?: any; q?: string }) => Promise<any[]>
let serviceList: ServiceList | undefined

async function tryInitService() {
  try {
    const mod = await import('@/services/exam.service')
    if (mod?.examService?.list) {
      serviceList = mod.examService.list as ServiceList
    }
  } catch {
    // giữ fallback mock
  }
}

/** Map ExamSummary(service) -> ExamRow(component) */
function mapSummaryToRow(s: any): ExamRow {
  const durMin = Math.max(1, Math.round((Number(s.durationSec) || 0) / 60))
  const st: ExamStatus = s.status === 'published' ? 'published' : 'draft'
  const id = Number(s.id)
  return {
    id,
    title: String(s.title || `Đề #${id}`),
    course: String(s.level || '—'),
    status: st,
    totalQuestions: Number(s.questionsCount || 0),
    durationMin: durMin,
    submissions: (id * 13) % 120,
    avgScore: (60 + (id % 40)) / 10,
    updatedAt: new Date(s.updatedAt || Date.now()).toLocaleString(),
  }
}

/** ===== Mock (ổn định) ===== */
function mockPool(): ExamRow[] {
  return Array.from({ length: 42 }).map((_, i) => {
    const id = i + 1
    const published = id % 3 !== 1
    return {
      id,
      title: `Đề kiểm tra #${id}`,
      course: `Khoá ${(id % 6) + 1}`,
      status: published ? 'published' : 'draft',
      totalQuestions: 20 + (id % 15),
      durationMin: 20 + (id % 6) * 5,
      submissions: (id * 13) % 120,
      avgScore: (60 + (id % 40)) / 10,
      updatedAt: new Date(Date.now() - id * 36e5).toLocaleString()
    }
  })
}

/** Lọc + sắp xếp + phân trang (dùng chung) */
function applyViewParams(
  all: ExamRow[],
  params: { q?: string; status?: '' | ExamStatus; sort?: 'updated'|'title'|'subs'; page?: number; pageSize?: number }
) {
  let filtered = all.slice()

  if (params.q) {
    const key = params.q.toLowerCase()
    filtered = filtered.filter(e =>
      e.title.toLowerCase().includes(key) || e.course.toLowerCase().includes(key)
    )
  }
  if (params.status) filtered = filtered.filter(e => e.status === params.status)

  if (params.sort === 'title') filtered.sort((a,b)=>a.title.localeCompare(b.title))
  else if (params.sort === 'subs') filtered.sort((a,b)=>b.submissions - a.submissions)

  const pg = params.page ?? 1
  const size = params.pageSize ?? 10
  const start = (pg - 1) * size
  return {
    items: filtered.slice(start, start + size),
    total: filtered.length
  }
}

/** ===== Fetch (token chống race) ===== */
let fetchToken = 0
async function fetchList(p = page.value) {
  const token = ++fetchToken
  loading.value = true
  page.value = p
  try {
    let pool: ExamRow[] = []
    if (serviceList) {
      const summaries = await (serviceList(q.value ? { q: q.value } : undefined))
      if (token !== fetchToken) return
      pool = (summaries || []).map(mapSummaryToRow)
    } else {
      pool = mockPool()
    }

    const res = applyViewParams(pool, {
      q: q.value || undefined,
      status: status.value,
      sort: sort.value,
      page: page.value,
      pageSize: pageSize.value
    })
    if (token !== fetchToken) return
    items.value = res.items
    total.value = res.total
  } finally {
    if (token === fetchToken) loading.value = false
  }
}

/** Debounce search */
let debounceTimer: number | null = null
function debouncedFetch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(() => fetchList(1), 250) as unknown as number
}

/** Pager helpers */
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
const pagesToShow = computed(() => {
  const max = totalPages.value
  const cur = page.value
  const windowSize = 7
  const arr: { key: string; num?: number; text: string; sep?: boolean }[] = []
  const push = (n: number) => arr.push({ key: 'p' + n, num: n, text: String(n) })
  const sep = (k: string) => arr.push({ key: k, text: '…', sep: true })

  if (max <= windowSize + 2) {
    for (let i = 1; i <= max; i++) push(i)
  } else {
    push(1)
    const start = Math.max(2, cur - 2)
    const end   = Math.min(max - 1, cur + 2)
    if (start > 2) sep('s')
    for (let i = start; i <= end; i++) push(i)
    if (end < max - 1) sep('e')
    push(max)
  }
  return arr
})

/** Actions */
function createExam()           { router.push({ path: '/teacher/exams/new' }) }
function openDetail(id: number) { router.push({ path: `/teacher/exams/${id}` }) }
function openGrading(id: number){ router.push({ path: `/teacher/exams/${id}/grading` }) }

/** Mount */
function onResize() { updateCompactFlag() }
onMounted(async () => {
  updateCompactFlag()
  window.addEventListener('resize', onResize, { passive: true })
  await tryInitService()
  fetchList(1)
})

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
  window.removeEventListener('resize', onResize)
})
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }

/* ===== Custom select (fix icon & height cross-browser) ===== */
.select-base{
  @apply w-full rounded-2xl border border-slate-200 bg-white px-3 pr-8 py-2 text-sm leading-6 outline-none;
  @apply focus:ring-2 focus:ring-sky-500/30 focus:border-sky-400;
  appearance: none;          /* Chrome/Safari */
  -webkit-appearance: none;  /* iOS Safari */
  -moz-appearance: none;     /* Firefox */
  background-image: none;
}
.select-chevron{
  @apply pointer-events-none absolute inset-y-0 right-3 flex items-center text-slate-400;
}

/* Improve momentum scroll for pager row */
[role="navigation"] { -webkit-overflow-scrolling: touch; }
</style>
