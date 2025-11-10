<!-- src/pages/student/courses/MyCourses.vue -->
<template>
  <div class="my-courses">
    <div class="layout">
      <!-- Main content -->
      <div class="container">
        <!-- Header -->
        <div class="header">
          <div class="lh">
            <h1>Khoá học của tôi</h1>
            <p class="lead">
              Các khóa học bạn đang sở hữu được chia theo từng cấp trình độ, tương ứng với mỗi chặng mục tiêu.
              Hãy chọn trình độ mà bạn muốn bắt đầu nhé.
            </p>
          </div>

          <!-- Quick Links -->
          <div class="quick">
            <router-link class="ghost" :to="{ name: 'student-learning-path' }">Lộ trình</router-link>
            <router-link class="ghost" :to="{ name: 'student-catalog' }">Catalog</router-link>
          </div>
        </div>

        <!-- Tabs + tools -->
        <div class="tabs-tools">
          <div class="tabs">
            <button class="tab" :class="{active: activeTab==='main'}" @click="activeTab='main'">Khóa học chính</button>
            <button class="tab" :class="{active: activeTab==='supp'}" @click="activeTab='supp'">Khóa học bổ trợ</button>
          </div>

          <div class="tools">
            <div class="select" @mouseleave="open=false">
              <button class="select-btn" @click="open = !open">
                {{ level || 'Tất cả trình độ' }}
                <svg viewBox="0 0 24 24"><path d="M6 9l6 6 6-6"/></svg>
              </button>
              <ul v-show="open" class="select-menu">
                <li @click="setLevel('')">Tất cả trình độ</li>
                <li @click="setLevel('Khối 1–2')">Khối 1–2</li>
                <li @click="setLevel('Khối 3–5')">Khối 3–5</li>
              </ul>
            </div>

            <div class="search">
              <svg viewBox="0 0 24 24"><path d="M21 21l-4.3-4.3"/><circle cx="11" cy="11" r="7"/></svg>
              <input v-model.trim="q" placeholder="Tìm khóa học..." />
            </div>
          </div>
        </div>

        <!-- ============ TAB: KHÓA HỌC CHÍNH ============ -->
        <template v-if="activeTab==='main'">
          <!-- SECTION: Khối 1–2 -->
          <section class="section" v-if="baseList.length">
            <div class="section-head">
              <div>
                <h3>Khối 1–2 (Cơ bản)</h3>
                <span class="sub">{{ baseList.length }} môn</span>
              </div>
              <div class="rh">
                <span class="trophy">🏆 {{ baseTrophies.earned }}/{{ baseTrophies.total }}</span>
                <router-link class="ghost sm" :to="{ name:'student-catalog', query: { grade: 1 } }">Xem tất cả ›</router-link>
              </div>
            </div>

            <div class="grid">
              <article v-for="c in baseList" :key="c.id" class="card" @click="openDetail(c.id)">
                <div class="thumb">
                  <img :src="c.thumbnail" :alt="c.title" />
                  <button class="play" type="button" title="Vào học" @click.stop="playFirst(c.id)">
                    <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  </button>
                </div>
                <div class="meta">
                  <div class="title">{{ c.title }}</div>
                  <div class="info">
                    <span class="state" :class="{ok: c.done}">
                      <span class="dot"></span>
                      {{ c.done ? 'Đã hoàn thành' : 'Đang học' }}<template v-if="!c.done"> · {{ c.progress }}%</template>
                    </span>
                    <span class="score"><span class="emoji">🏆</span> {{ c.score }}</span>
                  </div>
                </div>
              </article>
            </div>
          </section>

          <!-- SECTION: Khối 3–5 -->
          <section class="section" v-if="midList.length">
            <div class="section-head">
              <div>
                <h3>Khối 3–5 (Nâng cao)</h3>
                <span class="sub">{{ midList.length }} môn</span>
              </div>
              <div class="rh">
                <span class="trophy">🏆 {{ midTrophies.earned }}/{{ midTrophies.total }}</span>
                <router-link class="ghost sm" :to="{ name:'student-catalog', query: { grade: 3 } }">Xem tất cả ›</router-link>
              </div>
            </div>

            <div class="grid">
              <article v-for="c in midList" :key="c.id" class="card" @click="openDetail(c.id)">
                <div class="thumb">
                  <img :src="c.thumbnail" :alt="c.title" />
                  <button class="play" type="button" title="Vào học" @click.stop="playFirst(c.id)">
                    <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z"/></svg>
                  </button>
                </div>
                <div class="meta">
                  <div class="title">{{ c.title }}</div>
                  <div class="info">
                    <span class="state" :class="{ok: c.done}">
                      <span class="dot"></span>
                      {{ c.done ? 'Đã hoàn thành' : 'Đang học' }}<template v-if="!c.done"> · {{ c.progress }}%</template>
                    </span>
                    <span class="score"><span class="emoji">🏆</span> {{ c.score }}</span>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </template>

        <!-- ============ TAB: KHÓA HỌC BỔ TRỢ ============ -->
        <template v-else>
          <section class="section">
            <div class="section-head">
              <div>
                <h3>Khóa học bổ trợ</h3>
                <span class="sub">{{ suppList.length }} khóa</span>
              </div>
              <router-link class="ghost sm" :to="{ name:'student-catalog' }">Tìm thêm ›</router-link>
            </div>

            <div class="grid">
              <article 
                v-for="s in suppList" 
                :key="s.id" 
                class="card"
                @click="enroll(s.id)"
              >
                <div class="thumb">
                  <img :src="s.thumbnail" :alt="s.title" />
                  <span class="chip">{{ s.tag }}</span>
                </div>
                <div class="meta">
                  <div class="title">{{ s.title }}</div>
                  <div class="info">
                    <span class="state ok"><span class="dot"></span> Phù hợp {{ toLevelLabel(s.grade) }}</span>
                    <button class="join-btn" @click.stop="enroll(s.id)"><span>Tham gia</span></button>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </template>

        <!-- Tổng số cúp -->
        <div class="stats-bottom" v-if="activeTab==='main' && (baseList.length || midList.length)">
          <span class="pill"><span class="emoji">🏆</span> Tổng số cúp đã đạt <b>{{ (baseTrophies.earned + midTrophies.earned) }}/{{ (baseTrophies.total + midTrophies.total) }}</b></span>
        </div>

        <div
          v-if="(activeTab==='main' && baseList.length + midList.length === 0) || (activeTab==='supp' && !suppList.length)"
          class="empty"
        >
          Không có khóa học phù hợp.
        </div>

        <div v-if="err" class="empty" style="color:#b91c1c">{{ err }}</div>
      </div>

      <!-- ============ SIDEBAR TIẾN ĐỘ ============ -->
      <aside class="progress-sidebar">
        <!-- Tổng quan -->
        <div class="widget overview">
          <div class="widget-header">
            <h4>Tiến độ học tập</h4>
            <span class="period">Tháng này</span>
          </div>

          <!-- Overall progress -->
          <div class="overall-progress">
            <div class="circle-progress">
              <svg viewBox="0 0 120 120" class="progress-ring">
                <circle class="ring-bg" cx="60" cy="60" r="52" />
                <circle 
                  class="ring-fill" 
                  cx="60" 
                  cy="60" 
                  r="52" 
                  :style="{ strokeDashoffset: overallDashOffset }"
                />
              </svg>
              <div class="progress-text">
                <span class="pct">{{ overallProgress }}%</span>
                <span class="label">Hoàn thành</span>
              </div>
            </div>

            <div class="stats-row">
              <div class="stat-item">
                <span class="num">{{ totalCoursesEnrolled }}</span>
                <span class="lbl">Khóa học</span>
              </div>
              <div class="stat-item">
                <span class="num">{{ totalLessonsCompleted }}</span>
                <span class="lbl">Bài học</span>
              </div>
              <div class="stat-item">
                <span class="num">{{ totalHoursLearned }}</span>
                <span class="lbl">Giờ học</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Mục tiêu tuần -->
        <div class="widget goals">
          <div class="widget-header">
            <h4>Mục tiêu tuần</h4>
            <button class="icon-btn" title="Chỉnh sửa">
              <svg viewBox="0 0 24 24"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg>
            </button>
          </div>

          <div class="goal-list">
            <div class="goal-item">
              <div class="goal-info">
                <span class="goal-label">Học 5 bài/tuần</span>
                <span class="goal-progress">{{ weeklyLessons }}/5</span>
              </div>
              <div class="goal-bar">
                <div class="goal-fill" :style="{ width: Math.min(100, (weeklyLessons / 5) * 100) + '%' }"></div>
              </div>
            </div>

            <div class="goal-item">
              <div class="goal-info">
                <span class="goal-label">60 phút/ngày</span>
                <span class="goal-progress">{{ dailyMinutes }}/60</span>
              </div>
              <div class="goal-bar">
                <div class="goal-fill" :style="{ width: Math.min(100, (dailyMinutes / 60) * 100) + '%' }"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Đang học gần đây -->
        <div class="widget recent">
          <div class="widget-header">
            <h4>Đang học</h4>
            <router-link class="link-sm" :to="{ name: 'student-catalog' }">Xem thêm ›</router-link>
          </div>

          <div class="recent-list">
            <article 
              v-for="c in recentCourses" 
              :key="c.id" 
              class="recent-item"
              @click="openDetail(c.id)"
            >
              <div class="recent-thumb">
                <img :src="c.thumbnail" :alt="c.title" />
              </div>
              <div class="recent-info">
                <div class="recent-title">{{ c.title }}</div>
                <div class="recent-meta">
                  <span class="recent-progress">{{ c.progress }}%</span>
                  <div class="mini-bar">
                    <div class="mini-fill" :style="{ width: c.progress + '%' }"></div>
                  </div>
                </div>
              </div>
            </article>
          </div>
        </div>
      </aside>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { courseService, type CourseSummary, type CourseDetail } from '@/services/course.service'

