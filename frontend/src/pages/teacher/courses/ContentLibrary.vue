<!-- src/pages/teacher/courses/ContentLibrary.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="mx-auto w-full max-w-screen-2xl px-6 py-8 md:px-10">
      <!-- Header -->
      <div class="mb-5 flex items-center justify-between gap-3">
        <div class="flex items-center gap-3">
          <button class="rounded-xl border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50" @click="goBack">
            ← Quay lại
          </button>
          <h1 class="text-2xl font-semibold">Thư viện nội dung</h1>
        </div>
        <div v-if="courseId" class="text-sm text-slate-600">
          Đang thêm vào khoá: <b>#{{ courseId }}</b>
        </div>
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
              placeholder="Tìm theo tiêu đề / môn…"
              class="w-full bg-transparent outline-none"
              @input="debouncedFetch"
            />
          </div>
        </div>

        <!-- Filters -->
        <div class="grid grid-cols-2 gap-2">
          <select v-model="gradeBand" class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="fetchList(1)">
            <option value="">Tất cả khối</option>
            <option value="Khối 1–2">Khối 1–2</option>
            <option value="Khối 3–5">Khối 3–5</option>
          </select>
          <select v-model="ctype" class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm" @change="fetchList(1)">
            <option value="">Tất cả loại</option>
            <option value="video">Video</option>
            <option value="pdf">PDF</option>
            <option value="doc">Tài liệu</option>
            <option value="quiz">Quiz</option>
          </select>
        </div>
      </div>

      <!-- List (loading) -->
      <div v-if="loading" class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <div v-for="i in pageSize" :key="'skel-'+i" class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="mb-2 h-12 w-12 animate-pulse rounded-xl bg-slate-200"></div>
          <div class="mb-2 h-4 w-3/4 animate-pulse rounded bg-slate-200"></div>
          <div class="h-3 w-2/3 animate-pulse rounded bg-slate-100"></div>
        </div>
      </div>

      <!-- List -->
      <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <article
          v-for="item in items"
          :key="item.id"
          class="flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-4 hover:shadow-sm"
        >
          <div class="grid h-12 w-12 shrink-0 place-items-center rounded-xl bg-slate-100 text-sm font-semibold text-slate-600">
            {{ item.type.toUpperCase() }}
          </div>

          <div class="min-w-0 flex-1">
            <div class="flex items-center gap-2">
              <h3 class="truncate font-semibold">{{ item.title }}</h3>
              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs">{{ subjectLabel(item.subject) }}</span>
              <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs">{{ item.gradeBand }}</span>
            </div>
            <div class="mt-1 text-xs text-slate-500">
              Cập nhật {{ item.updatedAt }}
              <template v-if="item.meta?.duration"> · {{ item.meta.duration }}</template>
              <template v-if="item.meta?.size"> · {{ item.meta.size }}</template>
              <template v-if="item.meta?.questions"> · {{ item.meta.questions }} câu</template>
            </div>
          </div>

          <div class="shrink-0">
            <button
              class="rounded-xl border border-slate-300 px-3 py-2 text-sm font-semibold hover:bg-slate-50"
              @click="addToCourse(item.id)"
            >
              Thêm
            </button>
          </div>
        </article>
      </div>

      <p v-if="!loading && !items.length" class="mt-10 text-center text-slate-500">
        Không có nội dung phù hợp.
      </p>

      <!-- Pager -->
      <div v-if="totalPages > 1" class="mt-6 flex items-center justify-center gap-2">
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
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/* ==== TYPES ==== */
type Subject = 'math' | 'vietnamese' | 'english' | 'science' | 'history'
type Ctype = 'video' | 'pdf' | 'doc' | 'quiz'
type GradeBand = 'Khối 1–2' | 'Khối 3–5'
type ContentItem = {
  id: number
  title: string
  subject: Subject
  type: Ctype
  gradeBand: GradeBand
  updatedAt: string
  meta?: { duration?: string; size?: string; questions?: number }
}
type ListParams = {
  q?: string
  gradeBand?: GradeBand | ''
  type?: Ctype | ''
  page?: number
  pageSize?: number
}
type ListResult = { items: ContentItem[]; total: number }
type ListFn = (p: ListParams) => Promise<ListResult>

/* ==== ROUTER ==== */
const router = useRouter()
const route = useRoute()
const courseId = route.query.courseId ? String(route.query.courseId) : ''

/* ==== STATE ==== */
const q = ref('')
const gradeBand = ref<'' | GradeBand>('')
const ctype = ref<'' | Ctype>('')
const loading = ref(true)
const items = ref<ContentItem[]>([])

