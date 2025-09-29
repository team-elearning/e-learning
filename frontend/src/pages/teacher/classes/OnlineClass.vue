<!-- src/pages/teacher/classes/ClassLive.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <!-- Loading -->
    <main v-if="loading" class="w-full mx-auto max-w-screen-xl px-6 py-10">
      <div class="h-7 w-72 rounded bg-slate-200 animate-pulse mb-2"></div>
      <div class="h-4 w-96 rounded bg-slate-100 animate-pulse mb-6"></div>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <div
          class="rounded-2xl border border-slate-200 bg-black/60 aspect-video md:col-span-2"
        ></div>
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <div class="h-5 w-1/3 rounded bg-slate-200 mb-3"></div>
          <div class="space-y-2">
            <div class="h-9 w-full rounded bg-slate-100"></div>
            <div class="h-9 w-full rounded bg-slate-100"></div>
            <div class="h-9 w-full rounded bg-slate-100"></div>
            <div class="h-9 w-full rounded bg-slate-100"></div>
          </div>
        </div>
      </div>
    </main>

    <!-- Not found -->
    <main v-else-if="!cls" class="mx-auto max-w-screen-md px-6 py-16 text-center">
      <h1 class="text-xl font-semibold">Không tìm thấy lớp học</h1>
      <p class="mt-2 text-slate-500">Vui lòng quay lại danh sách lớp.</p>
    </main>

    <!-- Content -->
    <main v-else class="w-full mx-auto max-w-screen-xl px-6 py-8 md:px-10">
      <div class="mb-5">
        <h1 class="text-2xl font-semibold">Lớp trực tuyến · {{ headerTitle }}</h1>
        <p class="mt-1 text-sm text-slate-500">
          Phòng: {{ cls.room || '—' }} · Lịch: {{ (cls.scheduleDays || []).join(', ') || '—' }} ·
          {{ cls.time || '—' }}
        </p>
      </div>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-3">
        <!-- Video/Meeting placeholder -->
        <div
          class="rounded-2xl border border-slate-200 bg-black/80 aspect-video md:col-span-2 flex items-center justify-center text-white"
        >
          <div class="text-center">
            <div class="text-xl font-semibold">Khung video/meeting</div>
            <div class="mt-2 text-sm text-white/70">Giả lập – nhúng Zoom/Meet/WebRTC tại đây</div>
          </div>
        </div>

        <!-- Controls -->
        <div class="rounded-2xl border border-slate-200 bg-white p-4">
          <h2 class="mb-3 text-base font-semibold">Điều khiển</h2>
          <div class="space-y-2">
            <button
              class="w-full rounded-xl bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-700"
            >
              Bắt đầu buổi học
            </button>
            <button class="w-full rounded-xl border px-3 py-2 text-sm hover:bg-slate-50">
              Chia sẻ màn hình
            </button>
            <button class="w-full rounded-xl border px-3 py-2 text-sm hover:bg-slate-50">
              Tắt/Mở mic
            </button>
            <button class="w-full rounded-xl border px-3 py-2 text-sm hover:bg-slate-50">
              Tắt/Mở camera
            </button>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

/* ===== Types ===== */
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

/* ===== Router / state ===== */
const route = useRoute()
const id = ref<number>(Number(route.params.id))
const loading = ref(true)
const cls = ref<TeacherClass | null>(null)

let classDetail: undefined | ((id: number) => Promise<TeacherClass | null>)

/* ===== Mock fallback ===== */
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

/* ===== Fetch ===== */
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

/* ===== UI ===== */
const headerTitle = computed(() => cls.value?.name ?? `Lớp #${id.value}`)
</script>

<style scoped>
:host,
.min-h-screen {
  overflow-x: hidden;
}
</style>
