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
              Các khóa học bạn đang sở hữu được chia theo từng cấp trình độ, tương ứng với mỗi chặng
              mục tiêu. Hãy chọn trình độ mà bạn muốn bắt đầu nhé.
            </p>
          </div>

          <!-- Quick Links -->
          <div class="quick">
            <router-link class="ghost" :to="{ name: 'student-learning-path' }"
              >Lộ trình</router-link
            >
            <router-link class="ghost" :to="{ name: 'student-catalog' }">Tài liệu</router-link>
          </div>
        </div>

        <!-- Tabs + tools -->
        <div class="tabs-tools">
          <div class="tabs">
            <button
              class="tab"
              :class="{ active: activeTab === 'main' }"
              @click="activeTab = 'main'"
            >
              Khóa học của tôi
            </button>
            <button
              class="tab"
              :class="{ active: activeTab === 'supp' }"
              @click="activeTab = 'supp'"
            >
              Khóa học mở rộng
            </button>
          </div>

          <div class="tools">
            <div class="select" @mouseleave="open = false">
              <ul v-show="open" class="select-menu">
                <li @click="setLevel('')">Tất cả trình độ</li>
                <li @click="setLevel('Khối 1–2')">Khối 1–2</li>
                <li @click="setLevel('Khối 3–5')">Khối 3–5</li>
              </ul>
            </div>

            <div class="search">
              <svg viewBox="0 0 24 24">
                <path d="M21 21l-4.3-4.3" />
                <circle cx="11" cy="11" r="7" />
              </svg>
              <input v-model.trim="q" placeholder="Tìm khóa học..." />
            </div>
          </div>
        </div>

        <!-- ============ TAB: KHÓA HỌC CHÍNH ============ -->
        <template v-if="activeTab === 'main'">
          <!-- SECTION: Khối 1–2 -->
          <section class="section" v-if="baseList.length">
            <div class="section-head">
              <div>
                <h3>Khối 1–2 (Cơ bản)</h3>
                <span class="sub">{{ baseList.length }} môn</span>
              </div>
              <div class="rh">
                <span class="trophy"
                  >🏆 {{ getAnimatedTrophy(baseKey) }}/{{ baseTrophies.total }}</span
                >
                <button
                  class="ghost sm"
                  type="button"
                  @click="viewAllCourses"
                  :disabled="loadingAll"
                >
                  {{ loadingAll ? 'Đang tải...' : 'Xem tất cả ›' }}
                </button>
              </div>
            </div>

            <div class="grid">
              <article
                v-for="c in baseList"
                :key="`main-base-${activeTab}-${c.id}`"
                class="card"
                @click="playFirst(c.id)"
              >
                <div :class="['thumb', { loaded: isThumbLoaded(c.id) }]">
                  <img
                    :src="thumbSource(c.id, c.thumbnail)"
                    :alt="c.title"
                    loading="lazy"
                    @load="markThumbLoaded(c.id)"
                    @error="(e) => handleThumbError(e, c.id)"
                  />
                  <div v-if="isThumbMissing(c.id)" class="thumb-empty">Không có ảnh</div>
                  <button class="play" type="button" title="Vào học" @click.stop="playFirst(c.id)">
                    <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                  </button>
                </div>
                <div class="meta">
                  <div class="title">{{ c.title }}</div>
                  <div class="info">
                    <span class="state" :class="{ ok: c.done }">
                      <span class="dot"></span>
                      {{ c.done ? 'Đã hoàn thành' : 'Đang học'
                      }}<template v-if="!c.done">
                        · {{ getAnimatedProgress(c.id, c.progress) }}%
                      </template>
                    </span>
                    <span class="score"
                      ><span class="emoji">🏆</span>
                      {{ getAnimatedCourseTrophy(c.id, c.scoreEarned) }}/{{ c.scoreTotal }}</span
                    >
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
                <span class="trophy"
                  >🏆 {{ getAnimatedTrophy(midKey) }}/{{ midTrophies.total }}</span
                >
                <button
                  class="ghost sm"
                  type="button"
                  @click="viewAllCourses"
                  :disabled="loadingAll"
                >
                  {{ loadingAll ? 'Đang tải...' : 'Xem tất cả ›' }}
                </button>
              </div>
            </div>

            <div class="grid">
              <article
                v-for="c in midList"
                :key="`main-mid-${activeTab}-${c.id}`"
                class="card"
                @click="playFirst(c.id)"
              >
                <div :class="['thumb', { loaded: isThumbLoaded(c.id) }]">
                  <img
                    :src="thumbSource(c.id, c.thumbnail)"
                    :alt="c.title"
                    loading="lazy"
                    @load="markThumbLoaded(c.id)"
                    @error="(e) => handleThumbError(e, c.id)"
                  />
                  <div v-if="isThumbMissing(c.id)" class="thumb-empty">Không có ảnh</div>
                  <button class="play" type="button" title="Vào học" @click.stop="playFirst(c.id)">
                    <svg viewBox="0 0 24 24"><path d="M8 5v14l11-7z" /></svg>
                  </button>
                </div>
                <div class="meta">
                  <div class="title">{{ c.title }}</div>
                  <div class="info">
                    <span class="state" :class="{ ok: c.done }">
                      <span class="dot"></span>
                      {{ c.done ? 'Đã hoàn thành' : 'Đang học'
                      }}<template v-if="!c.done">
                        · {{ getAnimatedProgress(c.id, c.progress) }}%
                      </template>
                    </span>
                    <span class="score"
                      ><span class="emoji">🏆</span>
                      {{ getAnimatedCourseTrophy(c.id, c.scoreEarned) }}/{{ c.scoreTotal }}</span
                    >
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
            </div>

            <div class="grid">
              <article
                v-for="s in suppList"
                :key="`supp-${activeTab}-${s.id}`"
                class="card"
                @click="handleSuppEnroll(s)"
              >
                <div :class="['thumb', { loaded: isThumbLoaded(s.id) }]">
                  <img
                    :src="thumbSource(s.id, s.thumbnail)"
                    :alt="s.title"
                    loading="lazy"
                    @load="markThumbLoaded(s.id)"
                    @error="(e) => handleThumbError(e, s.id)"
                  />
                  <div v-if="isThumbMissing(s.id)" class="thumb-empty">Không có ảnh</div>
                  <span class="chip">{{ s.tag }}</span>
                </div>
                <div class="meta">
                  <div class="title">{{ s.title }}</div>
                  <div class="price-tag">{{ formatPrice(s.price) }}</div>
                  <div class="info">
                    <span class="state ok"
                      ><span class="dot"></span> Phù hợp {{ toLevelLabel(Number(s.grade)) }}</span
                    >
                    <button
                      class="join-btn"
                      :disabled="enrollingId === s.id"
                      @click.stop="handleSuppEnroll(s)"
                    >
                      <span>{{ enrollingId === s.id ? 'Đang đăng ký…' : 'Đăng ký' }}</span>
                    </button>
                  </div>
                </div>
              </article>
            </div>
          </section>
        </template>

        <!-- Tổng số cúp -->
        <div
          class="stats-bottom"
          v-if="activeTab === 'main' && (baseList.length || midList.length)"
        >
          <span class="pill"
            ><span class="emoji">🏆</span> Tổng số cúp đã đạt
            <b
              >{{ baseTrophies.earned + midTrophies.earned }}/{{
                baseTrophies.total + midTrophies.total
              }}</b
            ></span
          >
        </div>

        <div
          v-if="
            (activeTab === 'main' && baseList.length + midList.length === 0) ||
            (activeTab === 'supp' && !suppList.length)
          "
          class="empty"
        >
          Không có khóa học phù hợp.
        </div>

        <div v-if="err" class="empty" style="color: #b91c1c">{{ err }}</div>
      </div>

      <!-- ============ SIDEBAR TIẾN ĐỘ ============ -->
      <aside class="progress-sidebar" :key="activeTab">
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
                  :style="{ '--progress-offset': `${overallDashOffset}` }"
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
              <svg viewBox="0 0 24 24">
                <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
            </button>
          </div>

          <div class="goal-list">
            <div class="goal-item">
              <div class="goal-info">
                <span class="goal-label">Học 5 bài/tuần</span>
                <span class="goal-progress">{{ weeklyLessons }}/5</span>
              </div>
              <div class="goal-bar">
                <div
                  class="goal-fill"
                  :style="{
                    '--progress-target': Math.min(100, (weeklyLessons / 5) * 100) + '%',
                  }"
                ></div>
              </div>
            </div>

            <div class="goal-item">
              <div class="goal-info">
                <span class="goal-label">60 phút/ngày</span>
                <span class="goal-progress">{{ dailyMinutes }}/60</span>
              </div>
              <div class="goal-bar">
                <div
                  class="goal-fill"
                  :style="{
                    '--progress-target': Math.min(100, (dailyMinutes / 60) * 100) + '%',
                  }"
                ></div>
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
              @click="playFirst(c.id)"
            >
              <div :class="['recent-thumb', { loaded: isThumbLoaded(c.id) }]">
                <img
                  :src="thumbSource(c.id, c.thumbnail)"
                  :alt="c.title"
                  loading="lazy"
                  @load="markThumbLoaded(c.id)"
                  @error="(e) => handleThumbError(e, c.id)"
                />
                <div v-if="isThumbMissing(c.id)" class="thumb-empty">Không có ảnh</div>
              </div>
              <div class="recent-info">
                <div class="recent-title">{{ c.title }}</div>
                <div class="recent-meta">
                  <span class="recent-progress">{{ getAnimatedProgress(c.id, c.progress) }}%</span>
                  <div class="mini-bar">
                    <div
                      class="mini-fill"
                      :style="{ '--progress-target': Math.min(100, c.progress) + '%' }"
                    ></div>
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
import { computed, ref, onMounted, watch, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  courseService,
  type CourseSummary,
  type CourseDetail,
  type CourseStatus,
  type ID,
  resolveMediaUrl,
} from '@/services/course.service'

