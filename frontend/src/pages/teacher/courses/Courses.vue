<!-- src/pages/teacher/courses/Courses.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <!-- Header -->
      <div class="mb-5 flex flex-col items-stretch justify-between gap-3 sm:flex-row sm:items-center">
        <h1 class="text-xl font-semibold sm:text-2xl">Khoá học</h1>
        <button
          class="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-2 font-semibold text-white hover:bg-sky-700"
          @click="createCourse"
        >
          + Tạo khoá học
        </button>
      </div>

      <!-- Tools -->
      <div class="mb-5 grid grid-cols-1 gap-3 md:grid-cols-3">
        <!-- Search -->
        <div class="md:col-span-2">
          <label class="sr-only">Tìm kiếm</label>
          <div class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" aria-hidden="true">
              <circle cx="11" cy="11" r="8" stroke-width="2" />
              <path d="M21 21l-4.3-4.3" stroke-width="2" />
            </svg>
            <input
              v-model.trim="q"
              type="text"
              placeholder="Tìm khoá học…"
              class="w-full bg-transparent outline-none placeholder:text-slate-400"
              @input="debouncedFetch()"
            />
          </div>
        </div>

        <!-- Filters -->
        <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <select v-model="status" @change="fetch()" class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm">
            <option value="all">Tất cả trạng thái</option>
            <option value="published">Đã xuất bản</option>
            <option value="draft">Nháp</option>
            <option value="archived">Lưu trữ</option>
          </select>
          <select v-model="sort" @change="fetch()" class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm">
            <option value="updated,descending">Mới cập nhật</option>
            <option value="title,ascending">A → Z</option>
            <option value="enrollments,descending">Học sinh nhiều</option>
          </select>
        </div>
      </div>

      <!-- List -->
      <div v-if="loading" class="grid grid-cols-1 gap-4">
        <div v-for="i in pageSize" :key="i" class="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center">
          <div class="h-40 w-full rounded-xl bg-slate-200 animate-pulse sm:h-20 sm:w-32" />
          <div class="min-w-0 flex-1 space-y-2">
            <div class="h-4 w-2/3 rounded bg-slate-200 animate-pulse" />
            <div class="h-3 w-1/2 rounded bg-slate-200 animate-pulse" />
          </div>
          <div class="h-10 w-full rounded bg-slate-200 animate-pulse sm:h-8 sm:w-24" />
        </div>
      </div>

      <div v-else class="grid grid-cols-1 gap-4">
        <article
          v-for="c in items"
          :key="String(c.id)"
          class="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 transition-shadow hover:shadow-sm sm:flex-row sm:items-center"
        >
          <!-- Thumbnail -->
          <img
            :src="c.thumbnail"
            :alt="c.title"
            class="h-40 w-full rounded-xl object-cover sm:h-20 sm:w-32 sm:shrink-0"
          />

          <!-- Content -->
          <div class="min-w-0 flex-1">
            <div class="flex flex-col gap-2 sm:flex-row sm:items-center sm:gap-3">
              <h3
                class="truncate font-semibold cursor-pointer hover:underline"
                @click="viewDetail(c.id)"
                :title="c.title"
              >
                {{ c.title }}
              </h3>
              <span class="w-max rounded-full border px-2 py-0.5 text-xs" :class="badgeClass(c.status)">
                {{ statusText(c.status) }}
              </span>
            </div>
            <div class="mt-1 text-sm text-slate-500">
              {{ c.lessonsCount }} bài học · {{ c.enrollments }} học sinh · Cập nhật {{ fmtDate(c.updatedAt) }}
            </div>
          </div>

          <!-- Actions -->
          <div class="grid grid-cols-3 gap-2 sm:flex sm:shrink-0">
            <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50 w-full sm:w-auto" @click="viewDetail(c.id)">
              Chi tiết
            </button>
            <button class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50 w-full sm:w-auto" @click="openLibrary(c.id)">
              Thư viện
            </button>
            <button
              class="inline-flex items-center justify-center rounded-xl bg-sky-600 px-3 py-2 font-semibold text-white hover:bg-sky-700 w-full sm:w-auto"
              @click="editCourse(c.id)"
            >
              Sửa
            </button>
          </div>
        </article>

        <p v-if="!items.length" class="mt-10 text-center text-slate-500">
          Không có khoá học phù hợp.
        </p>
      </div>

      <!-- Pager -->
      <div v-if="total > pageSize" class="mt-6 flex flex-wrap items-center justify-center gap-2">
        <button class="rounded-xl border px-3 py-1.5 text-sm disabled:opacity-50" :disabled="page<=1" @click="go(page-1)">‹</button>
        <span class="text-sm text-slate-600">Trang {{ page }} / {{ totalPages }}</span>
        <button class="rounded-xl border px-3 py-1.5 text-sm disabled:opacity-50" :disabled="page>=totalPages" @click="go(page+1)">›</button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { courseService, type CourseSummary, type CourseStatus } from '@/services/course.service'

