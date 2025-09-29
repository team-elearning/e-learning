<!-- src/pages/student/learn/LessonPlayer.vue -->
<template>
  <div class="lesson-player" v-if="course">
    <div class="container">
      <!-- TOP BAR -->
      <div class="topbar">
        <button class="link" @click="goBack">Rời khỏi đây</button>
        <div class="spacer" />
      </div>

      <div class="content">
        <!-- LEFT: VIDEO -->
        <div class="left">
          <div class="video-shell">
            <video
              ref="videoRef"
              class="video"
              :src="currentSrc"
              controls
              playsinline
              @ended="markDone(currentLesson?.id)"
            ></video>

            <div class="video-title">
              <h2>{{ course.title }}</h2>
              <p class="subtitle">
                {{ (currentFlatIndex + 1) }}. {{ currentLesson?.title }}
              </p>
            </div>
          </div>

          <!-- BOTTOM NAV -->
          <div class="bottom-nav">
            <button class="btn bw" :disabled="!prevLesson" @click="goPrev">‹ BÀI TRƯỚC</button>
            <div class="actions"></div>
            <button class="btn bw" :disabled="!nextLesson" @click="goNext">BÀI TIẾP THEO ›</button>
          </div>
        </div>

        <!-- RIGHT: OUTLINE -->
        <aside class="right">
          <div class="panel">
            <!-- Progress header -->
            <div class="progress-head">
              <div class="circle">
                <svg viewBox="0 0 36 36" class="c">
                  <path class="bg" d="M18 2a16 16 0 1 1 0 32a16 16 0 1 1 0-32"/>
                  <path class="fg" :style="{ strokeDasharray: dash + ', 100' }"
                        d="M18 2a16 16 0 1 1 0 32a16 16 0 1 1 0-32"/>
                </svg>
                <div class="pct">{{ progressPct }}%</div>
              </div>
              <div class="meta">
                <h4>Nội dung khóa học</h4>
                <div class="sub">{{ doneCount }}/{{ totalCount }} bài học</div>
              </div>
            </div>

            <!-- Outline -->
            <div class="outline" ref="outlineRef">
              <div v-for="(sec, si) in uiSections" :key="sec.id" class="sec">
                <button class="sec-head" @click="toggle(si)">
                  <span class="name">{{ si + 1 }}. {{ sec.title }}</span>
                  <span class="len">{{ sec.items.length }}</span>
                  <svg class="chev" viewBox="0 0 24 24" :class="{open: openIndex === si}">
                    <path d="M6 9l6 6 6-6"/>
                  </svg>
                </button>

                <transition name="acc">
                  <ul v-show="openIndex === si">
                    <li v-for="(it, li) in sec.items"
                        :key="it.id"
                        :class="['row', {active: String(it.id)===String(currentLesson?.id), done: it.done}]"
                        @click="goToLesson(si, li)">
                      <div class="leftcell">
                        <span class="idx">{{ li + 1 }}</span>
                        <span class="title">{{ it.title }}</span>
                      </div>
                      <div class="rightcell">
                        <span class="time">{{ formatDuration(it.durationMinutes) }}</span>
                        <span class="state">
                          <svg v-if="it.done" viewBox="0 0 24 24"><path d="M20 6L9 17l-5-5"/></svg>
                        </span>
                      </div>
                    </li>
                  </ul>
                </transition>
              </div>
            </div>
          </div>
        </aside>
      </div>
    </div>
  </div>

  <div v-else class="grid min-h-screen place-items-center text-slate-200">Đang tải…</div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watchEffect } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { courseService, type CourseDetail, type Lesson as ApiLesson } from '@/services/course.service'

const router = useRouter()
const route = useRoute()

/* ====== STATE ====== */
const course = ref<CourseDetail | null>(null)
const videoRef = ref<HTMLVideoElement|null>(null)
const doneSet = reactive(new Set<string>())               // local progress
const showNonVideoInOutline = true                       // ẩn/hiện PDF/Quiz
const openIndex = ref<number>(0)
const cur = ref<{ si: number; li: number }>({ si: 0, li: 0 })

/* ====== LOAD ====== */
async function load() {
  const id = route.params.id as any
  const lessonParam = route.params.lessonId as any

  const d = await courseService.detail(id)
  course.value = d

  // build và trỏ đúng bài
  rebuildAndKeepCursor(lessonParam ?? null)
  if (lessonParam) openIndex.value = findById(lessonParam)?.si ?? 0
}

/* ====== UI sections ====== */
type UiLesson = { id: string|number; title: string; durationMinutes?: number; type: ApiLesson['type']; done?: boolean }
type UiSection = { id: string|number; title: string; items: UiLesson[] }
const uiSections = ref<UiSection[]>([])

function buildUiSections() {
  if (!course.value) { uiSections.value = []; return }
  uiSections.value = (course.value.sections || []).map(s => ({
    id: s.id,
    title: s.title,
    items: (s.lessons || [])
      .filter(l => showNonVideoInOutline ? true : l.type === 'video')
      .map(l => ({
        id: l.id,
        title: l.title,
        durationMinutes: l.durationMinutes,
        type: l.type,
        done: doneSet.has(String(l.id))
      }))
  }))
}