const router = useRouter()

/* Tabs */
const activeTab = ref<'main' | 'supp'>('main')

/* Tìm kiếm / lọc */
const q = ref('')
const level = ref<'' | 'Khối 1–2' | 'Khối 3–5'>('')
const open = ref(false)
function setLevel(v: '' | 'Khối 1–2' | 'Khối 3–5') {
  level.value = v
  open.value = false
}

const err = ref('')
const loading = ref(false)
const loadingAll = ref(false)
const enrollingId = ref<string | number | null>(null)
const PREFETCH_DETAIL_LIMIT = 0
const thumbLoaded = ref<Record<string, boolean>>({})
const thumbSrc = ref<Record<string, string>>({})
const thumbMissing = ref<Record<string, boolean>>({})
const PLACEHOLDER =
  'data:image/svg+xml;utf8,' +
  encodeURIComponent(
    `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 225" width="400" height="225">
      <defs>
        <linearGradient id="g" x1="0" x2="1" y1="0" y2="1">
          <stop stop-color="#e2e8f0" offset="0%"/>
          <stop stop-color="#cbd5e1" offset="100%"/>
        </linearGradient>
      </defs>
      <rect width="400" height="225" fill="url(#g)"/>
      <text x="200" y="118" font-size="22" font-family="Arial, sans-serif" fill="#475569" text-anchor="middle">Không có ảnh</text>
    </svg>`,
  )

