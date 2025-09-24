<!-- src/pages/teacher/dashboard/dashboard.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-6 py-8 md:px-10">
      <h1 class="mb-4 text-2xl font-semibold">Bảng điều khiển</h1>

      <div class="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div class="space-y-6 xl:col-span-2">
          <!-- Thao tác nhanh -->
          <Card>
            <CardHeader title="Thao tác nhanh" />
            <div class="grid grid-cols-2 gap-3 p-4 sm:grid-cols-4">
              <QuickAction label="Tạo khoá học"         :onClick="goCreateCourse"><IconPlus/></QuickAction>
              <QuickAction label="Chấm điểm bài tập"     :onClick="goGradeAssignments"><IconClipboard/></QuickAction>
              <QuickAction label="Tạo bài kiểm tra"      :onClick="goCreateExam"><IconFile/></QuickAction>
              <QuickAction label="Xem báo cáo"           :onClick="goReports"><IconChart/></QuickAction>
            </div>
          </Card>

          <!-- Khoá học của tôi -->
          <Card>
            <CardHeader title="Khoá học của tôi" />
            <div class="space-y-3 p-4">
              <template v-if="loading">
                <div class="rounded-2xl border border-slate-200 bg-white p-6 text-center text-slate-500">
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

              <div v-else class="rounded-2xl border border-slate-200 bg-white p-6 text-center text-slate-500">
                Chưa có khoá học nào.
              </div>
            </div>
          </Card>
        </div>

        <!-- Cột phải -->
        <div class="space-y-6">
          <Card>
            <CardHeader title="Sự kiện sắp tới" />
            <div class="space-y-1.5 p-4">
              <UpcomingItem title="Kiểm tra giữa kỳ" time="11:24 AM" />
              <UpcomingItem title="Thuyết trình dự án" time="09:24 AM" />
              <UpcomingItem title="Phản biện thiết kế" time="03:00 PM" />
            </div>
          </Card>

          <Card>
            <CardHeader title="Thống kê" />
            <div class="grid grid-cols-3 gap-3 p-4 text-center">
              <Stat k="Khoá học" :v="stats.courses" />
              <Stat k="Học sinh" :v="stats.students" />
              <Stat k="Bài học"  :v="stats.assignments" />
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

/* ===== Kiểu dữ liệu local cho Dashboard ===== */
type Status = CourseStatus
type TeacherCourse = {
  id: number
  title: string
  enrolled: number
  lessons: number
  status: Status
}

/* ===== State ===== */
const loading = ref(true)
const source = ref<TeacherCourse[]>([])

/* Tổng hợp cho “Thống kê” (tổng hệ thống) */
const totals = ref({ courses: 0, students: 0, assignments: 0 })

/* ===== Nạp “Khoá học của tôi” (1 trang nhỏ) ===== */
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
    // Fallback demo
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

/* ===== Tính “Thống kê” đúng tổng từ service =====
   - Lấy total khoá học từ page đầu
   - Cộng dồn enrollments/lessonsCount bằng cách phân trang
   - Chặn đúng số record cuối cùng để không đếm thừa (mock hay thật đều an toàn)
*/
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

    // Giới hạn số bản ghi thực sự còn lại theo total
    const producedSoFar = (page - 1) * pageSize
    const remaining = Math.max(0, total - producedSoFar)
    const take = Math.min(remaining, res.items.length)

    const chunk = (res.items as CourseSummary[]).slice(0, take)
    for (const c of chunk) {
      sumStudents += (c.enrollments || 0)
      sumLessons  += (c.lessonsCount || 0)
    }

    if (page * pageSize >= total || take <= 0) break
    page++
    // an toàn: tránh vòng lặp vô hạn nếu BE không trả total chuẩn
    if (page > 50) break
  }

  totals.value = { courses: total, students: sumStudents, assignments: sumLessons }
}

onMounted(async () => {
  await Promise.all([loadCourses(), computeTotals()])
})

/* ===== sparkline point ===== */
type Pt = { x:number; y:number }
function sparkFor(id: number, enrolled: number): Pt[] {
  const n = 6
  return Array.from({ length: n }, (_, i) => {
    const y = 6 + ((id * (i + 3) + enrolled) % 13) // 6..18
    return { x: i + 1, y }
  })
}

/* Lấy tất cả khoá (hiển thị “của tôi”) */
const myCourses = computed<TeacherCourse[]>(() => source.value.slice())

/* ===== Thống kê (hiển thị tổng hệ thống) ===== */
const stats = computed(() => totals.value)

/* ===== Card primitives ===== */
const Card = defineComponent({
  name:'Card',
  setup(_, { slots }) { return () => (
    <div class="overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm">
      {slots.default?.()}
    </div>
  ) }
})

const CardHeader = defineComponent({
  name:'CardHeader',
  props:{ title:{type:String,required:true} },
  setup(p){ return () => (
    <div class="border-b p-4 pb-2"><h2 class="text-base font-semibold">{p.title}</h2></div>
  ) }
})

/* === QuickAction === */
const QuickAction = defineComponent({
  name:'QuickAction',
  props:{
    label: String,
    onClick: Function as PropType<() => void>
  },
  setup(props, { slots }) {
    return () => (
      <button
        type="button"
        class="w-full rounded-2xl border border-slate-200 bg-white p-4 text-left transition hover:shadow-lg focus:outline-none"
        onClick={props.onClick as any}
      >
        <div class="flex items-center gap-3">
          <div class="rounded-2xl bg-slate-100 p-3"><div class="h-5 w-5">{slots.default?.()}</div></div>
          <div class="text-sm font-medium">{props.label}</div>
        </div>
      </button>
    )
  }
})