/** Rebuild nhưng vẫn giữ nguyên con trỏ theo id cũ (nếu còn). */
function rebuildAndKeepCursor(preferredId: any) {
  const oldId = preferredId ?? currentLesson.value?.id ?? null
  buildUiSections()
  if (!uiSections.value.length) { cur.value = { si: 0, li: 0 }; return }

  // nếu còn id cũ thì trỏ lại, không thì snap về 0
  const found = oldId != null ? findById(oldId) : null
  cur.value = found ?? { si: 0, li: 0 }
}

/* ====== DERIVED (dựa theo chỉ số phẳng) ====== */
const flat = computed<UiLesson[]>(() => uiSections.value.flatMap(s => s.items))
const totalCount = computed(() => flat.value.length)
const doneCount = computed(() => flat.value.filter(l => l.done).length)
const progressPct = computed(() => Math.round((doneCount.value / Math.max(1, totalCount.value)) * 100))
const dash = computed(() => (progressPct.value/100)*100)

const currentLesson = computed<UiLesson | null>(() => {
  const sec = uiSections.value[cur.value.si]; if (!sec) return null
  return sec.items[cur.value.li] || null
})

/** Trả về index trong mảng phẳng ứng với cur; an toàn khi rebuild */
const currentFlatIndex = computed<number>(() => {
  const id = currentLesson.value?.id
  if (id == null) return -1
  return flat.value.findIndex(l => String(l.id) === String(id))
})

const prevLesson = computed<UiLesson | null>(() => {
  const idx = currentFlatIndex.value
  return idx > 0 ? flat.value[idx - 1] : null
})

const nextLesson = computed<UiLesson | null>(() => {
  const idx = currentFlatIndex.value
  return (idx >= 0 && idx < flat.value.length - 1) ? flat.value[idx + 1] : null
})

/* Demo src: thay bằng URL thật của bạn */
const currentSrc = computed(() =>
  'https://pub-52a4bc53687a4601ac29f7d454bef601.r2.dev/test2.mp4'
)

/* ====== METHODS ====== */
function formatDuration(min?: number){
  if (!min || min <= 0) return '—'
  const total = Math.round(min * 60)
  const mm = Math.floor(total / 60).toString().padStart(2,'0')
  const ss = (total % 60).toString().padStart(2,'0')
  return `${mm}:${ss}`
}

function goBack(){ window.history.length > 1 ? window.history.back() : router.push('/student/courses') }

function goToLesson(si: number, li: number){
  cur.value = { si, li }
  openIndex.value = si
  const id = uiSections.value[si]?.items[li]?.id
  if (id != null) router.replace({ params: { ...route.params, lessonId: String(id) } })
  videoRef.value?.play?.()
}

function goPrev(){
  if (!prevLesson.value) return
  const found = findById(prevLesson.value.id)
  if (found) goToLesson(found.si, found.li)
}

function goNext(){
  if (!nextLesson.value) return
  const found = findById(nextLesson.value.id)
  if (found) goToLesson(found.si, found.li)
}

function toggle(i: number){ openIndex.value = openIndex.value===i ? -1 : i }

function findById(id: any){
  if (id == null) return null
  for (let si=0; si<uiSections.value.length; si++){
    const li = uiSections.value[si].items.findIndex(x => String(x.id) === String(id))
    if (li >= 0) return { si, li }
  }
  return null
}

function markDone(id?: string|number|null){
  if (id == null) return
  doneSet.add(String(id))
  // rebuild nhưng vẫn giữ bài hiện tại => không bị -1 làm mất nút "tiếp theo"
  rebuildAndKeepCursor(id)
}

/* Nếu dữ liệu/sections đổi bất chợt (reset), vẫn đảm bảo con trỏ hợp lệ */
watchEffect(() => {
  if (!uiSections.value.length) return
  const id = currentLesson.value?.id
  const found = id != null ? findById(id) : null
  if (!found) {
    // snap về 0 an toàn
    cur.value = { si: 0, li: 0 }
  }
})

/* ====== MOUNT ====== */
onMounted(load)
</script>

<style scoped>
:root{
  --page-bg:#0b1220;
  --panel:#ffffff;
  --text:#0f172a;
  --muted:#6b7280;
  --line:#e5e7eb;
  --accent:#16a34a;
}

.lesson-player{ background:var(--page-bg); min-height:100vh; }
.container{ max-width:1440px; margin:0 auto; padding:14px; }