/* ====== LOAD COURSES FROM SERVICE ====== */
export interface CourseSummary {
  id: ID
  title: string
  thumbnail?: string | null
  grade: number
  subject?: string
  subjectName?: string
  my_progress?: MyProgress
}

const all = ref<CourseSummary[]>([])
const detailsMap = ref(new Map<string, CourseDetail>())
const animatedProgressMap = reactive<Record<string, number>>({})
const progressFrameMap = new Map<string, number>()
const animatedCourseTrophiesMap = reactive<Record<string, number>>({})
const courseTrophyFrameMap = new Map<string, number>()
const trophyTarget = reactive<Record<string, number>>({ base: 0, mid: 0 })
const trophyAnimated = reactive<Record<string, number>>({ base: 0, mid: 0 })
const trophyFrameMap = new Map<string, number>()
const suppCourses = ref<CourseSummary[]>([])

export interface MyProgress {
  enrollment_id: string
  percent_completed: number
  is_completed: boolean
  status_label: 'not_started' | 'in_progress' | 'completed'
  last_accessed_at?: string
}

function markThumbLoaded(id: ID) {
  thumbLoaded.value = { ...thumbLoaded.value, [String(id)]: true }
}
function isThumbLoaded(id: ID) {
  return Boolean(thumbLoaded.value[String(id)])
}
function isThumbMissing(id: ID) {
  return Boolean(thumbMissing.value[String(id)])
}
function markThumbMissing(id: ID) {
  const key = String(id)
  thumbMissing.value = { ...thumbMissing.value, [key]: true }
  thumbSrc.value = { ...thumbSrc.value, [key]: PLACEHOLDER }
  thumbLoaded.value = { ...thumbLoaded.value, [key]: true }
}
function handleThumbError(event: Event, id: ID) {
  const img = event.target as HTMLImageElement | null
  if (img) img.style.opacity = '0'
  markThumbMissing(id)
  markThumbLoaded(id)
}
async function ensureThumb(id: ID, url?: string | null) {
  const key = String(id)
  if (!url) {
    markThumbMissing(id)
    return
  }
  if (thumbSrc.value[key]) return
  try {
    const resolved = await resolveMediaUrl(url)
    if (resolved) {
      thumbSrc.value = { ...thumbSrc.value, [key]: resolved }
    } else {
      markThumbMissing(id)
    }
  } catch (error) {
    console.warn('Không thể tải ảnh khoá học', error)
    markThumbMissing(id)
  }
}
function thumbSource(id: ID, fallback?: string | null) {
  return thumbSrc.value[String(id)] || fallback || PLACEHOLDER
}

function getAnimatedProgress(id: number | string, fallback: number) {
  const val = animatedProgressMap[String(id)]
  return val == null ? fallback : val
}

function animateCourseProgress(id: number | string, target: number) {
  const key = String(id)
  if (progressFrameMap.has(key)) {
    cancelAnimationFrame(progressFrameMap.get(key)!)
    progressFrameMap.delete(key)
  }
  const start = animatedProgressMap[key] ?? 0
  const duration = 700
  const startTime = typeof performance !== 'undefined' ? performance.now() : Date.now()

  const step = (now: number) => {
    const elapsed = now - startTime
    const progress = Math.min(elapsed / duration, 1)
    animatedProgressMap[key] = Math.round(start + (target - start) * progress)
    if (progress < 1) {
      progressFrameMap.set(key, requestAnimationFrame(step))
    } else {
      progressFrameMap.delete(key)
    }
  }

  progressFrameMap.set(key, requestAnimationFrame(step))
}