const router = useRouter()

/* Tabs */
const activeTab = ref<'main'|'supp'>('main')

/* Tìm kiếm / lọc */
const q = ref('')
const level = ref<'' | 'Khối 1–2' | 'Khối 3–5'>('')
const open = ref(false)
function setLevel(v: '' | 'Khối 1–2' | 'Khối 3–5'){ level.value = v; open.value = false }

const err = ref('')

/* ====== LOAD COURSES FROM SERVICE ====== */
type Item = CourseSummary & {
  progress: number
  done: boolean
  score: string
  tag?: string
  isPurchased?: boolean
}

const all = ref<Item[]>([])
const detailsMap = ref(new Map<string, CourseDetail>())

function toLevelLabel(grade: number) { return grade <= 2 ? 'Khối 1–2' : 'Khối 3–5' }

function calcScore(progress: number) {
  const earned = Math.max(0, Math.min(5, Math.round(progress / 20)))
  return `${earned}/5`
}

function calcProgressFromDetail(d: CourseDetail, id: number | string) {
  const total = d.lessonsCount || d.sections?.reduce((a, s) => a + (s.lessons?.length || 0), 0) || 0
  let done = Number(id) % (total || 1)
  if (total > 0 && done === 0) done = total
  const pct = total ? Math.round((done / total) * 100) : 0
  return Math.max(0, Math.min(100, pct))
}

