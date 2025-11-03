<template>
  <div class="lesson-player" v-if="course">
    <div class="container">
      <div class="topbar">
        <button class="link" @click="goBack">Rời khỏi đây</button>
        <div class="spacer" />
      </div>

      <div class="content">
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
          <div class="bottom-nav">
            <button class="btn bw" :disabled="!prevLesson" @click="goPrev">‹ BÀI TRƯỚC</button>
            <div class="actions"></div>
            <button class="btn bw" :disabled="!nextLesson" @click="goNext">BÀI TIẾP THEO ›</button>
          </div>
        </div>

        <aside class="right">
          <div class="panel">
            <div class="progress-head">
              <div class="circle">
                <svg viewBox="0 0 36 36" class="c">
                  <path class="bg" d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                  <path class="fg" :style="{ strokeDasharray: dash + ', 100' }"
                        d="M18 2.0845 a 15.9155 15.9155 0 0 1 0 31.831 a 15.9155 15.9155 0 0 1 0 -31.831"/>
                </svg>
                <div class="pct">{{ progressPct }}%</div>
              </div>
              <div class="meta">
                <h4>Nội dung khóa học</h4>
                <div class="sub">{{ doneCount }}/{{ totalCount }} bài học</div>
              </div>
            </div>

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

// Giả lập service nếu bạn chưa có
const courseService = {
  detail: async (id: string) => {
    await new Promise(r => setTimeout(r, 500));
    return mockCourseData;
  }
};
type CourseDetail = typeof mockCourseData;
type Lesson = CourseDetail['sections'][0]['lessons'][0];
// ---

const router = useRouter()
const route = useRoute()

const course = ref<CourseDetail | null>(null)
const videoRef = ref<HTMLVideoElement|null>(null)
const doneSet = reactive(new Set<string>())
const openIndex = ref<number>(0)
const cur = ref<{ si: number; li: number }>({ si: 0, li: 0 })

async function load() {
  const id = route.params.id as any
  const lessonParam = route.params.lessonId as any
  const d = await courseService.detail(id)
  course.value = d
  rebuildAndKeepCursor(lessonParam ?? null)
  if (lessonParam) openIndex.value = findById(lessonParam)?.si ?? 0
}

type UiLesson = { id: string|number; title: string; durationMinutes?: number; type: Lesson['type']; done?: boolean }
type UiSection = { id: string|number; title: string; items: UiLesson[] }
const uiSections = ref<UiSection[]>([])

function buildUiSections() {
  if (!course.value) { uiSections.value = []; return }
  uiSections.value = (course.value.sections || []).map(s => ({
    id: s.id,
    title: s.title,
    items: (s.lessons || []).map(l => ({
      id: l.id,
      title: l.title,
      durationMinutes: l.durationMinutes,
      type: l.type,
      done: doneSet.has(String(l.id))
    }))
  }))
}

function rebuildAndKeepCursor(preferredId: any) {
  const oldId = preferredId ?? currentLesson.value?.id ?? null
  buildUiSections()
  if (!uiSections.value.length) { cur.value = { si: 0, li: 0 }; return }
  const found = oldId != null ? findById(oldId) : null
  cur.value = found ?? { si: 0, li: 0 }
}

const flat = computed<UiLesson[]>(() => uiSections.value.flatMap(s => s.items))
const totalCount = computed(() => flat.value.length)
// [NOTE] SỬA LỖI LOGIC: Tính trực tiếp từ `doneSet.size` để đảm bảo reactivity
const doneCount = computed(() => doneSet.size)
const progressPct = computed(() => Math.round((doneCount.value / Math.max(1, totalCount.value)) * 100))
const dash = computed(() => progressPct.value)

const currentLesson = computed<UiLesson | null>(() => uiSections.value[cur.value.si]?.items[cur.value.li] || null);