function getAnimatedCourseTrophy(id: number | string, fallback: number) {
  const val = animatedCourseTrophiesMap[String(id)]
  return val == null ? fallback : val
}

function animateCourseTrophy(id: number | string, target: number) {
  const key = String(id)
  if (courseTrophyFrameMap.has(key)) {
    cancelAnimationFrame(courseTrophyFrameMap.get(key)!)
    courseTrophyFrameMap.delete(key)
  }
  const start = animatedCourseTrophiesMap[key] ?? 0
  const duration = 700
  const startTime = typeof performance !== 'undefined' ? performance.now() : Date.now()

  const step = (now: number) => {
    const progress = Math.min((now - startTime) / duration, 1)
    animatedCourseTrophiesMap[key] = Math.round(start + (target - start) * progress)
    if (progress < 1) {
      courseTrophyFrameMap.set(key, requestAnimationFrame(step))
    } else {
      courseTrophyFrameMap.delete(key)
    }
  }

  courseTrophyFrameMap.set(key, requestAnimationFrame(step))
}

function toLevelLabel(grade: number) {
  return grade <= 2 ? 'Khối 1–2' : 'Khối 3–5'
}

function formatPrice(price?: number | null) {
  if (price == null || Number(price) === 0) return 'Miễn phí'
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(Number(price))
}

function formatSubjectLabel(course?: CourseSummary | Item | null) {
  if (!course) return 'Môn học'
  if (course.subjectName) return course.subjectName
  if (typeof course.subject === 'string' && course.subject.trim().length) return course.subject
  return 'Môn học'
}

function calcScore(progress: number) {
  const earned = Math.max(0, Math.min(5, Math.round(progress / 20)))
  return { earned, total: 5 }
}

function calcProgressFromDetail(d: CourseDetail, id: number | string) {
  const total = d.lessonsCount || d.sections?.reduce((a, s) => a + (s.lessons?.length || 0), 0) || 0
  let done = Number(id) % (total || 1)
  if (total > 0 && done === 0) done = total
  const pct = total ? Math.round((done / total) * 100) : 0
  return Math.max(0, Math.min(100, pct))
}

async function hydrateCourses(items: CourseSummary[]) {
  all.value = (items || []).map((i) => {
    const pct = i.my_progress?.percent_completed ?? 0

    const scoreInfo = calcScore(pct)

    return {
      ...i,
      progress: Math.round(pct), // ✅ SOURCE OF TRUTH
      done: Boolean(i.my_progress?.is_completed),
      scoreEarned: scoreInfo.earned,
      scoreTotal: scoreInfo.total,
    }
  })

  await Promise.all(all.value.map((i) => ensureThumb(i.id, i.thumbnail)))
}

async function load(fetchAll = false) {
  try {
    err.value = ''
    loading.value = true
    loadingAll.value = fetchAll

    let enrolledItems: CourseSummary[] = []
    try {
      enrolledItems = await courseService.listMyEnrolled()
    } catch (error) {
      console.warn('Không tải được danh sách khoá học đã đăng ký, fallback list()', error)
      const fallback = await courseService.list({
        page: 1,
        pageSize: fetchAll ? 200 : 20,
        status: 'published' as CourseStatus,
        sortBy: 'updatedAt' as const,
        sortDir: 'descending' as const,
      })
      enrolledItems = fallback.items || []
    }

    await hydrateCourses(enrolledItems)

    const enrolledIds = new Set(all.value.map((c) => String(c.id)))

    let catalogItems: CourseSummary[] = []
    try {
      const publicRes = await courseService.listPublicCatalog()
      catalogItems = publicRes.items
    } catch (error) {
      console.warn('Không tải được catalog công khai, fallback list()', error)
      const fallback = await courseService.list({
        page: 1,
        pageSize: fetchAll ? 200 : 40,
        status: 'published' as CourseStatus,
        sortBy: 'updatedAt' as const,
        sortDir: 'descending' as const,
      })
      catalogItems = fallback.items || []
    }

    const supplementary = catalogItems.filter((c) => !enrolledIds.has(String(c.id)))
    suppCourses.value = supplementary
    await Promise.all(supplementary.map((c) => ensureThumb(c.id, c.thumbnail)))
  } catch (e: any) {
    err.value = e?.message || String(e)
  } finally {
    loading.value = false
    loadingAll.value = false
  }
}

async function viewAllCourses() {
  if (loadingAll.value) return
  if (router.hasRoute('student-courses-all')) {
    router.push({ name: 'student-courses-all' })
    return
  }
  // Fallback: hiển thị toàn bộ tại chỗ nếu route chưa khai báo
  level.value = ''
  q.value = ''
  await load(true)
}