async function load() {
  try {
    const { items } = await courseService.list({
      page: 1, pageSize: 20,
      status: 'published', sortBy: 'updatedAt', sortDir: 'descending'
    })

    const limited = (items || []).slice(0, 24)
    const details = await Promise.all(limited.map(i => courseService.detail(i.id)))
    const map = new Map<string, CourseDetail>()
    details.forEach(d => map.set(String(d.id), d))
    detailsMap.value = map

    all.value = (items || []).map(i => {
      const d = map.get(String(i.id))
      const progress = d ? calcProgressFromDetail(d, i.id) : ((Number(i.id) * 13) % 100)
      
      const isPurchased = i.grade <= 2
      
      return {
        ...i,
        progress,
        done: progress >= 100,
        score: calcScore(progress),
        tag: i.subject?.toUpperCase?.(),
        isPurchased
      }
    })
  } catch (e: any) {
    err.value = e?.message || String(e)
  }
}

/* ====== FILTERING ====== */
const filteredMain = computed(() => {
  let arr = all.value.slice()
  if (q.value) {
    const key = q.value.toLowerCase()
    arr = arr.filter(x => x.title.toLowerCase().includes(key))
  }
  if (level.value) {
    arr = arr.filter(x => toLevelLabel(x.grade) === level.value)
  }
  return arr
})
const baseList = computed(()=> filteredMain.value.filter(x=> x.grade <= 2))
const midList  = computed(()=> filteredMain.value.filter(x=> x.grade >= 3))
function parseScore(s: string){ const [a,b] = s.split('/').map(n=>parseInt(n)); return { earned: a||0, total: b||0 } }
function sumTrophies(list: Item[]){ return list.reduce((acc,c)=>{ const s=parseScore(c.score); acc.earned+=s.earned; acc.total+=s.total; return acc }, {earned:0,total:0}) }
const baseTrophies = computed(()=> sumTrophies(baseList.value))
const midTrophies  = computed(()=> sumTrophies(midList.value))

