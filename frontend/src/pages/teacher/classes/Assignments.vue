<!-- src/pages/teacher/classes/ClassAssignments.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-xl px-6 py-8 md:px-10">
      <!-- Header -->
      <div class="mb-5 flex items-center justify-between">
        <h1 class="text-2xl font-semibold">Bài tập · {{ headerTitle }}</h1>
        <button
          class="rounded-xl bg-sky-600 px-4 py-2 font-semibold text-white hover:bg-sky-700"
          @click="createAssignment"
        >
          + Tạo bài tập
        </button>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <table class="w-full table-fixed">
          <thead class="bg-slate-50 text-left text-sm text-slate-600">
            <tr>
              <th class="p-3">Tiêu đề</th>
              <th class="p-3 w-40">Hạn nộp</th>
              <th class="p-3 w-32">Bài nộp</th>
              <th class="p-3 w-32">Trạng thái</th>
              <th class="p-3 w-48">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="i in 5" :key="'skel-' + i" class="border-t">
              <td class="p-3">
                <div class="h-4 w-48 rounded bg-slate-200 animate-pulse mb-2"></div>
                <div class="h-3 w-72 rounded bg-slate-100 animate-pulse"></div>
              </td>
              <td class="p-3"><div class="h-4 w-24 rounded bg-slate-100 animate-pulse"></div></td>
              <td class="p-3"><div class="h-4 w-16 rounded bg-slate-100 animate-pulse"></div></td>
              <td class="p-3">
                <div class="h-5 w-24 rounded-full bg-slate-100 animate-pulse"></div>
              </td>
              <td class="p-3">
                <div class="flex gap-2">
                  <div class="h-8 w-16 rounded bg-slate-100 animate-pulse"></div>
                  <div class="h-8 w-20 rounded bg-slate-100 animate-pulse"></div>
                  <div class="h-8 w-14 rounded bg-slate-200 animate-pulse"></div>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Empty -->
      <div
        v-else-if="!assignments.length"
        class="rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-500"
      >
        Chưa có bài tập nào. Hãy bấm “Tạo bài tập”.
      </div>

      <!-- Table -->
      <div v-else class="overflow-hidden rounded-2xl border border-slate-200 bg-white">
        <table class="w-full table-fixed">
          <thead class="bg-slate-50 text-left text-sm text-slate-600">
            <tr>
              <th class="p-3">Tiêu đề</th>
              <th class="p-3 w-40">Hạn nộp</th>
              <th class="p-3 w-32">Bài nộp</th>
              <th class="p-3 w-32">Trạng thái</th>
              <th class="p-3 w-48">Thao tác</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="a in assignments" :key="a.id" class="border-t text-sm">
              <td class="p-3">
                <div class="font-medium">{{ a.title }}</div>
                <div class="text-xs text-slate-500 truncate">{{ a.desc }}</div>
              </td>
              <td class="p-3">{{ a.due }}</td>
              <td class="p-3">{{ a.submitted }}/{{ a.total }}</td>
              <td class="p-3">
                <span
                  class="rounded-full border px-2 py-0.5 text-xs"
                  :class="
                    a.published
                      ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                      : 'bg-amber-50 text-amber-700 border-amber-200'
                  "
                >
                  {{ a.published ? 'Đã phát hành' : 'Nháp' }}
                </span>
              </td>
              <td class="p-3">
                <div class="flex flex-wrap gap-2">
                  <button
                    class="rounded-xl border px-3 py-1.5 text-sm hover:bg-slate-50"
                    @click="viewAssignment(a.id)"
                  >
                    Xem
                  </button>
                  <button
                    class="rounded-xl border px-3 py-1.5 text-sm hover:bg-slate-50"
                    @click="gradeAssignment(a.id)"
                  >
                    Chấm điểm
                  </button>
                  <button
                    class="rounded-xl bg-sky-600 px-3 py-1.5 text-sm font-semibold text-white hover:bg-sky-700"
                    @click="editAssignment(a.id)"
                  >
                    Sửa
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- Optional pager (ẩn nếu ít dữ liệu) -->
      <div v-if="totalPages > 1" class="mt-6 flex items-center justify-center gap-2">
        <button
          class="rounded-xl border px-3 py-2 text-sm"
          :disabled="page <= 1"
          @click="fetchList(page - 1)"
        >
          ‹
        </button>
        <button
          v-for="p in pagesToShow"
          :key="p.key"
          class="rounded-xl border px-3 py-2 text-sm"
          :class="{ 'bg-sky-600 text-white border-sky-600': p.num === page, 'opacity-70': p.sep }"
          :disabled="p.sep"
          @click="!p.sep && fetchList(p.num!)"
        >
          {{ p.text }}
        </button>
        <button
          class="rounded-xl border px-3 py-2 text-sm"
          :disabled="page >= totalPages"
          @click="fetchList(page + 1)"
        >
          ›
        </button>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/** ===== Types ===== */