watch(
  all,
  (list) => {
    list.forEach((course) => {
      animateCourseProgress(course.id, course.progress)
      animateCourseTrophy(course.id, course.scoreEarned)
    })
  },
  { deep: true },
)

/* ====== FILTERING ====== */
const filteredMain = computed(() => {
  let arr = all.value.slice()
  if (q.value) {
    const key = q.value.toLowerCase()
    arr = arr.filter((x) => x.title.toLowerCase().includes(key))
  }
  if (level.value) {
    arr = arr.filter((x) => toLevelLabel(x.grade) === level.value)
  }
  return arr
})
const baseList = computed(() => filteredMain.value.filter((x) => x.grade <= 2))
const midList = computed(() => filteredMain.value.filter((x) => x.grade >= 3))
function parseScore(item: Item) {
  return { earned: item.scoreEarned || 0, total: item.scoreTotal || 0 }
}
function sumTrophies(list: Item[]) {
  return list.reduce(
    (acc, c) => {
      const s = parseScore(c)
      acc.earned += s.earned
      acc.total += s.total
      return acc
    },
    { earned: 0, total: 0 },
  )
}
const baseTrophies = computed(() => sumTrophies(baseList.value))
const midTrophies = computed(() => sumTrophies(midList.value))
const baseKey = 'base'
const midKey = 'mid'

function animateTrophies(key: 'base' | 'mid', target: number) {
  if (trophyFrameMap.has(key)) {
    cancelAnimationFrame(trophyFrameMap.get(key)!)
    trophyFrameMap.delete(key)
  }
  const start = trophyAnimated[key]
  const duration = 700
  const startTime = typeof performance !== 'undefined' ? performance.now() : Date.now()
  const step = (now: number) => {
    const progress = Math.min((now - startTime) / duration, 1)
    trophyAnimated[key] = Math.round(start + (target - start) * progress)
    if (progress < 1) trophyFrameMap.set(key, requestAnimationFrame(step))
    else trophyFrameMap.delete(key)
  }
  trophyFrameMap.set(key, requestAnimationFrame(step))
}

watch(baseTrophies, (val) => {
  trophyTarget.base = val.earned
  animateTrophies('base', val.earned)
})
watch(midTrophies, (val) => {
  trophyTarget.mid = val.earned
  animateTrophies('mid', val.earned)
})

function getAnimatedTrophy(key: 'base' | 'mid') {
  return trophyAnimated[key] ?? 0
}

/** Supp tab */
const suppList = computed(() => {
  let arr = suppCourses.value.slice().map((c) => ({
    ...c,
    tag: c.subjectName || c.subject?.toString()?.toUpperCase() || 'Bổ trợ',
  }))
  if (level.value) arr = arr.filter((s) => toLevelLabel(Number(s.grade)) === level.value)
  if (q.value) {
    const key = q.value.toLowerCase()
    arr = arr.filter(
      (s) => s.title.toLowerCase().includes(key) || (s.tag || '').toLowerCase().includes(key),
    )
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
    const total =
      d.lessonsCount || d.sections?.reduce((a, s) => a + (s.lessons?.length || 0), 0) || 0
    const done = Math.round((c.progress / 100) * total)
    return sum + done
  }, 0)
})
const totalHoursLearned = computed(() => Math.round(totalLessonsCompleted.value * 0.5))

const weeklyLessons = ref(3)
const dailyMinutes = ref(45)

const recentCourses = computed(() => {
  return all.value.filter((c) => !c.done && c.progress > 0).slice(0, 3)
})

/* ====== ACTIONS ====== */
function openDetail(id: number | string) {
  if (router.hasRoute('student-course-detail'))
    router.push({ name: 'student-course-detail', params: { id } })
  else router.push(`/student/courses/${id}`)
}

async function playFirst(id: number | string) {
  try {
    console.log('[playFirst] Bắt đầu mở khóa học:', id)
    let d = detailsMap.value.get(String(id))
    if (!d) {
      console.log('[playFirst] Chưa có detail, đang tải...')
      try {
        d = await courseService.detail(id)
        detailsMap.value.set(String(id), d)
        console.log('[playFirst] Đã tải detail thành công:', d)
      } catch (error) {
        console.error('[playFirst] Không thể tải chi tiết khóa học:', error)
        ElMessage.error('Không thể tải thông tin khóa học. Vui lòng thử lại.')
        return
      }
    } else {
      console.log('[playFirst] Đã có detail trong cache')
    }

    // Tìm lesson đầu tiên
    let firstLessonId: string | number | null = null
    if (d.sections && d.sections.length > 0) {
      console.log('[playFirst] Có', d.sections.length, 'sections')
      for (const section of d.sections) {
        if (section.lessons && section.lessons.length > 0) {
          firstLessonId = section.lessons[0].id
          console.log('[playFirst] Tìm thấy lesson đầu tiên:', firstLessonId)
          break
        }
      }
    } else {
      console.warn('[playFirst] Không có sections hoặc sections rỗng')
    }

    if (!firstLessonId) {
      console.warn('[playFirst] Không tìm thấy lesson, chuyển đến detail page')
      ElMessage.warning('Khóa học này chưa có bài học nào.')
      openDetail(id)
      return
    }

    // Điều hướng đến player
    const routeName = 'student-course-player'
    const routePath = `/student/courses/${id}/player/${firstLessonId}`
    console.log('[playFirst] Điều hướng đến player:', {
      routeName,
      routePath,
      id,
      lessonId: firstLessonId,
    })

    if (router.hasRoute(routeName)) {
      router.push({ name: routeName, params: { id, lessonId: firstLessonId } })
    } else {
      router.push(routePath)
    }
  } catch (error: any) {
    console.error('[playFirst] Lỗi khi mở khóa học:', error)
    ElMessage.error('Không thể mở khóa học. Vui lòng thử lại.')
  }
}