const currentFlatIndex = computed<number>(() => {
  const id = currentLesson.value?.id
  return id != null ? flat.value.findIndex(l => String(l.id) === String(id)) : -1;
})

const prevLesson = computed<UiLesson | null>(() => {
  const idx = currentFlatIndex.value
  return idx > 0 ? flat.value[idx - 1] : null
})

const nextLesson = computed<UiLesson | null>(() => {
  const idx = currentFlatIndex.value
  return (idx >= 0 && idx < flat.value.length - 1) ? flat.value[idx + 1] : null
})

const currentSrc = computed(() => 'https://pub-52a4bc53687a4601ac29f7d454bef601.r2.dev/test')

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

function toggle(i: number){ openIndex.value = openIndex.value === i ? -1 : i }

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
  if (!doneSet.has(String(id))) {
    doneSet.add(String(id));
    // Rebuild UI để cập nhật trạng thái 'done' cho các bài học
    rebuildAndKeepCursor(id);
  }
}

watchEffect(() => {
  if (!uiSections.value.length) return
  const id = currentLesson.value?.id
  const found = id != null ? findById(id) : null
  if (!found) {
    cur.value = { si: 0, li: 0 }
  }
})

onMounted(load)

// --- MOCK DATA ---
const mockCourseData = {
  id: "1",
  title: "Khóa học Vue.js Toàn Tập",
  sections: Array.from({ length: 5 }, (_, si) => ({
    id: `s${si + 1}`,
    title: `Chương ${si + 1}: Bắt đầu với Vue`,
    lessons: Array.from({ length: 4 }, (_, li) => ({
      id: `l${si * 4 + li + 1}`,
      title: `Bài học ${si * 4 + li + 1}`,
      durationMinutes: 5,
      type: 'video' as const,
    })),
  })),
};
</script>

<style scoped>
:root{
  --page-bg:#0b1220;
  --panel:#1e293b;
  --text:#f8fafc;
  --muted:#94a3b8;
  --line:#334155;
  --accent:#22c55e;
}

.lesson-player{ background:var(--page-bg); min-height:100vh; }
.container{ max-width:1440px; margin:0 auto; padding:14px; }

.topbar{ display:flex; align-items:center; gap:10px; margin-bottom:10px; }
.link{ 
  background:var(--panel); 
  border:1px solid var(--line); 
  color: var(--text) !important; /* Thêm !important */
  border-radius:10px; 
  padding:8px 12px; 
  font-weight:700; 
  cursor:pointer; 
}
.spacer{ flex:1; }

.content{ display:grid; grid-template-columns:minmax(0,1fr) 380px; gap:14px; }

