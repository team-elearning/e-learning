<!-- src/pages/teacher/dashboard/dashboard.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <h1 class="mb-4 text-xl sm:text-2xl font-semibold">Bảng điều khiển</h1>

      <div class="grid grid-cols-1 gap-4 sm:gap-6 xl:grid-cols-3">
        <div class="space-y-4 sm:space-y-6 xl:col-span-2">
          <!-- Thao tác nhanh -->
          <Card>
            <CardHeader title="Thao tác nhanh" />
            <div class="grid grid-cols-2 gap-2 p-3 sm:grid-cols-4 sm:gap-3 sm:p-4">
              <QuickAction label="Tạo khoá học" :onClick="goCreateCourse"><IconPlus /></QuickAction>
              <QuickAction label="Chấm điểm bài tập" :onClick="goGradeAssignments"><IconClipboard /></QuickAction>
              <QuickAction label="Tạo bài kiểm tra" :onClick="goCreateExam"><IconFile /></QuickAction>
              <QuickAction label="Xem báo cáo" :onClick="goReports"><IconChart /></QuickAction>
            </div>
          </Card>

          <!-- Khoá học của tôi -->
          <Card>
            <CardHeader title="Khoá học của tôi" />
            <div class="space-y-2 p-3 sm:space-y-3 sm:p-4">
              <template v-if="loading">
                <div class="rounded-2xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
                  Đang tải dữ liệu...
                </div>
              </template>

              <template v-else-if="myCourses.length">
                <CourseItem
                  v-for="c in myCourses"
                  :key="c.id"
                  :title="c.title"
                  :students="c.enrolled"
                  :status="statusLabel(c.status)"
                  :data="sparkFor(c.id, c.enrolled)"
                  :onClick="() => openCourse(c.id)"
                />
              </template>

              <div v-else class="rounded-2xl border border-slate-200 bg-white p-6 text-center text-sm text-slate-500">
                Chưa có khoá học nào.
              </div>
            </div>
          </Card>
        </div>

        <!-- Cột phải -->
        <div class="space-y-4 sm:space-y-6">
          <Card>
            <CardHeader title="Sự kiện sắp tới" />
            <div class="space-y-1.5 p-3 sm:p-4">
              <UpcomingItem title="Kiểm tra giữa kỳ" time="11:24 AM" />
              <UpcomingItem title="Thuyết trình dự án" time="09:24 AM" />
              <UpcomingItem title="Phản biện thiết kế" time="03:00 PM" />
            </div>
          </Card>

          <Card>
            <CardHeader title="Thống kê" />
            <div class="grid grid-cols-3 gap-2 p-3 text-center sm:gap-3 sm:p-4">
              <Stat k="Khoá học" :v="stats.courses" />
              <Stat k="Học sinh" :v="stats.students" />
              <Stat k="Bài học" :v="stats.assignments" />
            </div>
          </Card>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="tsx">