async function enroll(id: number | string): Promise<boolean> {
  if (enrollingId.value === id) return false
  enrollingId.value = id
  try {
    await courseService.enroll(id)
    ElMessage.success('Đăng ký khoá học thành công')
    await load()
    return true
  } catch (e: any) {
    const message =
      e?.response?.data?.detail || e?.message || 'Không thể đăng ký khoá học, vui lòng thử lại.'
    ElMessage.error(message)
    return false
  } finally {
    enrollingId.value = null
  }
}

async function handleSuppEnroll(course: CourseSummary | Item) {
  if (!course) return
  // Tự động đăng ký và vào học luôn
  const success = await enroll(course.id)
  if (success) {
    await playFirst(course.id)
  }
}

onMounted(load)
</script>

<style>
:root {
  --bg: #f6f7fb;
  --card: #fff;
  --text: #0f172a;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #16a34a;
  --brand: #0ea5e9;
  --warn: #f59e0b;
}
</style>

<style scoped>
.my-courses {
  background: var(--bg);
  min-height: 100vh;
  color: var(--text);
}
.layout {
  display: flex;
  max-width: 1600px;
  margin: 0 auto;
  gap: clamp(16px, 2vw, 28px);
  align-items: flex-start;
}
.container {
  flex: 1;
  padding: 18px;
  min-width: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: flex-start;
}
.quick {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}
.quick .ghost {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 6px 12px;
  height: 34px;
  text-align: center;
  white-space: nowrap;
  font-size: 13px;
}
h1 {
  font-size: 28px;
  font-weight: 800;
  margin: 8px 0 6px;
}
.lead {
  color: var(--muted);
  max-width: 760px;
}

.tabs-tools {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}
.tabs {
  display: flex;
  gap: 18px;
}
.tab {
  position: relative;
  background: transparent;
  border: 0;
  font-weight: 800;
  padding: 10px 0;
  cursor: pointer;
}
.tab.active::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -6px;
  height: 3px;
  background: var(--brand);
  border-radius: 3px;
}

.tools {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.ghost {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 8px 10px;
  font-weight: 700;
  cursor: pointer;
}
.ghost:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
.ghost.sm {
  padding: 6px 10px;
  font-size: 13px;
}
.search {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 8px 12px;
}
.search input {
  border: 0;
  outline: 0;
  width: 240px;
}
.search svg {
  width: 18px;
  height: 18px;
  stroke: #9ca3af;
  fill: none;
  stroke-width: 2;
}

.select {
  position: relative;
}
.select-menu {
  position: absolute;
  top: 42px;
  left: 0;
  min-width: 180px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 6px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.06);
  z-index: 10;
}
.select-menu li {
  padding: 8px 10px;
  border-radius: 8px;
  cursor: pointer;
}
.select-menu li:hover {
  background: #f3f4f6;
}

.section {
  margin-top: 22px;
}
.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 10px;
  gap: 8px;
}
.section-head h3 {
  font-size: 20px;
  font-weight: 800;
  margin: 0;
}
.sub {
  color: var(--muted);
  font-size: 13px;
}
.trophy {
  color: var(--warn);
  font-weight: 800;
}
.rh {
  display: flex;
  align-items: center;
  gap: 8px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
}
.card {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.04);
  transition:
    transform 0.15s,
    box-shadow 0.15s;
  cursor: pointer;
}
.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.08);
}
.thumb {
  position: relative;
  aspect-ratio: 16/9;
  background: #e5e7eb;
  overflow: hidden;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}