/** Supp tab */
const suppList = computed(() => {
  let arr = all.value.slice().map(c => ({ ...c, tag: c.tag || 'Bổ trợ' }))
  if (level.value) arr = arr.filter(s => toLevelLabel(s.grade) === level.value)
  if (q.value){
    const key=q.value.toLowerCase()
    arr = arr.filter(s => s.title.toLowerCase().includes(key) || (s.tag||'').toLowerCase().includes(key))
  }
  return arr
})

/* ====== SIDEBAR DATA ====== */
const overallProgress = computed(() => {
  if (!all.value.length) return 0
  const total = all.value.reduce((sum, c) => sum + c.progress, 0)
  return Math.round(total / all.value.length)
})

const overallDashOffset = computed(() => {
  const circumference = 2 * Math.PI * 52
  const offset = circumference - (overallProgress.value / 100) * circumference
  return offset
})

const totalCoursesEnrolled = computed(() => all.value.length)
const totalLessonsCompleted = computed(() => {
  return all.value.reduce((sum, c) => {
    const d = detailsMap.value.get(String(c.id))
    if (!d) return sum
    const total = d.lessonsCount || d.sections?.reduce((a, s) => a + (s.lessons?.length || 0), 0) || 0
    const done = Math.round((c.progress / 100) * total)
    return sum + done
  }, 0)
})
const totalHoursLearned = computed(() => Math.round(totalLessonsCompleted.value * 0.5))

const weeklyLessons = ref(3)
const dailyMinutes = ref(45)

const recentCourses = computed(() => {
  return all.value
    .filter(c => !c.done && c.progress > 0)
    .slice(0, 3)
})

/* ====== ACTIONS ====== */
function openDetail(id: number | string){
  if (router.hasRoute('student-course-detail')) router.push({ name:'student-course-detail', params:{ id } })
  else router.push(`/student/courses/${id}`)
}

async function playFirst(id: number | string){
  let d = detailsMap.value.get(String(id))
  if (!d) {
    d = await courseService.detail(id)
    detailsMap.value.set(String(id), d)
  }
  const first = d.sections?.[0]?.lessons?.[0]?.id
  if (!first) return openDetail(id)
  if (router.hasRoute('student-course-player'))
    router.push({ name:'student-course-player', params:{ id, lessonId: first } })
  else
    router.push(`/student/courses/${id}/player/${first}`)
}

function enroll(id: number | string){
  if (router.hasRoute('student-payments-cart')) router.push({ name: 'student-payments-cart', query: { add: String(id) } })
  else router.push({ path: '/student/payments/cart', query: { add: String(id) } })
}