/* ===== Sparkline ===== */
const Sparkline = defineComponent({
  name:'Sparkline',
  props:{ data:{ type: Array as PropType<Pt[]>, required:true } },
  setup(props){
    const d = computed(() => {
      const pts = props.data
      const xs = pts.map(p=>p.x), ys = pts.map(p=>p.y)
      const minX = Math.min(...xs), maxX = Math.max(...xs)
      const minY = Math.min(...ys), maxY = Math.max(...ys)
      const w=120,h=36,pad=2
      const sx = (x:number)=> pad+(w-2*pad)*(x-minX)/(maxX-minX || 1)
      const sy = (y:number)=> h-(pad+(h-2*pad)*(y-minY)/(maxY-minY || 1))
      return pts.map((p,i)=>`${i?'L':'M'}${sx(p.x)},${sy(p.y)}`).join(' ')
    })
    return () => (
      <svg viewBox="0 0 120 36" class="block h-9 w-28 leading-none">
        <path d={d.value} fill="none" stroke="currentColor" style={{strokeWidth:2}} class="text-slate-700"/>
      </svg>
    )
  }
})

/* ===== Course row (clickable) ===== */
const CourseItem = defineComponent({
  name:'CourseItem',
  props:{
    title: String,
    students: Number,
    status: String,
    data: { type: Array as PropType<Pt[]>, required:true },
    onClick: Function as PropType<() => void>
  },
  setup(p){
    return () => (
      <div
        class="flex items-center gap-4 rounded-2xl border border-slate-200 bg-white p-4 hover:bg-slate-50 cursor-pointer"
        onClick={p.onClick as any}
      >
        <div class="min-w-0 flex-1">
          <div class="text-sm font-medium">{p.title}</div>
          <div class="text-xs text-slate-500">{p.students} học viên</div>
        </div>
        <div class="ml-auto mr-2 w-28 sm:w-32 shrink-0 flex items-center justify-end">
          <Sparkline data={p.data as Pt[]}/>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          {p.status ? <span class="rounded-full bg-slate-100 px-2 py-1 text-xs">{p.status}</span> : null}
          <IconChevron class="text-slate-400 h-5 w-5"/>
        </div>
      </div>
    )
  }
})

const UpcomingItem = defineComponent({
  name:'UpcomingItem',
  props:{ title:String, time:String },
  setup(p){ return () => (
    <div class="flex items-center justify-between rounded-xl p-3 hover:bg-slate-50">
      <div class="flex items-center gap-3">
        <div class="rounded-xl bg-slate-100 p-2"><IconClock class="h-4 w-4"/></div>
        <div class="text-sm">{p.title}</div>
      </div>
      <div class="text-xs text-slate-500">{p.time}</div>
    </div>
  ) }
})

const Stat = defineComponent({
  name: 'Stat',
  props: {
    k: { type: String, required: true },
    v: { type: Number, default: 0 },
  },
  setup(p) {
    const fmt = (n: number) => new Intl.NumberFormat('vi-VN').format(n)
    return () => (
      <div class="rounded-2xl bg-slate-100 p-4">
        <div class="text-2xl font-semibold">{fmt(Number(p.v ?? 0))}</div>
        <div class="text-xs text-slate-500">{p.k}</div>
      </div>
    )
  },
})

/* ===== Icons ===== */
const IconPlus     = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5"><path d="M12 5v14M5 12h14" style={{strokeWidth:2}}/></svg>)
const IconClipboard= () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5"><rect x="8" y="2" width="8" height="4" rx="1" style={{strokeWidth:2}}/><path d="M9 4H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V6a2 2 0 0 0-2-2h-2" style={{strokeWidth:2}}/></svg>)
const IconFile     = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12V8z" style={{strokeWidth:2}}/><path d="M14 2v6h6" style={{strokeWidth:2}}/></svg>)
const IconChart    = () => (<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5"><path d="M3 3v18h18" style={{strokeWidth:2}}/><path d="M7 13l3 3 7-7" style={{strokeWidth:2}}/></svg>)
const IconClock    = (p:any) => (<svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor"><circle cx="12" cy="12" r="10" style={{strokeWidth:2}}/><path d="M12 6v6l4 2" style={{strokeWidth:2}}/></svg>)
const IconChevron  = (p:any) => (<svg {...p} viewBox="0 0 24 24" fill="none" stroke="currentColor" class="h-5 w-5"><path d="M9 18l6-6-6-6" style={{strokeWidth:2}}/></svg>)

/* ===== Helpers & Nav ===== */
function statusLabel(s: Status) {
  return s === 'published'       ? 'Đang dạy'
       : s === 'draft'           ? 'Nháp'
       : s === 'archived'        ? 'Lưu trữ'
       : s === 'pending_review'  ? 'Chờ duyệt'
       : s === 'rejected'        ? 'Bị từ chối'
       : s
}

const router = useRouter()
function openCourse(id: number) {
  router.push({ path: `/teacher/courses/${id}` })
}
const has = (name:string) => router.getRoutes().some(r => r.name === (name as any))
const go  = (name:string, path:string) => has(name) ? router.push({ name }) : router.push({ path })
function goCreateCourse()     { go('teacher-course-new',   '/teacher/courses/new') }
function goGradeAssignments() { go('teacher-exams',        '/teacher/exams') }
function goCreateExam()       { has('teacher-exam-new') ? router.push({ name:'teacher-exam-new' }) : router.push({ path:'/teacher/exams' }) }
function goReports()          { go('teacher-reports',      '/teacher/reports') }
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
</style>