.thumb img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.25s ease;
}
.thumb.loaded img {
  opacity: 1;
}
.thumb::before,
.thumb::after {
  content: '';
  position: absolute;
  inset: 0;
}
.thumb::before {
  background: rgba(255, 255, 255, 0.35);
}
.thumb::after {
  width: 26px;
  height: 26px;
  border: 3px solid #cbd5f5;
  border-top-color: #16a34a;
  border-radius: 999px;
  animation: spin 0.9s linear infinite;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.thumb.loaded::before,
.thumb.loaded::after {
  opacity: 0;
  visibility: hidden;
}
.thumb-empty {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e2e8f0, #cbd5e1);
  color: #475569;
  font-weight: 600;
  font-size: 14px;
  border-top-left-radius: 16px;
  border-top-right-radius: 16px;
}
.play {
  position: absolute;
  right: 12px;
  bottom: 12px;
  width: 40px;
  height: 40px;
  border-radius: 999px;
  background: var(--accent);
  border: 1px solid var(--accent);
  color: #fff;
  display: grid;
  place-items: center;
  cursor: pointer;
  z-index: 2;
}
.play svg {
  width: 20px;
  height: 20px;
  fill: #fff;
}
.chip {
  position: absolute;
  left: 10px;
  bottom: 10px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: 4px 8px;
  font-size: 12px;
  font-weight: 700;
}

.meta {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.price-tag {
  font-weight: 800;
  color: #0ea5e9;
  font-size: 13px;
}
.title {
  font-weight: 800;
  line-height: 1.35;
}
.info {
  display: flex;
  align-items: center;
  gap: 8px;
}
.state {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 800;
  color: #f59e0b;
}
.state .dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #f59e0b;
}
.state.ok {
  color: var(--accent);
}
.state.ok .dot {
  background: var(--accent);
}
.score {
  color: var(--warn);
  font-weight: 800;
  display: flex;
  align-items: center;
  gap: 6px;
}
.score .emoji {
  font-size: 16px;
}

.join-btn {
  margin-left: auto;
  min-width: 108px;
  height: 36px;
  padding: 0 14px;
  border-radius: 10px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: var(--accent);
  color: #fff;
  border: 1px solid var(--accent);
  font-size: 14px;
  font-weight: 800;
  letter-spacing: 0.1px;
  box-shadow: 0 2px 0 rgba(0, 0, 0, 0.06);
  transition:
    transform 0.08s ease,
    box-shadow 0.08s ease,
    filter 0.18s;
  cursor: pointer;
}
.join-btn:hover {
  filter: brightness(0.96);
}
.join-btn:active {
  transform: translateY(1px);
  box-shadow: none;
}
.join-btn:focus-visible {
  outline: 3px solid #bbf7d0;
  outline-offset: 2px;
}
.join-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  filter: grayscale(0.1);
  box-shadow: none;
}

.stats-bottom {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}
.pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  font-weight: 800;
}
.pill .emoji {
  font-size: 16px;
}

.empty {
  text-align: center;
  padding: 40px 20px;
  color: var(--muted);
}

/* ============ SIDEBAR TIẾN ĐỘ ============ */
.progress-sidebar {
  flex: 0 0 clamp(240px, 22vw, 320px);
  min-width: clamp(240px, 22vw, 320px);
  width: clamp(240px, 22vw, 320px);
  padding: 18px 18px 18px 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
  position: sticky;
  top: 18px;
  height: fit-content;
  max-height: calc(100vh - 36px);
  overflow-y: auto;
  /* Hide scrollbar for all browsers */
  -ms-overflow-style: none; /* IE and Edge */
  scrollbar-width: none; /* Firefox */
}
.progress-sidebar::-webkit-scrollbar {
  display: none; /* Chrome, Safari, Opera */
}

.widget {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 16px;
  padding: 16px;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.04);
}

.widget-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;
}
.widget-header h4 {
  font-size: 16px;
  font-weight: 800;
  margin: 0;
}
.period {
  font-size: 12px;
  color: var(--muted);
  font-weight: 600;
}
.link-sm {
  font-size: 13px;
  font-weight: 700;
  color: var(--brand);
}

.icon-btn {
  background: transparent;
  border: 0;
  padding: 4px;
  cursor: pointer;
  display: grid;
  place-items: center;
  border-radius: 6px;
  transition: background 0.15s;
}
.icon-btn:hover {
  background: #f3f4f6;
}
.icon-btn svg {
  width: 16px;
  height: 16px;
  stroke: #6b7280;
  fill: none;
  stroke-width: 2;
}

/* Overall Progress */
.overall-progress {
  display: flex;
  flex-direction: column;
  gap: 12px;
  align-items: center;
}

.circle-progress {
  position: relative;
  width: 100px;
  height: 100px;
}
.progress-ring {
  transform: rotate(-90deg);
  width: 100%;
  height: 100%;
}
.ring-bg {
  fill: none;
  stroke: #e5e7eb;
  stroke-width: 6;
}
.ring-fill {
  fill: none;
  stroke: var(--accent);
  stroke-width: 6;
  stroke-linecap: round;
  stroke-dasharray: 326.73;
  stroke-dashoffset: var(--progress-offset, 326.73);
  animation: ringFill 1.1s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}