type Assignment = {
  id: number
  title: string
  desc: string
  due: string
  submitted: number
  total: number
  published: boolean
}
type ClassDetail = { id: number; name: string } | null

/** ===== Router / state ===== */
const route = useRoute()
const router = useRouter()
const classId = ref<number>(Number(route.params.id))

const loading = ref(true)
const assignments = ref<Assignment[]>([])
const cls = ref<ClassDetail>(null)

/** Pagination (tuỳ chọn) */
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

let fetchDetailFn: undefined | ((id: number) => Promise<ClassDetail>)
let fetchAssignmentsFn:
  | undefined
  | ((p: {
      classId: number
      page: number
      pageSize: number
    }) => Promise<{ items: Assignment[]; total: number }>)

/** ===== Mock fallback ===== */
function mockDetail(id: number): Promise<ClassDetail> {
  if (!id || Number.isNaN(id)) return Promise.resolve(null)
  return Promise.resolve({ id, name: `Lớp Demo ${id}` })
}
function mockAssignments(params: {
  classId: number
  page: number
  pageSize: number
}): Promise<{ items: Assignment[]; total: number }> {
  const { classId, page, pageSize } = params
  const allCount = 28 + (classId % 7) // tổng ảo
  const all = Array.from({ length: allCount }).map((_, i) => ({
    id: classId * 1000 + i + 1,
    title: `Bài tập ${i + 1}`,
    desc: i % 2 ? 'Ôn luyện kiến thức chương trước' : 'Bài luyện tập kỹ năng',
    due: new Date(Date.now() + (i + 2) * 864e5).toLocaleDateString(),
    submitted: (i * 7 + classId) % 21,
    total: 30,
    published: i % 3 !== 0,
  }))
  const start = (page - 1) * pageSize
  return Promise.resolve({ items: all.slice(start, start + pageSize), total: all.length })
}

/** ===== Fetchers ===== */
async function fetchDetail() {
  try {
    cls.value = fetchDetailFn ? await fetchDetailFn(classId.value) : await mockDetail(classId.value)
  } catch {
    cls.value = null
  }
}
async function fetchList(p = page.value) {
  loading.value = true
  page.value = p
  try {
    const res = fetchAssignmentsFn
      ? await fetchAssignmentsFn({
          classId: classId.value,
          page: page.value,
          pageSize: pageSize.value,
        })
      : await mockAssignments({
          classId: classId.value,
          page: page.value,
          pageSize: pageSize.value,
        })
    assignments.value = res.items
    total.value = res.total
  } catch (e) {
    console.error(e)
    assignments.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

/** ===== Header ===== */
const headerTitle = computed(() => cls.value?.name ?? `Lớp #${classId.value}`)

/** Pager window (gọn, có dấu …) */
const pagesToShow = computed(() => {
  const max = totalPages.value,
    cur = page.value,
    windowSize = 7
  const arr: { key: string; num?: number; text: string; sep?: boolean }[] = []
  const push = (n: number) => arr.push({ key: 'p' + n, num: n, text: String(n) })
  const sep = (k: string) => arr.push({ key: k, text: '…', sep: true })

  if (max <= windowSize + 2) {
    for (let i = 1; i <= max; i++) push(i)
  } else {
    push(1)
    const start = Math.max(2, cur - 2),
      end = Math.min(max - 1, cur + 2)
    if (start > 2) sep('s')
    for (let i = start; i <= end; i++) push(i)
    if (end < max - 1) sep('e')
    push(max)
  }
  return arr
})

/** ===== Actions (demo) ===== */
function createAssignment() {
  alert('Tạo bài tập (demo). Gắn router/Modal của bạn ở đây.')
}
function viewAssignment(id: number) {
  alert(`Xem bài tập #${id} (demo)`)
}
function gradeAssignment(id: number) {
  alert(`Chấm điểm bài tập #${id} (demo)`)
}
function editAssignment(id: number) {
  alert(`Sửa bài tập #${id} (demo)`)
}

/** ===== Mount & route change ===== */
onMounted(async () => {
  await fetchDetail()
  await fetchList(1)
})
watch(
  () => route.params.id,
  async (v) => {
    classId.value = Number(v)
    await fetchDetail()
    await fetchList(1)
  },
)
</script>

<style scoped>
:host,
.min-h-screen {
  overflow-x: hidden;
}
</style>
