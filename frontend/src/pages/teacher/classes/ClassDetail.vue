<!-- src/pages/teacher/classes/ClassDetail.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <!-- Loading skeleton -->
    <main v-if="loading" class="mx-auto max-w-screen-lg px-6 py-10">
      <div class="mb-5 flex items-center justify-between">
        <div class="h-7 w-64 rounded bg-slate-200 animate-pulse"></div>
        <div class="h-6 w-20 rounded bg-slate-200 animate-pulse"></div>
      </div>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="rounded-2xl border border-slate-200 bg-white p-4 md:col-span-2">
          <div class="h-5 w-40 rounded bg-slate-200 mb-3 animate-pulse"></div>
          <div class="space-y-2">
            <div class="h-4 w-3/4 rounded bg-slate-100 animate-pulse"></div>
            <div class="h-4 w-2/3 rounded bg-slate-100 animate-pulse"></div>
            <div class="h-4 w-1/2 rounded bg-slate-100 animate-pulse"></div>
          </div>
          <div class="mt-5 flex gap-2">
            <div class="h-9 w-24 rounded bg-slate-100 animate-pulse"></div>
            <div class="h-9 w-36 rounded bg-slate-100 animate-pulse"></div>
          </div>
        </div>
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="h-5 w-32 rounded bg-slate-200 mb-3 animate-pulse"></div>
          <div class="space-y-2">
            <div class="h-9 w-full rounded bg-slate-100 animate-pulse"></div>
            <div class="h-9 w-full rounded bg-slate-100 animate-pulse"></div>
          </div>
        </div>
      </div>
    </main>

    <!-- Not found -->
    <main v-else-if="!cls" class="mx-auto max-w-screen-md px-6 py-16 text-center">
      <h1 class="text-xl font-semibold">Không tìm thấy lớp học</h1>
      <p class="mt-2 text-slate-500">Vui lòng quay lại danh sách lớp.</p>
      <button
        class="mt-4 rounded-xl border px-4 py-2"
        @click="router.push({ path: '/teacher/classes' })"
      >
        ← Danh sách lớp
      </button>
    </main>

    <!-- Content -->
    <main v-else class="w-full mx-auto max-w-screen-lg px-6 py-8 md:px-10">
      <div class="mb-5 flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-semibold">
            {{ cls.name }}
            <span class="ml-2 text-base text-slate-500">({{ cls.code }})</span>
          </h1>
          <div class="mt-1 text-sm text-slate-500">
            Khoá: <span class="font-medium text-slate-700">{{ cls.course }}</span>
          </div>
        </div>
        <span class="rounded-full border px-3 py-1 text-xs" :class="badgeClass(cls.status)">
          {{ statusText(cls.status) }}
        </span>
      </div>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div class="rounded-2xl border border-slate-200 bg-white p-4 md:col-span-2">
          <h2 class="mb-3 text-base font-semibold">Thông tin lớp</h2>
          <ul class="space-y-2 text-sm">
            <li>
              • Mã lớp: <span class="font-medium text-slate-700">{{ cls.code }}</span>
            </li>
            <li>
              • Sĩ số: <span class="font-medium text-slate-700">{{ cls.students }}</span>
            </li>
            <li>
              • Lịch học:
              <span class="font-medium text-slate-700">
                {{ (cls.scheduleDays || []).join(', ') }} · {{ cls.time }}
              </span>
            </li>
            <li>
              • Phòng học: <span class="font-medium text-slate-700">{{ cls.room || '—' }}</span>
            </li>
            <li>
              • Cập nhật:
              <span class="font-medium text-slate-700">{{ fmtDate(cls.updatedAt) }}</span>
            </li>
          </ul>

          <div class="mt-5 flex flex-wrap gap-2">
            <button
              class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              @click="toAssignments"
            >
              Bài tập
            </button>
            <button
              class="rounded-xl bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-700"
              @click="toLive"
            >
              Vào lớp trực tuyến
            </button>
          </div>
        </div>

        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <h2 class="mb-3 text-base font-semibold">Tác vụ nhanh</h2>
          <div class="space-y-2">
            <button
              class="w-full rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              @click="toAssignments"
            >
              Giao bài tập
            </button>
            <button
              class="w-full rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              @click="toLive"
            >
              Bắt đầu buổi học
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

/** ===== Types ===== */
type ClassStatus = 'active' | 'draft' | 'archived'
type TeacherClass = {
  id: number
  name: string
  code: string
  course: string
  students: number
  scheduleDays: string[]
  time: string
  room?: string
  status: ClassStatus
  updatedAt: string
}

/** ===== Router ===== */
const route = useRoute()
const router = useRouter()
const id = ref<number>(Number(route.params.id))

/** ===== State ===== */
const loading = ref(true)
const cls = ref<TeacherClass | null>(null)

let classDetail: undefined | ((id: number) => Promise<TeacherClass | null>)

/** ===== Mock fallback ===== */
async function mockDetail(cid: number): Promise<TeacherClass | null> {
  if (!cid || Number.isNaN(cid)) return null
  const statuses: ClassStatus[] = ['active', 'draft', 'archived']
  return {
    id: cid,
    name: `Lớp Demo ${cid}`,
    code: 'CL' + String(1000 + cid),
    course: `Khoá học #${Math.max(1, cid % 7)}`,
    students: 18 + (cid % 10),
    scheduleDays: cid % 2 ? ['Thứ 3', 'Thứ 5'] : ['Thứ 2', 'Thứ 4', 'Thứ 6'],
    time: cid % 2 ? '18:30–20:00' : '19:00–20:30',
    room: cid % 3 ? `P${100 + (cid % 5)}` : 'Online',
    status: statuses[cid % statuses.length],
    updatedAt: new Date(Date.now() - cid * 36e5).toISOString(),
  }
}

/** ===== Fetch ===== */
async function fetchDetail() {
  loading.value = true
  cls.value = null
  try {
    const res = classDetail ? await classDetail(id.value) : await mockDetail(id.value)
    cls.value = res ?? null
  } catch (e) {
    console.error(e)
    cls.value = null
  } finally {
    loading.value = false
  }
}

onMounted(fetchDetail)
watch(
  () => route.params.id,
  (v) => {
    id.value = Number(v)
    fetchDetail()
  },
)

/** ===== UI helpers ===== */
function badgeClass(s: ClassStatus) {
  switch (s) {
    case 'active':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200'
    case 'draft':
      return 'bg-amber-50 text-amber-700 border-amber-200'
    case 'archived':
      return 'bg-slate-100 text-slate-700 border-slate-200'
  }
}
const statusText = (s: ClassStatus) =>
  s === 'active' ? 'Đang hoạt động' : s === 'draft' ? 'Nháp' : 'Lưu trữ'

function fmtDate(iso: string) {
  if (!iso) return '—'
  try {
    const d = new Date(iso)
    return d.toLocaleString()
  } catch {
    return iso
  }
}

/** ===== Nav actions ===== */
const toAssignments = () => router.push({ path: `/teacher/classes/${id.value}/assignments` })
const toLive = () => router.push({ path: `/teacher/classes/${id.value}/live` })

/** Expose router for template (not found back button) */
defineExpose({ router })
</script>

<style scoped>
:host,
.min-h-screen {
  overflow-x: hidden;
}
</style>
