<!-- src/pages/teacher/exams/ExamReports.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-6 py-8 md:px-10">
      <!-- Header -->
      <div class="mb-5 flex items-center justify-between gap-3">
        <h1 class="text-2xl font-semibold">Báo cáo bài kiểm tra</h1>
        <button class="rounded-xl border px-4 py-2 hover:bg-slate-50" @click="refresh">Làm mới</button>
      </div>

      <!-- Tools -->
      <div class="mb-6 grid grid-cols-1 gap-3 md:grid-cols-3">
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
              placeholder="Tìm theo tên/khoá…"
              class="w-full bg-transparent outline-none"
              @input="debouncedFetch"
            />
          </div>
        </div>

        <!-- Filters (giữ nguyên khối grid, cho select span đủ 2 cột để full-width) -->
        <div class="grid grid-cols-2 gap-2">
          <select
            v-model="sort"
            class="col-span-2 w-full rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm"
            @change="fetchList(1)"
          >
            <option value="updated">Mới cập nhật</option>
            <option value="title">A → Z</option>
            <option value="subs">Bài nộp nhiều</option>
            <option value="avg">Điểm TB cao</option>
            <option value="pass">Tỉ lệ đạt cao</option>
          </select>
        </div>

        <!-- Date range -->
        <div class="md:col-span-3 grid grid-cols-1 gap-2 sm:grid-cols-3">
          <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2">
            <label class="block text-xs text-slate-500 mb-1">Từ ngày</label>
            <input v-model="from" type="date" class="w-full bg-transparent outline-none text-sm" @change="fetchList(1)" />
          </div>
          <div class="rounded-2xl border border-slate-200 bg-white px-3 py-2">
            <label class="block text-xs text-slate-500 mb-1">Đến ngày</label>
            <input v-model="to" type="date" class="w-full bg-transparent outline-none text-sm" @change="fetchList(1)" />
          </div>
          <div class="flex items-end">
            <button class="w-full rounded-xl border px-3 py-2 text-sm hover:bg-slate-50" @click="clearDates">Xoá lọc ngày</button>
          </div>
        </div>
      </div>

      <!-- KPIs -->
      <div class="mb-6 grid grid-cols-2 gap-3 sm:grid-cols-4">
        <div class="rounded-2xl bg-slate-100 p-4">
          <div class="text-2xl font-semibold">{{ kpi.total }}</div>
          <div class="text-xs text-slate-500">Tổng đề</div>
        </div>
        <div class="rounded-2xl bg-slate-100 p-4">
          <div class="text-2xl font-semibold">{{ kpi.subs }}</div>
          <div class="text-xs text-slate-500">Tổng bài nộp</div>
        </div>
        <div class="rounded-2xl bg-slate-100 p-4">
          <div class="text-2xl font-semibold">{{ kpi.avg }}</div>
          <div class="text-xs text-slate-500">Điểm trung bình</div>
        </div>
        <div class="rounded-2xl bg-slate-100 p-4">
          <div class="text-2xl font-semibold">{{ kpi.pass }}%</div>
          <div class="text-xs text-slate-500">Tỉ lệ đạt</div>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="grid grid-cols-1 gap-4">
        <div v-for="i in pageSize" :key="'skel-'+i" class="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4">
          <div class="h-16 w-16 rounded-xl bg-slate-200 animate-pulse"></div>
          <div class="min-w-0 flex-1">
            <div class="h-4 w-56 rounded bg-slate-200 animate-pulse mb-2"></div>
            <div class="h-3 w-80 rounded bg-slate-100 animate-pulse"></div>
          </div>
          <div class="h-8 w-20 rounded bg-slate-100 animate-pulse"></div>
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
              Điểm TB {{ e.avgScore }} · Tỉ lệ đạt {{ e.passRate }}% ·
              Cập nhật {{ e.updatedAtDisplay }}
            </div>
          </div>

          <div class="flex shrink-0 gap-2">
            <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50" @click="openDetail(e.id)">Chi tiết</button>
            <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50" @click="openGrading(e.id)">Chấm</button>
          </div>
        </article>
      </div>

      <p v-else class="mt-10 text-center text-slate-500">Không có dữ liệu phù hợp.</p>

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
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

/** ===== Types ===== */
type ExamStatus = 'published' | 'draft'
type ReportRow = {
  id: number
  title: string
  course: string
  status: ExamStatus
  totalQuestions: number
  durationMin: number
  submissions: number
  avgScore: number
  passRate: number
  updatedTs: number           // số ms để sort/lọc chuẩn
  updatedAtDisplay: string    // chuỗi hiển thị
}

/** ===== Router ===== */
const router = useRouter()

/** ===== Filters & paging ===== */
const q = ref('')
const status = ref<'' | ExamStatus>('')        // '' = tất cả
const sort = ref<'updated' | 'title' | 'subs' | 'avg' | 'pass'>('updated')
const from = ref<string>('')                   // yyyy-MM-dd
const to = ref<string>('')

const page = ref(1)
const pageSize = ref(10)
const total = ref(0)

const loading = ref(true)
const items = ref<ReportRow[]>([])

/** ===== Service adapter (lazy) ===== */
type ServiceList = (params?: { q?: string }) => Promise<any[]>
let serviceList: ServiceList | undefined