const router = useRouter()

/* State */
const q = ref('')
const status = ref<'all' | CourseStatus>('all')
const sort = ref<'updated,descending' | 'title,ascending' | 'enrollments,descending'>('updated,descending')

const items = ref<CourseSummary[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(8)
const loading = ref(true)
const err = ref('')

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

/* Fetch */
async function fetch(p = page.value) {
  loading.value = true
  err.value = ''
  page.value = p
  try {
    const [sortBy, sortDir] = (sort.value as string).split(',') as any
    const params = {
      q: q.value || undefined,
      status: status.value === 'all' ? undefined : status.value,
      sortBy, sortDir,
      page: page.value,
      pageSize: pageSize.value
    }
    const res = await courseService.list(params)
    items.value = res.items
    total.value = res.total
  } catch (e: any) {
    err.value = e?.message || 'Không tải được danh sách khoá học.'
    items.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/* Debounce cho search */
let t: number | null = null
function debouncedFetch() {
  if (t) clearTimeout(t)
  t = window.setTimeout(() => fetch(1), 300) as unknown as number
}

/* Helpers */
function badgeClass(s: CourseStatus) {
  switch (s) {
    case 'published': return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    case 'draft':     return 'bg-amber-50 text-amber-700 border-amber-200'
    case 'archived':  return 'bg-slate-100 text-slate-700 border-slate-200'
    case 'pending_review': return 'bg-sky-50 text-sky-700 border-sky-200'
    case 'rejected':  return 'bg-rose-50 text-rose-700 border-rose-200'
  }
}
function statusText(s: CourseStatus) {
  return s === 'published' ? 'Đã xuất bản'
    : s === 'pending_review' ? 'Chờ duyệt'
    : s === 'draft' ? 'Nháp'
    : s === 'rejected' ? 'Từ chối'
    : 'Lưu trữ'
}
function fmtDate(iso?: string) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleString() } catch { return iso }
}

/* Pager */
function go(p: number) { fetch(p) }

/* Actions */
function createCourse() { router.push({ path: '/teacher/courses/new' }) }
function viewDetail(id: string | number) { router.push({ path: `/teacher/courses/${id}` }) }
function openLibrary(id: string | number) {
  router.push({ path: '/teacher/courses/content-library', query: { courseId: String(id) } })
}
function editCourse(id: string | number) { router.push({ path: `/teacher/courses/${id}/edit` }) }

/* init */
onMounted(() => {
  fetch()
})

onBeforeUnmount(() => {
  if (t) clearTimeout(t)
})
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
/* Ngăn chữ bị “nát” khi quá hẹp */
h3 { word-break: break-word; }
/* Tránh rung khi hover trên mobile */
@media (hover: none) {
  .hover\:shadow-sm:hover { box-shadow: none; }
  .hover\:bg-slate-50:hover { background: inherit; }
}
</style>