/* Pagination */
const page = ref(1)
const pageSize = ref(12)
const total = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

/* Dịch tên môn */
const subjectLabel = (s: Subject) =>
  s === 'math' ? 'Toán' :
  s === 'vietnamese' ? 'Tiếng Việt' :
  s === 'english' ? 'Tiếng Anh' :
  s === 'science' ? 'Khoa học' : 'Lịch sử'

/* Debounce search */
let debounceTimer: number | null = null
function debouncedFetch() {
  if (debounceTimer) clearTimeout(debounceTimer)
  debounceTimer = window.setTimeout(() => fetchList(1), 250) as unknown as number
}

/* ==== Lazy import service (an toàn kiểu) ==== */
let contentServiceList: ListFn | null = null

async function ensureServiceLoaded() {
  if (contentServiceList !== null) return
  try {
    const mod: unknown = await import('@/services/course.service')
    if (
      typeof mod === 'object' && mod !== null &&
      'contentService' in (mod as Record<string, unknown>) &&
      typeof (mod as any).contentService?.list === 'function'
    ) {
      contentServiceList = ((mod as any).contentService.list) as ListFn
    } else {
      contentServiceList = null // không đúng shape → dùng mock
    }
  } catch {
    contentServiceList = null // import fail → dùng mock
  }
}

/* ==== MOCK (fallback) ==== */
function mockList(params: ListParams): Promise<ListResult> {
  const size = params.pageSize ?? 12
  const pg = params.page ?? 1
  const all: ContentItem[] = Array.from({ length: 60 }).map((_, i) => {
    const id = i + 1
    const subj = (['math','vietnamese','english','science','history'] as Subject[])[id % 5]
    const ty = (['video','pdf','doc','quiz'] as Ctype[])[id % 4]
    const band: GradeBand = id % 2 ? 'Khối 3–5' : 'Khối 1–2'
    const meta: ContentItem['meta'] = {}
    if (ty === 'video') meta.duration = `${6 + (id % 10)} phút`
    if (ty === 'pdf' || ty === 'doc') meta.size = `${2 + (id % 8)} MB`
    if (ty === 'quiz') meta.questions = 10 + (id % 15)
    return {
      id,
      title: `Nội dung #${id} - ${subjectLabel(subj)}`,
      subject: subj,
      type: ty,
      gradeBand: band,
      updatedAt: new Date(Date.now() - id * 864e5).toLocaleDateString(),
      meta
    }
  })

  let filtered = all
  if (params.q) {
    const key = params.q.toLowerCase()
    filtered = filtered.filter(i =>
      i.title.toLowerCase().includes(key) ||
      subjectLabel(i.subject).toLowerCase().includes(key)
    )
  }
  if (params.gradeBand) filtered = filtered.filter(i => i.gradeBand === params.gradeBand)
  if (params.type) filtered = filtered.filter(i => i.type === params.type)

  const start = (pg - 1) * size
  return Promise.resolve({
    items: filtered.slice(start, start + size),
    total: filtered.length
  })
}

/* ==== FETCH ==== */
async function fetchList(p = page.value) {
  loading.value = true
  page.value = p
  try {
    await ensureServiceLoaded()

    const params: ListParams = {
      q: q.value || undefined,
      gradeBand: gradeBand.value || undefined,
      type: ctype.value || undefined,
      page: page.value,
      pageSize: pageSize.value
    }

    const res = contentServiceList
      ? await contentServiceList(params)
      : await mockList(params)

    items.value = res.items
    total.value = res.total
  } catch (e) {
    console.error(e)
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/* ==== Pager window ==== */
const pagesToShow = computed(() => {
  const max = totalPages.value
  const cur = page.value
  const windowSize = 7
  const arr: { key: string; num?: number; text: string; sep?: boolean }[] = []
  const push = (n: number) => arr.push({ key: 'p' + n, num: n, text: String(n) })
  const sep  = (k: string) => arr.push({ key: k, text: '…', sep: true })

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

/* ==== Actions ==== */
function addToCourse(contentId: number) {
  if (courseId) {
    router.push({ path: `/teacher/courses/${courseId}/edit`, query: { add: String(contentId) } })
  } else {
    alert(`Đã chọn nội dung #${contentId}. Hãy mở từ khoá học để thêm trực tiếp.`)
  }
}
function goBack() {
  if (courseId) router.push({ path: `/teacher/courses/${courseId}` })
  else router.push({ path: '/teacher/courses' })
}

onMounted(() => fetchList(1))
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
</style>