async function tryInitService() {
  try {
    const mod = await import('@/services/exam.service')
    if (mod?.examService?.list) {
      serviceList = mod.examService.list as ServiceList
    }
  } catch {
    // fallback to mock
  }
}

/** ===== Mapping helpers ===== */
function mapFromService(s: any): ReportRow {
  const id = Number(s.id)
  const st: ExamStatus = s.status === 'published' ? 'published' : 'draft'
  const durationMin = Math.max(1, Math.round((Number(s.durationSec) || 1800) / 60))
  const totalQuestions = Number(s.questionsCount ?? (20 + (id % 15)))
  const course = String(s.level || `Khoá ${((id % 6) + 1)}`)
  const submissions = (id * 13) % 160
  const avgScore = Number((6 + (id % 4) + (id % 3) * 0.5).toFixed(1))
  const passRate = Math.min(100, 50 + (id % 50))
  const updatedTs = s.updatedAt ? Date.parse(s.updatedAt) : (Date.now() - id * 36e5)
  const updatedAtDisplay = new Date(updatedTs).toLocaleString()
  return { id, title: String(s.title || `Đề #${id}`), course, status: st, totalQuestions, durationMin, submissions, avgScore, passRate, updatedTs, updatedAtDisplay }
}

function mockRows(): ReportRow[] {
  return Array.from({ length: 42 }).map((_, i) => {
    const id = i + 1
    const published = id % 3 !== 1
    const updatedTs = Date.now() - id * 36e5
    return {
      id,
      title: `Đề kiểm tra #${id}`,
      course: `Khoá ${((id % 6) + 1)}`,
      status: published ? 'published' : 'draft',
      totalQuestions: 20 + (id % 15),
      durationMin: 20 + (id % 6) * 5,
      submissions: (id * 13) % 160,
      avgScore: Number((6 + (id % 4) + (id % 3) * 0.5).toFixed(1)),
      passRate: Math.min(100, 50 + (id % 50)),
      updatedTs,
      updatedAtDisplay: new Date(updatedTs).toLocaleString()
    }
  })
}

/** ===== Fetch (chống race) ===== */
let fetchToken = 0
async function fetchList(p = page.value) {
  const token = ++fetchToken
  loading.value = true
  page.value = p
  try {
    // Pool dữ liệu
    let pool: ReportRow[] = []
    if (serviceList) {
      const summaries = await serviceList(q.value ? { q: q.value } : undefined)
      if (token !== fetchToken) return
      pool = (summaries || []).map(mapFromService)
    } else {
      pool = mockRows()
    }

    // Lọc text
    const key = q.value.toLowerCase()
    let filtered = key
      ? pool.filter(e => [e.title, e.course].some(x => String(x).toLowerCase().includes(key)))
      : pool

    // Lọc trạng thái
    if (status.value) filtered = filtered.filter(e => e.status === status.value)

    // Lọc ngày theo updatedTs
    const fromTime = from.value ? Date.parse(from.value + 'T00:00:00') : 0
    const toTime = to.value ? Date.parse(to.value + 'T23:59:59') : Number.MAX_SAFE_INTEGER
    filtered = filtered.filter(e => e.updatedTs >= fromTime && e.updatedTs <= toTime)

    // Sort
    if (sort.value === 'title') filtered.sort((a, b) => a.title.localeCompare(b.title))
    else if (sort.value === 'subs') filtered.sort((a, b) => b.submissions - a.submissions)
    else if (sort.value === 'avg')  filtered.sort((a, b) => b.avgScore - a.avgScore)
    else if (sort.value === 'pass') filtered.sort((a, b) => b.passRate - a.passRate)
    else /* updated */              filtered.sort((a, b) => b.updatedTs - a.updatedTs)

    // Paging
    total.value = filtered.length
    const start = (page.value - 1) * pageSize.value
    items.value = filtered.slice(start, start + pageSize.value)
  } finally {
    if (token === fetchToken) loading.value = false
  }
}

function refresh() { fetchList(page.value) }

/** Debounce search */
let timer: number | null = null
function debouncedFetch() {
  if (timer) clearTimeout(timer)
  timer = window.setTimeout(() => fetchList(1), 250) as unknown as number
}

/** KPIs (tính theo trang hiện tại để mượt) */
const kpi = computed(() => {
  const src = items.value
  const totalExams = total.value
  const subs = src.reduce((s, e) => s + e.submissions, 0)
  const avg = src.length ? (src.reduce((s, e) => s + e.avgScore, 0) / src.length).toFixed(1) : '0.0'
  const pass = src.length ? Math.round(src.reduce((s, e) => s + e.passRate, 0) / src.length) : 0
  return { total: totalExams, subs, avg, pass }
})

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
    const end = Math.min(max - 1, cur + 2)
    if (start > 2) sep('s')
    for (let i = start; i <= end; i++) push(i)
    if (end < max - 1) sep('e')
    push(max)
  }
  return arr
})

/** Actions */
function openDetail(id: number)  { router.push({ path: `/teacher/exams/${id}` }) }
function openGrading(id: number) { router.push({ path: `/teacher/exams/${id}/grading` }) }
function clearDates() { from.value = ''; to.value = ''; fetchList(1) }

/** Mount */
onMounted(async () => {
  await tryInitService()
  fetchList(1)
})

onBeforeUnmount(() => {
  if (timer) clearTimeout(timer)
})
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
</style>