import { computed, defineComponent, type PropType, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { courseService, type CourseStatus, type CourseSummary } from '@/services/course.service'

type Status = CourseStatus
type TeacherCourse = {
  id: number
  title: string
  enrolled: number
  lessons: number
  status: Status
}

const loading = ref(true)
const source = ref<TeacherCourse[]>([])
const totals = ref({ courses: 0, students: 0, assignments: 0 })

async function loadCourses() {
  try {
    const { items } = await courseService.list({ page: 1, pageSize: 8 })
    source.value = (items as CourseSummary[]).map((c) => ({
      id: Number(c.id),
      title: c.title,
      enrolled: c.enrollments,
      lessons: c.lessonsCount,
      status: c.status as Status
    }))
  } catch {
    source.value = Array.from({ length: 5 }, (_, i) => ({
      id: i + 1,
      title: `Khoá học #${i + 1}`,
      enrolled: 20 + i * 7,
      lessons: 8 + i * 3,
      status: (i % 2 === 0 ? 'published' : 'draft') as Status
    }))
  } finally {
    loading.value = false
  }
}

async function computeTotals() {
  const pageSize = 50
  let page = 1
  let total = 0
  let sumStudents = 0
  let sumLessons = 0
  let knownTotal = false

  while (true) {
    const res = await courseService.list({ page, pageSize })
    if (!knownTotal) {
      total = res.total || res.items.length
      knownTotal = true
    }

    const producedSoFar = (page - 1) * pageSize
    const remaining = Math.max(0, total - producedSoFar)
    const take = Math.min(remaining, res.items.length)

    const chunk = (res.items as CourseSummary[]).slice(0, take)
    for (const c of chunk) {
      sumStudents += c.enrollments || 0
      sumLessons += c.lessonsCount || 0
    }

    if (page * pageSize >= total || take <= 0) break
    page++
    if (page > 50) break
  }

  totals.value = { courses: total, students: sumStudents, assignments: sumLessons }
}

onMounted(async () => {
  await Promise.all([loadCourses(), computeTotals()])
})

type Pt = { x: number; y: number }
function sparkFor(id: number, enrolled: number): Pt[] {
  const n = 6
  return Array.from({ length: n }, (_, i) => {
    const y = 6 + ((id * (i + 3) + enrolled) % 13)
    return { x: i + 1, y }
  })
}

const myCourses = computed<TeacherCourse[]>(() => source.value.slice())
const stats = computed(() => totals.value)

const Card = defineComponent({
  name: 'Card',
  setup(_, { slots }) {
    return () => (
      <div class="overflow-hidden rounded-xl sm:rounded-2xl border border-slate-200 bg-white shadow-sm">
        {slots.default?.()}
      </div>
    )
  }
})

const CardHeader = defineComponent({
  name: 'CardHeader',
  props: { title: { type: String, required: true } },
  setup(p) {
    return () => (
      <div class="border-b p-3 pb-2 sm:p-4 sm:pb-2">
        <h2 class="text-sm font-semibold sm:text-base">{p.title}</h2>
      </div>
    )
  }
})

const QuickAction = defineComponent({
  name: 'QuickAction',
  props: {
    label: String,
    onClick: Function as PropType<() => void>
  },
  setup(props, { slots }) {
    return () => (
      <button
        type="button"
        class="w-full rounded-xl sm:rounded-2xl border border-slate-200 bg-white p-3 sm:p-4 text-left transition hover:shadow-lg focus:outline-none active:scale-95"
        onClick={props.onClick as any}
      >
        <div class="flex flex-col items-center gap-2 sm:flex-row sm:items-center sm:gap-3">
          <div class="rounded-xl sm:rounded-2xl bg-slate-100 p-2.5 sm:p-3">
            <div class="h-4 w-4 sm:h-5 sm:w-5">{slots.default?.()}</div>
          </div>
          <div class="text-xs font-medium text-center sm:text-left sm:text-sm">{props.label}</div>
        </div>
      </button>
    )
  }
})

const Sparkline = defineComponent({
  name: 'Sparkline',
  props: { data: { type: Array as PropType<Pt[]>, required: true } },
  setup(props) {
    const d = computed(() => {
      const pts = props.data
      const xs = pts.map((p) => p.x),
        ys = pts.map((p) => p.y)
      const minX = Math.min(...xs),
        maxX = Math.max(...xs)
      const minY = Math.min(...ys),
        maxY = Math.max(...ys)
      const w = 120,
        h = 36,
        pad = 2
      const sx = (x: number) => pad + ((w - 2 * pad) * (x - minX)) / (maxX - minX || 1)
      const sy = (y: number) => h - (pad + ((h - 2 * pad) * (y - minY)) / (maxY - minY || 1))
      return pts.map((p, i) => `${i ? 'L' : 'M'}${sx(p.x)},${sy(p.y)}`).join(' ')
    })
    return () => (
      <svg viewBox="0 0 120 36" class="block h-7 w-20 leading-none sm:h-9 sm:w-28">
        <path d={d.value} fill="none" stroke="currentColor" style={{ strokeWidth: 2 }} class="text-slate-700" />
      </svg>
    )
  }
})

const CourseItem = defineComponent({
  name: 'CourseItem',
  props: {
    title: String,
    students: Number,
    status: String,
    data: { type: Array as PropType<Pt[]>, required: true },
    onClick: Function as PropType<() => void>
  },
  setup(p) {
    return () => (
      <div
        class="flex items-center gap-2 sm:gap-4 rounded-xl sm:rounded-2xl border border-slate-200 bg-white p-3 sm:p-4 hover:bg-slate-50 cursor-pointer transition active:scale-[0.98]"
        onClick={p.onClick as any}
      >
        <div class="min-w-0 flex-1">
          <div class="text-xs font-medium sm:text-sm truncate">{p.title}</div>
          <div class="text-[10px] text-slate-500 sm:text-xs">{p.students} học viên</div>
        </div>
        <div class="ml-auto shrink-0 flex items-center justify-end">
          <Sparkline data={p.data as Pt[]} />
        </div>
        <div class="flex items-center gap-1.5 sm:gap-2 shrink-0">
          {p.status ? (
            <span class="rounded-full bg-slate-100 px-2 py-0.5 text-[10px] sm:text-xs whitespace-nowrap">{p.status}</span>
          ) : null}
          <IconChevron class="text-slate-400 h-4 w-4 sm:h-5 sm:w-5" />
        </div>
      </div>
    )
  }
})

const UpcomingItem = defineComponent({
  name: 'UpcomingItem',
  props: { title: String, time: String },
  setup(p) {
    return () => (
      <div class="flex items-center justify-between rounded-lg sm:rounded-xl p-2.5 sm:p-3 hover:bg-slate-50 transition">
        <div class="flex items-center gap-2 sm:gap-3">
          <div class="rounded-lg sm:rounded-xl bg-slate-100 p-1.5 sm:p-2">
            <IconClock class="h-3.5 w-3.5 sm:h-4 sm:w-4" />
          </div>
          <div class="text-xs sm:text-sm truncate">{p.title}</div>
        </div>
        <div class="text-[10px] text-slate-500 sm:text-xs whitespace-nowrap ml-2">{p.time}</div>
      </div>
    )
  }
})

const Stat = defineComponent({
  name: 'Stat',
  props: {
    k: { type: String, required: true },
    v: { type: Number, default: 0 }
  },
  setup(p) {
    const fmt = (n: number) => new Intl.NumberFormat('vi-VN').format(n)
    return () => (
      <div class="rounded-xl sm:rounded-2xl bg-slate-100 p-3 sm:p-4">
        <div class="text-lg font-semibold sm:text-2xl">{fmt(Number(p.v ?? 0))}</div>
        <div class="text-[10px] text-slate-500 sm:text-xs">{p.k}</div>
      </div>
    )
  }
})

const IconPlus = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-full w-full">
    <path d="M12 5v14M5 12h14" style={{ strokeWidth: 2 }} />
  </svg>
)
const IconClipboard = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-full w-full">
    <rect x="8" y="2" width="8" height="4" rx="1" style={{ strokeWidth: 2 }} />
    <path d="M9 4H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2" style={{ strokeWidth: 2 }} />
  </svg>
)
const IconFile = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-full w-full">
    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12V8z" style={{ strokeWidth: 2 }} />
    <path d="M14 2v6h6" style={{ strokeWidth: 2 }} />
  </svg>
)
const IconChart = () => (
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-full w-full">
    <path d="M3 3v18h18" style={{ strokeWidth: 2 }} />
    <path d="M7 13l3 3 7-7" style={{ strokeWidth: 2 }} />
  </svg>
)
const IconClock = (p: any) => (
  <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor">
    <circle cx="12" cy="12" r="10" style={{ strokeWidth: 2 }} />
    <path d="M12 6v6l4 2" style={{ strokeWidth: 2 }} />
  </svg>
)
const IconChevron = (p: any) => (
  <svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor">
    <path d="M9 18l6-6-6-6" style={{ strokeWidth: 2 }} />
  </svg>
)

function statusLabel(s: Status) {
  return s === 'published'
    ? 'Đang dạy'
    : s === 'draft'
    ? 'Nháp'
    : s === 'archived'
    ? 'Lưu trữ'
    : s === 'pending_review'
    ? 'Chờ duyệt'
    : s === 'rejected'
    ? 'Bị từ chối'
    : s
}

const router = useRouter()
function openCourse(id: number) {
  router.push({ path: `/teacher/courses/${id}` })
}
const has = (name: string) => router.getRoutes().some((r) => r.name === (name as any))
const go = (name: string, path: string) => (has(name) ? router.push({ name }) : router.push({ path }))
function goCreateCourse() {
  go('teacher-course-new', '/teacher/courses/new')
}
function goGradeAssignments() {
  go('teacher-exams', '/teacher/exams')
}
function goCreateExam() {
  has('teacher-exam-new') ? router.push({ name: 'teacher-exam-new' }) : router.push({ path: '/teacher/exams' })
}
function goReports() {
  go('teacher-reports', '/teacher/reports')
}
</script>

<style scoped>
:host,
.min-h-screen {
  overflow-x: hidden;
}
</style>