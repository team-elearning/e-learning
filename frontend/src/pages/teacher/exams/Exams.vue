<!-- src/pages/teacher/exams/Exams.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-6 py-8 md:px-10">
      <!-- Header -->
      <div class="mb-5 flex items-center justify-between gap-3">
        <h1 class="text-2xl font-semibold">Bài kiểm tra</h1>
        <button
          class="rounded-xl bg-sky-600 px-4 py-2 font-semibold text-white hover:bg-sky-700"
          @click="createExam"
        >
          + Tạo bài kiểm tra
        </button>
      </div>

      <!-- Tools -->
      <div class="mb-5 grid grid-cols-1 gap-3 md:grid-cols-3">
        <!-- Search -->
        <div class="md:col-span-2">
          <div class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor">
              <circle cx="11" cy="11" r="8" stroke-width="2" />
              <path d="M21 21l-4.3-4.3" stroke-width="2" />
            </svg>
            <input
              v-model.trim="q"
              type="text"
              placeholder="Tìm đề theo tên/khoá…"
              class="w-full bg-transparent outline-none"
              @input="debouncedFetch"
            />
          </div>
        </div>

        <!-- Filters -->
        <div class="grid grid-cols-2 gap-2">
          <select v-model="status" class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="fetchList(1)">
            <option value="">Tất cả trạng thái</option>
            <option value="published">Đã phát hành</option>
            <option value="draft">Nháp</option>
          </select>
          <select v-model="sort" class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="fetchList(1)">
            <option value="updated">Mới cập nhật</option>
            <option value="title">A → Z</option>
            <option value="subs">Bài nộp nhiều</option>
          </select>
        </div>
      </div>

      <!-- Loading skeleton -->
      <div v-if="loading" class="grid grid-cols-1 gap-4">
        <div v-for="i in pageSize" :key="'skel-'+i" class="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4">
          <div class="h-16 w-16 rounded-xl bg-slate-200 animate-pulse"></div>
          <div class="min-w-0 flex-1">
            <div class="h-4 w-56 rounded bg-slate-200 animate-pulse mb-2"></div>
            <div class="h-3 w-80 rounded bg-slate-100 animate-pulse"></div>
          </div>
          <div class="h-8 w-24 rounded bg-slate-100 animate-pulse"></div>
        </div>
      </div>

      <!-- List -->
      <div v-else-if="items.length" class="grid grid-cols-1 gap-4">
        <article
          v-for="e in items"
          :key="e.id"
          class="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 hover:shadow-sm"
        >
          <div class="grid h-16 w-16 place-items-center rounded-xl bg-slate-100 text-lg font-semibold text-slate-600">
            {{ e.totalQuestions }}
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <h3 class="truncate font-semibold">{{ e.title }}</h3>
              <span
                class="rounded-full border px-2 py-0.5 text-xs"
                :class="e.status==='published'
                         ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                         : 'bg-amber-50 text-amber-700 border-amber-200'"
              >
                {{ e.status === 'published' ? 'Đã phát hành' : 'Nháp' }}
              </span>
            </div>
            <div class="mt-1 text-sm text-slate-500">
              Khoá: <span class="font-medium text-slate-700">{{ e.course }}</span> ·
              {{ e.durationMin }} phút · {{ e.submissions }} bài nộp ·
              Điểm TB {{ e.avgScore }} · Cập nhật {{ e.updatedAt }}
            </div>
          </div>

          <div class="flex shrink-0 gap-2">
            <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50" @click="openDetail(e.id)">
              Chi tiết
            </button>
            <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50" @click="openGrading(e.id)">
              Chấm
            </button>
          </div>
        </article>
      </div>

      <p v-else class="mt-10 text-center text-slate-500">Không có đề phù hợp.</p>

      <!-- Pager -->
      <div v-if="!loading && totalPages > 1" class="mt-6 flex items-center justify-center gap-2">
        <button class="rounded-xl border px-3 py-2 text-sm" :disabled="page<=1" @click="fetchList(page-1)">‹</button>
        <button
          v-for="p in pagesToShow"
          :key="p.key"
          class="rounded-xl border px-3 py-2 text-sm"
          :class="{ 'bg-sky-600 text-white border-sky-600': p.num===page, 'opacity-70': p.sep }"
          :disabled="p.sep"
          @click="!p.sep && fetchList(p.num!)"
        >
          {{ p.text }}
        </button>
        <button class="rounded-xl border px-3 py-2 text-sm" :disabled="page>=totalPages" @click="fetchList(page+1)">›</button>
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

/** ===== Service adapter (không sửa service) =====
 * Nếu có '@/services/exam.service' (list: (params?: {level?:..., q?:...}) => ExamSummary[] )
 * thì gọi và CHUYỂN ĐỔI sang ExamRow + tự lọc/sort/phân trang ở client.
 */
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
  // exam.service trả: { id, title, level, durationSec, passScore, questionsCount, status, updatedAt }
  const durMin = Math.max(1, Math.round((Number(s.durationSec) || 0) / 60))
  const st: ExamStatus = s.status === 'published' ? 'published' : 'draft' // 'archived' coi như draft để lọc/hiển thị
  const id = Number(s.id)
  return {
    id,
    title: String(s.title || `Đề #${id}`),
    course: String(s.level || '—'),         // không có course trong service → hiển thị level để có ngữ cảnh
    status: st,
    totalQuestions: Number(s.questionsCount || 0),
    durationMin: durMin,
    submissions: (id * 13) % 120,           // mock nhẹ cho UI
    avgScore: (60 + (id % 40)) / 10,        // 6.0 .. 9.9
    updatedAt: new Date(s.updatedAt || Date.now()).toLocaleString(),
  }
}

/** ===== Mock (nhẹ, ổn định) ===== */
function mockPool(): ExamRow[] {
  return Array.from({ length: 42 }).map((_, i) => {
    const id = i + 1
    const published = id % 3 !== 1
    return {
      id,
      title: `Đề kiểm tra #${id}`,
      course: `Khoá ${((id % 6) + 1)}`,
      status: published ? 'published' : 'draft',
      totalQuestions: 20 + (id % 15),
      durationMin: 20 + (id % 6) * 5,
      submissions: (id * 13) % 120,
      avgScore: (60 + (id % 40)) / 10,      // 6.0 .. 9.9
      updatedAt: new Date(Date.now() - id * 36e5).toLocaleString()
    }
  })
}

/** Lọc + sắp xếp + phân trang (dùng chung cho service/mock) */
function applyViewParams(all: ExamRow[], params: {
  q?: string; status?: '' | ExamStatus; sort?: 'updated'|'title'|'subs'; page?: number; pageSize?: number
}) {
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
  // 'updated' giữ thứ tự có sẵn

  const pg = params.page ?? 1
  const size = params.pageSize ?? 10
  const start = (pg - 1) * size
  return {
    items: filtered.slice(start, start + size),
    total: filtered.length
  }
}

/** ===== Fetch (có token chống race) ===== */
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
function createExam()          { router.push({ path: '/teacher/exams/new' }) }
function openDetail(id: number){ router.push({ path: `/teacher/exams/${id}` }) }
function openGrading(id: number){ router.push({ path: `/teacher/exams/${id}/grading` }) }

/** Mount */
onMounted(async () => {
  await tryInitService()
  fetchList(1)
})

onBeforeUnmount(() => {
  if (debounceTimer) clearTimeout(debounceTimer)
})
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
</style>