/* LEFT */
.left{ background:#000; border-radius:12px; overflow:hidden; }
.video-shell{ background:#000; position:relative; }
.video{ width:100%; aspect-ratio:16/9; display:block; background:#000; }

.video-title{
  display:flex; justify-content:space-between; align-items:flex-end;
  gap:12px; padding:12px 14px; background:#0f172a; 
  border-top:1px solid var(--line);
}
.video-title h2{ 
  font-size:18px; 
  font-weight:800; 
  margin:0; 
  color:var(--text) !important; /* Thêm !important */
}
.video-title .subtitle{ 
  color: var(--muted) !important; /* Thêm !important */
  font-size:14px; 
  margin:0; 
}

/* RIGHT */
.right{ position:relative; }
.panel{
  position:sticky; top:14px;
  background:var(--panel); border:1px solid var(--line); border-radius:12px; overflow:hidden;
  box-shadow:0 8px 24px rgba(0,0,0,.2);
}

/* Progress head */
.progress-head{ 
  display:flex; 
  gap:16px; 
  padding:16px; 
  border-bottom:1px solid var(--line); 
  align-items: center;
}
.circle{ position:relative; width:56px; height:56px; flex-shrink: 0;}
.c{ transform:rotate(-90deg); }
.bg{ fill:none; stroke:var(--line); stroke-width:4; }
.fg{ fill:none; stroke:var(--accent); stroke-width:4; stroke-linecap:round; transition:stroke-dasharray .4s ease; }
.pct{ 
  position:absolute; 
  inset:0; 
  display:grid; 
  place-items:center; 
  font-weight:800; 
  font-size:14px; 
  color: var(--text) !important; /* Thêm !important */
}
.meta h4{ 
  margin:0; 
  font-size:16px; 
  font-weight:800; 
  color: var(--text) !important; /* Thêm !important */
}
.meta .sub{ 
  color:var(--muted) !important; /* Thêm !important */
  font-size:13px; 
  margin-top: 4px; 
}

/* Outline */
.outline{ max-height:calc(100vh - 220px); overflow:auto; padding:8px; }
.sec{ border-radius:8px; overflow:hidden; margin-bottom:8px; background:#27364b; }
.sec-head{
  width:100%; text-align:left; display:flex; align-items:center; gap:8px;
  padding:12px; background:transparent; border:0; cursor:pointer; 
  color: var(--text) !important; /* Thêm !important */
}
.sec-head .name{ 
  font-weight:700; 
  flex:1; 
  color: var(--text) !important; /* Thêm !important */
}
.sec-head .len{
  font-size:12px; 
  font-weight:700; 
  color:var(--muted) !important; /* Thêm !important */
  background:#334155; 
  border-radius:999px; 
  padding:2px 8px;
}
.chev{ 
  width:20px; 
  height:20px; 
  fill:var(--muted); 
  transition: transform 0.2s ease; 
}
.chev.open{ transform:rotate(180deg) }

.row{
  display:flex; justify-content:space-between; align-items:center; gap:8px;
  padding:12px; border-top:1px solid var(--line); cursor:pointer; background:transparent;
}
.row:hover{ background: #334155; }
.row.active{ background:var(--accent) !important; color: #fff !important; }
.row.active .title, 
.row.active .time, 
.row.active .idx { color: #fff !important; }
.row.done .title{ opacity: 0.7; }
.leftcell{ display:flex; align-items:center; gap:10px; min-width:0 }
.idx{
  width:22px; height:22px; display:grid; place-items:center;
  border-radius:6px; font-size:12px; font-weight:700; 
  color:var(--muted) !important; /* Thêm !important */
  background:#334155; flex-shrink: 0;
}
.title{ 
  font-weight:500; 
  white-space:nowrap; 
  overflow:hidden; 
  text-overflow:ellipsis; 
  color: var(--text) !important; /* Thêm !important */
}
.rightcell{ display:flex; align-items:center; gap:10px; }
.time{ 
  color:var(--muted) !important; /* Thêm !important */
  font-size:12px; 
}
.state svg{ 
  width:18px; 
  height:18px; 
  stroke:var(--accent); 
  stroke-width:2.5; 
  fill:none; 
}
.row.active .state svg { stroke: #fff !important; }

/* Accordion anim */
.acc-enter-from, .acc-leave-to{ max-height:0; opacity:.2 }
.acc-enter-to, .acc-leave-from{ max-height:500px; opacity:1 }
.acc-enter-active, .acc-leave-active{ transition:all .2s ease-in-out }

/* Buttons */
.btn{
  padding:12px 20px;
  border-radius:10px;
  font-weight:700;
  border:1.5px solid var(--line);
  background:var(--panel);
  color:var(--text) !important; /* Thêm !important */
  transition:all .15s ease;
  cursor:pointer;
}
.btn:hover:not(:disabled){
  background:#334155;
  border-color:#475569;
  transform:translateY(-1px);
}
.btn:disabled{
  opacity:.5;
  cursor:not-allowed;
  transform:none;
}
.bottom-nav{
  display:flex; justify-content:space-between; align-items:center;
  gap:10px; padding:12px; background:#0f172a; border-top:1px solid var(--line);
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