.topbar{ display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.link{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:8px 12px; font-weight:700; cursor:pointer; }
.spacer{ flex:1; }

.content{ display:grid; grid-template-columns:minmax(0,1fr) 380px; gap:14px; }

/* LEFT */
.left{ background:#000; border-radius:12px; overflow:hidden; border:6px solid #000; }
.video-shell{ background:#000; position:relative; }
.video{ width:100%; aspect-ratio:16/9; display:block; background:#000; }

.video-title{
  display:flex; justify-content:space-between; align-items:flex-end;
  gap:12px; padding:12px 14px; background:#0b1220; color:#e5e7eb;
  border-top:1px solid rgba(255,255,255,.08);
}
.video-title h2{ font-size:18px; font-weight:800; margin:0; }
.video-title .subtitle{ opacity:.85; font-size:14px; margin:0; }

/* RIGHT */
.right{ position:relative; }
.panel{
  position:sticky; top:10px;
  background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow:hidden;
  box-shadow:0 8px 24px rgba(0,0,0,.08);
}

/* Progress head */
.progress-head{ display:flex; gap:12px; padding:12px; border-bottom:1px solid var(--line); align-items:center; }
.circle{ position:relative; width:56px; height:56px; }
.c{ transform:rotate(-90deg); }
.bg{ fill:none; stroke:#e5e7eb; stroke-width:4; opacity:.9 }
.fg{ fill:none; stroke:var(--accent); stroke-width:4; stroke-linecap:round; stroke-dasharray:0 100; transition:stroke-dasharray .4s ease; }

/* >>> SỬA MÀU CHỮ Ở ĐÂY <<< */
.pct{ position:absolute; inset:0; display:grid; place-items:center; font-weight:800; font-size:12px; color:var(--text); }
.meta h4{ margin:0; font-size:16px; font-weight:800; color:var(--text); }
.meta .sub{ color:var(--muted); font-size:13px; }
/* <<< HẾT PHẦN SỬA >>> */

/* Outline */
.outline{ max-height:calc(100vh - 200px); overflow:auto; padding:8px; }
.sec{ border-radius:10px; overflow:hidden; margin-bottom:8px; border:1px solid var(--line); background:#fff; }
.sec-head{
  width:100%; text-align:left; display:flex; align-items:center; gap:8px;
  padding:10px 12px; background:#fff; border:0; cursor:pointer;
}
.sec-head .name{ font-weight:800; flex:1; }
.sec-head .len{
  font-size:12px; font-weight:800; color:#475569;
  background:#f1f5f9; border:1px solid #e2e8f0; border-radius:999px; padding:2px 8px;
}
.chev{ width:18px; height:18px; fill:#475569 }
.chev.open{ transform:rotate(180deg) }

.row{
  display:flex; justify-content:space-between; align-items:center; gap:8px;
  padding:10px 12px; border-top:1px solid var(--line); cursor:pointer; background:#fff;
}
.row:hover{ background:#f8fafc; }
.row.active{ background:#e8f2ff; }
.row.done .title{ color:#16a34a; }
.leftcell{ display:flex; align-items:center; gap:10px; min-width:0 }
.idx{
  width:22px; height:22px; display:grid; place-items:center;
  border:1px solid #e5e7eb; border-radius:6px; font-size:12px; font-weight:800; color:#64748b;
  background:#f8fafc;
}
.title{ font-weight:700; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.rightcell{ display:flex; align-items:center; gap:10px; }
.time{ color:#64748b; font-size:12px; }
.state svg{ width:18px; height:18px; stroke:#16a34a; stroke-width:2; fill:none }

/* Accordion anim */
.acc-enter-from, .acc-leave-to{ max-height:0; opacity:.2 }
.acc-enter-to, .acc-leave-from{ max-height:500px; opacity:1 }
.acc-enter-active, .acc-leave-active{ transition:all .18s ease-in-out }

/* ==== BUTTONS: đen/trắng, KHÔNG đổi màu khi reset/disabled ==== */
.btn{
  padding:12px 20px;
  border-radius:12px;
  font-weight:800;
  border:1.5px solid #e5e7eb;
  background:#fff;
  color:#0f172a;
  transition:all .15s ease;
  cursor:pointer;
  box-shadow:0 1px 0 rgba(0,0,0,.05);
}
.btn:hover:not(:disabled){
  background:#f8fafc;
  border-color:#cbd5e1;
  transform:translateY(-1px);
}
.btn:disabled{
  opacity:.55;
  cursor:not-allowed;
  background:#fff !important;
  color:#0f172a !important;
  border-color:#e5e7eb !important;
  transform:none;
  box-shadow:none;
}
.btn.bw{ /* alias rõ ràng cho style này */
  background:#fff;
  color:#0f172a;
  border-color:#e5e7eb;
}

/* BOTTOM NAV container */
.bottom-nav{
  display:flex; justify-content:space-between; align-items:center;
  gap:10px; padding:12px; background:#0b1220; border-top:1px solid rgba(255,255,255,.08);
}
.actions{ display:flex; align-items:center; gap:8px; }

/* Responsive */
@media (max-width: 1200px){
  .content{ grid-template-columns:1fr 340px; }
}
@media (max-width: 980px){
  .content{ grid-template-columns:1fr; }
  .right{ order:2 }
  .left{ order:1 }
  .panel{ position:static }
  .outline{ max-height:none }
}
</style>