.progress-text {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.progress-text .pct {
  font-size: 20px;
  font-weight: 800;
  color: var(--accent);
}
.progress-text .label {
  font-size: 10px;
  color: var(--muted);
  font-weight: 600;
}

.stats-row {
  display: flex;
  gap: 20px;
  width: 100%;
  justify-content: space-around;
}
.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.stat-item .num {
  font-size: 18px;
  font-weight: 800;
  color: var(--text);
}
.stat-item .lbl {
  font-size: 11px;
  color: var(--muted);
  font-weight: 600;
}

/* Goals */
.goal-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.goal-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.goal-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.goal-label {
  font-size: 13px;
  font-weight: 700;
}
.goal-progress {
  font-size: 13px;
  font-weight: 800;
  color: var(--brand);
}
.goal-bar {
  height: 6px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}
.goal-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--brand), var(--accent));
  border-radius: 999px;
  width: var(--progress-target, 0%);
  animation: barFill 0.9s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

/* Recent Courses */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.recent-item {
  display: flex;
  gap: 10px;
  padding: 8px;
  border-radius: 10px;
  transition: background 0.15s;
  cursor: pointer;
}
.recent-item:hover {
  background: #f9fafb;
}
.recent-thumb {
  width: 56px;
  height: 56px;
  border-radius: 8px;
  overflow: hidden;
  background: #e5e7eb;
  flex-shrink: 0;
  position: relative;
}
.recent-thumb img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  opacity: 0;
  transition: opacity 0.25s ease;
}
.recent-thumb.loaded img {
  opacity: 1;
}
.recent-thumb::before,
.recent-thumb::after {
  content: '';
  position: absolute;
  inset: 0;
}
.recent-thumb::before {
  background: rgba(255, 255, 255, 0.3);
}
.recent-thumb::after {
  width: 18px;
  height: 18px;
  border: 2px solid #cbd5f5;
  border-top-color: #16a34a;
  border-radius: 999px;
  animation: spin 0.9s linear infinite;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
}
.recent-thumb.loaded::before,
.recent-thumb.loaded::after {
  opacity: 0;
  visibility: hidden;
}
.recent-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}
.recent-title {
  font-size: 13px;
  font-weight: 700;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
}
.recent-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}
.recent-progress {
  font-size: 12px;
  font-weight: 800;
  color: var(--brand);
  white-space: nowrap;
}
.mini-bar {
  flex: 1;
  height: 4px;
  background: #e5e7eb;
  border-radius: 999px;
  overflow: hidden;
}
.mini-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 999px;
  width: var(--progress-target, 0%);
  animation: barFill 0.9s cubic-bezier(0.4, 0, 0.2, 1) forwards;
}

@keyframes ringFill {
  from {
    stroke-dashoffset: 326.73;
  }
  to {
    stroke-dashoffset: var(--progress-offset, 326.73);
  }
}
@keyframes barFill {
  from {
    width: 0;
  }
  to {
    width: var(--progress-target, 0%);
  }
}

@keyframes spin {
  to {
    transform: translate(-50%, -50%) rotate(360deg);
  }
}

@media (max-width: 1400px) {
  .layout {
    max-width: 100%;
  }
  .progress-sidebar {
    flex: 0 0 clamp(240px, 24vw, 300px);
    min-width: clamp(240px, 24vw, 300px);
    width: clamp(240px, 24vw, 300px);
  }
  .grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 1280px) {
  .layout {
    flex-direction: column;
  }
  .progress-sidebar {
    width: 100%;
    flex: 1 1 100%;
    position: static;
    max-height: none;
    padding: 0 18px 18px;
    flex-direction: row;
    flex-wrap: wrap;
  }
  .widget {
    flex: 1;
    min-width: 280px;
  }
  .grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 880px) {
  .header {
    flex-direction: column;
    gap: 16px;
  }
  .header h1 {
    font-size: 1.75rem;
  }
  .quick {
    width: 100%;
  }
  .grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
  .search input {
    width: 180px;
  }
  .join-btn {
    min-width: 100px;
    height: 34px;
    padding: 0 12px;
    font-size: 0.875rem;
  }
  .progress-sidebar {
    flex-direction: column;
  }
  .widget {
    min-width: 0;
  }
  .tabs {
    width: 100%;
  }
  .tab {
    flex: 1;
  }
}

@media (max-width: 560px) {
  .tabs-tools {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  .tools {
    width: 100%;
    flex-direction: column;
    align-items: stretch;
  }
  .search {
    width: 100%;
  }
  .search input {
    width: 100%;
  }
  .select {
    width: 100%;
  }
  .grid {
    grid-template-columns: 1fr;
  }
  .header h1 {
    font-size: 1.5rem;
  }
  .header .lead {
    font-size: 0.875rem;
  }
  .quick {
    width: 100%;
    justify-content: stretch;
  }
  .quick .ghost {
    flex: 1;
    text-align: center;
  }
  .section-head {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  .rh {
    width: 100%;
    justify-content: space-between;
  }
  .card .title {
    font-size: 0.875rem;
  }
  .card .info {
    font-size: 0.75rem;
  }
}
</style>