onMounted(load)
</script>

<style>
:root{
  --bg:#f6f7fb; --card:#fff; --text:#0f172a; --muted:#6b7280; --line:#e5e7eb;
  --accent:#16a34a; --brand:#0ea5e9; --warn:#f59e0b;
}
</style>

<style scoped>
.my-courses{ background:var(--bg); min-height:100vh; color:var(--text); }
.layout{ display:flex; max-width:1600px; margin:0 auto; gap:18px; }
.container{ flex:1; padding:18px; min-width:0; }

.header{ display:flex; justify-content:space-between; gap:12px; align-items:flex-start; }
.quick{ display:flex; gap:8px; }
h1{ font-size:28px; font-weight:800; margin:8px 0 6px; }
.lead{ color:var(--muted); max-width:760px; }

.tabs-tools{ margin-top:16px; display:flex; align-items:center; gap:12px; }
.tabs{ display:flex; gap:18px; }
.tab{ position:relative; background:transparent; border:0; font-weight:800; padding:10px 0; cursor:pointer; }
.tab.active::after{ content:''; position:absolute; left:0; right:0; bottom:-6px; height:3px; background:var(--brand); border-radius:3px; }

.tools{ margin-left:auto; display:flex; align-items:center; gap:10px; flex-wrap:wrap; }
.ghost{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:8px 10px; font-weight:700; cursor:pointer; }
.ghost.sm{padding:6px 10px; font-size:13px}
.search{ display:flex; align-items:center; gap:8px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:8px 12px; }
.search input{ border:0; outline:0; width:240px; }
.search svg{ width:18px; height:18px; stroke:#9ca3af; fill:none; stroke-width:2; }

.select{ position:relative; }
.select-btn{ display:flex; align-items:center; gap:8px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:8px 12px; cursor:pointer; font-weight:700; }
.select-btn svg{ width:16px; height:16px; fill:#6b7280; }
.select-menu{ position:absolute; top:42px; left:0; min-width:180px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:6px; box-shadow:0 8px 24px rgba(0,0,0,.06); z-index:10; }
.select-menu li{ padding:8px 10px; border-radius:8px; cursor:pointer; }
.select-menu li:hover{ background:#f3f4f6; }

.section{ margin-top:22px; }
.section-head{ display:flex; align-items:flex-end; justify-content:space-between; margin-bottom:10px; gap:8px; }
.section-head h3{ font-size:20px; font-weight:800; margin:0; }
.sub{ color:var(--muted); font-size:13px; }
.trophy{ color:var(--warn); font-weight:800; }
.rh{ display:flex; align-items:center; gap:8px; }

.grid{ display:grid; grid-template-columns:repeat(3, 1fr); gap:14px; }
.card{ background:#fff; border:1px solid var(--line); border-radius:16px; overflow:hidden; box-shadow:0 6px 14px rgba(15,23,42,.04); transition:transform .15s, box-shadow .15s; cursor:pointer; }
.card:hover{ transform:translateY(-2px); box-shadow:0 10px 22px rgba(15,23,42,.08); }
.thumb{ position:relative; aspect-ratio:16/9; background:#e5e7eb; }
.thumb img{ position:absolute; inset:0; width:100%; height:100%; object-fit:cover; }
.play{ position:absolute; right:12px; bottom:12px; width:40px; height:40px; border-radius:999px; background:var(--accent); border:1px solid var(--accent); color:#fff; display:grid; place-items:center; cursor:pointer; }
.play svg{ width:20px; height:20px; fill:#fff; }
.chip{
  position:absolute; left:10px; bottom:10px;
  background:#fff; border:1px solid var(--line); border-radius:999px; padding:4px 8px; font-size:12px; font-weight:700;
}

.meta{ padding:12px; display:flex; flex-direction:column; gap:10px; }
.title{ font-weight:800; line-height:1.35; }
.info{ display:flex; align-items:center; gap:8px; }
.state{ display:flex; align-items:center; gap:8px; font-weight:800; color:#f59e0b; }
.state .dot{ width:10px; height:10px; border-radius:50%; background:#f59e0b; }
.state.ok{ color:var(--accent); }
.state.ok .dot{ background:var(--accent); }
.score{ color:var(--warn); font-weight:800; display:flex; align-items:center; gap:6px; }
.score .emoji{ font-size:16px; }

.join-btn{
  margin-left:auto;
  min-width:108px;
  height:36px;
  padding:0 14px;
  border-radius:10px;
  display:inline-flex; align-items:center; justify-content:center;
  background:var(--accent); color:#fff; border:1px solid var(--accent);
  font-size:14px; font-weight:800; letter-spacing:.1px;
  box-shadow:0 2px 0 rgba(0,0,0,.06);
  transition:transform .08s ease, box-shadow .08s ease, filter .18s; cursor:pointer;
}
.join-btn:hover{ filter:brightness(0.96); }
.join-btn:active{ transform:translateY(1px); box-shadow:none; }
.join-btn:focus-visible{ outline:3px solid #bbf7d0; outline-offset:2px; }

.stats-bottom{ margin-top:20px; display:flex; justify-content:flex-end; }
.pill{ display:flex; align-items:center; gap:8px; padding:10px 12px; background:#fff; border:1px solid #e5e7eb; border-radius:999px; font-weight:800; }
.pill .emoji{ font-size:16px; }

.empty{ text-align:center; padding:40px 20px; color:var(--muted); }

/* ============ SIDEBAR TIẾN ĐỘ ============ */
.progress-sidebar{ 
  width:340px; 
  padding:18px 18px 18px 0; 
  display:flex; 
  flex-direction:column; 
  gap:14px;
  position:sticky;
  top:18px;
  height:fit-content;
  max-height:calc(100vh - 36px);
  overflow-y:auto;
  /* Hide scrollbar for all browsers */
  -ms-overflow-style:none; /* IE and Edge */
  scrollbar-width:none; /* Firefox */
}
.progress-sidebar::-webkit-scrollbar{ 
  display:none; /* Chrome, Safari, Opera */
}

.widget{ 
  background:#fff; 
  border:1px solid var(--line); 
  border-radius:16px; 
  padding:16px; 
  box-shadow:0 6px 14px rgba(15,23,42,.04);
}

.widget-header{ 
  display:flex; 
  align-items:center; 
  justify-content:space-between; 
  margin-bottom:14px;
}
.widget-header h4{ 
  font-size:16px; 
  font-weight:800; 
  margin:0;
}
.period{ 
  font-size:12px; 
  color:var(--muted); 
  font-weight:600;
}
.link-sm{ 
  font-size:13px; 
  font-weight:700; 
  color:var(--brand);
}

.icon-btn{
  background:transparent; 
  border:0; 
  padding:4px; 
  cursor:pointer; 
  display:grid; 
  place-items:center;
  border-radius:6px;
  transition:background .15s;
}
.icon-btn:hover{ background:#f3f4f6; }
.icon-btn svg{ 
  width:16px; 
  height:16px; 
  stroke:#6b7280; 
  fill:none; 
  stroke-width:2;
}

/* Overall Progress */
.overall-progress{ display:flex; flex-direction:column; gap:14px; align-items:center; }

.circle-progress{ 
  position:relative; 
  width:120px; 
  height:120px;
}
.progress-ring{ 
  transform:rotate(-90deg); 
  width:100%; 
  height:100%;
}
.ring-bg{ 
  fill:none; 
  stroke:#e5e7eb; 
  stroke-width:8;
}
.ring-fill{ 
  fill:none; 
  stroke:var(--accent); 
  stroke-width:8; 
  stroke-linecap:round;
  stroke-dasharray:326.73;
  transition:stroke-dashoffset .6s ease;
}
.progress-text{ 
  position:absolute; 
  inset:0; 
  display:flex; 
  flex-direction:column; 
  align-items:center; 
  justify-content:center;
}
.progress-text .pct{ 
  font-size:24px; 
  font-weight:800; 
  color:var(--accent);
}
.progress-text .label{ 
  font-size:11px; 
  color:var(--muted); 
  font-weight:600;
}

.stats-row{ 
  display:flex; 
  gap:16px; 
  width:100%;
  justify-content:space-around;
}
.stat-item{ 
  display:flex; 
  flex-direction:column; 
  align-items:center;
}
.stat-item .num{ 
  font-size:20px; 
  font-weight:800;
}
.stat-item .lbl{ 
  font-size:11px; 
  color:var(--muted); 
  font-weight:600;
}

/* Goals */
.goal-list{ display:flex; flex-direction:column; gap:12px; }
.goal-item{ display:flex; flex-direction:column; gap:6px; }
.goal-info{ 
  display:flex; 
  justify-content:space-between; 
  align-items:center;
}
.goal-label{ 
  font-size:13px; 
  font-weight:700;
}
.goal-progress{ 
  font-size:13px; 
  font-weight:800; 
  color:var(--brand);
}
.goal-bar{ 
  height:6px; 
  background:#e5e7eb; 
  border-radius:999px; 
  overflow:hidden;
}
.goal-fill{ 
  height:100%; 
  background:linear-gradient(90deg, var(--brand), var(--accent)); 
  border-radius:999px;
  transition:width .3s ease;
}

/* Recent Courses */
.recent-list{ display:flex; flex-direction:column; gap:10px; }
.recent-item{ 
  display:flex; 
  gap:10px; 
  padding:8px; 
  border-radius:10px; 
  transition:background .15s; 
  cursor:pointer;
}
.recent-item:hover{ background:#f9fafb; }
.recent-thumb{ 
  width:56px; 
  height:56px; 
  border-radius:8px; 
  overflow:hidden; 
  background:#e5e7eb; 
  flex-shrink:0;
}
.recent-thumb img{ 
  width:100%; 
  height:100%; 
  object-fit:cover;
}
.recent-info{ 
  flex:1; 
  display:flex; 
  flex-direction:column; 
  gap:6px; 
  min-width:0;
}
.recent-title{ 
  font-size:13px; 
  font-weight:700; 
  line-height:1.3; 
  overflow:hidden; 
  text-overflow:ellipsis; 
  display:-webkit-box; 
  -webkit-line-clamp:2; 
  -webkit-box-orient:vertical;
}
.recent-meta{ 
  display:flex; 
  align-items:center; 
  gap:8px;
}
.recent-progress{ 
  font-size:12px; 
  font-weight:800; 
  color:var(--brand); 
  white-space:nowrap;
}
.mini-bar{ 
  flex:1; 
  height:4px; 
  background:#e5e7eb; 
  border-radius:999px; 
  overflow:hidden;
}
.mini-fill{ 
  height:100%; 
  background:var(--accent); 
  border-radius:999px;
  transition:width .3s ease;
}

@media (max-width: 1400px){ 
  .layout{ max-width:100%; }
  .progress-sidebar{ width:300px; }
  .grid{ grid-template-columns:repeat(2, 1fr); }
}

@media (max-width: 1100px){ 
  .layout{ flex-direction:column; }
  .progress-sidebar{ 
    width:100%; 
    position:static; 
    max-height:none;
    padding:0 18px 18px;
    flex-direction:row;
    flex-wrap:wrap;
  }
  .widget{ flex:1; min-width:280px; }
  .grid{ grid-template-columns:repeat(3, 1fr); }
}

@media (max-width: 880px){
  .header{ flex-direction:column; }
  .grid{ grid-template-columns:repeat(2, 1fr); }
  .search input{ width:180px; }
  .join-btn{ min-width:100px; height:34px; padding:0 12px; }
  .progress-sidebar{ flex-direction:column; }
  .widget{ min-width:0; }
}

@media (max-width: 560px){
  .tabs-tools{ flex-direction:column; align-items:flex-start; gap:8px; }
  .grid{ grid-template-columns:1fr; }
}
</style>
