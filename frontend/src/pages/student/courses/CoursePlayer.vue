<!-- src/pages/student/learn/coursePlayer.vue -->
<template>
  <div class="lesson-player" v-if="course">
    <div class="container">
      <!-- TOP BAR -->
      <div class="topbar">
        <button class="link" @click="goBack">Rời khỏi đây</button>
        <div class="spacer" />
      </div>

      <div class="content">
        <!-- LEFT: VIDEO & CONTENT -->
        <div class="left">
          <div v-if="!activeBlock" class="empty-state">
            <!-- <p>👈 Chọn một nội dung để bắt đầu học</p> -->
          </div>

          <!-- RICH TEXT -->
          <div v-else-if="activeBlock.type === 'rich_text'" class="rich-text-viewer">
            <div class="rich-text-card" ref="richTextRef">
              <h2 class="title">{{ activeBlock.title }}</h2>

              <div
                class="content"
                v-html="blockCache.get(String(activeBlock.id))?.payload?.html_content"
              />
            </div>
          </div>

          <!-- VIDEO -->
          <video
            v-else-if="activeBlock.type === 'video'"
            ref="videoRef"
            class="video"
            controls
            :src="blockCache.get(String(activeBlock.id))?.payload?.video_url"
          />

          <!-- QUIZ -->
          <div v-else-if="activeBlock.type === 'quiz'" class="quiz-shell">
            <h2>{{ activeBlock.title }}</h2>
            <button class="btn" @click="startQuiz(activeBlock)">Bắt đầu làm bài</button>
          </div>
          <!-- PDF / DOCX -->
          <div v-else-if="activeBlock.type === 'pdf'" class="doc-viewer">
            <iframe
              class="pdf-frame"
              :src="blockCache.get(String(activeBlock.id))?.payload?.file_url"
              frameborder="0"
              width="100%"
              height="100%"
            />
          </div>
          <div v-else-if="activeBlock.type === 'docx'" class="docx-viewer">
            <div class="docx-card">
              <div class="icon">📄</div>
              <h3>{{ activeBlock.title }}</h3>
              <p>Tài liệu Word (.docx)</p>

              <button class="btn" @click="downloadAndMark(activeBlock)">
                ⬇️ Tải & đánh dấu đã đọc
              </button>
            </div>
          </div>
        </div>

        <!-- RIGHT: OUTLINE -->
        <aside class="right">
          <div class="panel">
            <!-- Progress header -->
            <div class="progress-head">
              <div class="circle">
                <svg viewBox="0 0 36 36" class="c">
                  <path class="bg" d="M18 2a16 16 0 1 1 0 32a16 16 0 1 1 0-32" />
                  <path
                    class="fg"
                    pathLength="100"
                    :style="{ strokeDasharray: `${progressPct} 100` }"
                    d="M18 2a16 16 0 1 1 0 32a16 16 0 1 1 0-32"
                  />
                </svg>
                <div class="pct">{{ progressPct }}%</div>
              </div>
              <div class="meta">
                <h4>Nội dung khóa học</h4>
                <!-- <div class="sub">{{ doneCount }}/{{ totalCount }} bài học</div> -->
              </div>
            </div>

            <!-- Outline -->
            <div class="outline" ref="outlineRef">
              <div v-for="(sec, si) in uiSections" :key="sec.id" class="sec">
                <button class="sec-head" @click="toggle(si)">
                  <span class="name">{{ si + 1 }}. {{ sec.title }}</span>
                  <span class="len">{{ sec.items.length }}</span>
                  <svg class="chev" viewBox="0 0 24 24" :class="{ open: openIndex === si }">
                    <path d="M6 9l6 6 6-6" />
                  </svg>
                </button>

                <transition name="acc">
                  <ul v-show="openIndex === si">
                    <li v-for="(it, li) in sec.items" :key="it.id" class="lesson-wrap">
                      <!-- LESSON -->
                      <div class="row lesson-row">
                        <div class="leftcell">
                          <!-- <span class="idx">{{ li + 1 }}</span>   -->
                          <div class="lesson-title" :data-index="li + 1">
                            {{ it.title }}
                          </div>
                        </div>
                      </div>

                      <!-- 👉 TẦNG 3 -->
                      <ul class="blocks">
                        <li
                          v-for="block in it.contentBlocks"
                          :key="block.id"
                          class="block-row"
                          :class="{ active: activeBlock?.id === block.id }"
                          @click="selectBlock(block)"
                        >
                          <span class="icon">
                            <span v-if="block.type === 'video'">📹</span>
                            <span v-else-if="block.type === 'quiz'">📝</span>
                            <span v-else>📄</span>
                          </span>
                          <span class="title">{{ block.title }}</span>
                        </li>
                      </ul>
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
import { ref, computed, reactive, onMounted, watch, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import api from '@/config/axios'

/* ================= ROUTER ================= */
const router = useRouter()
const route = useRoute()

/* ================= STATE ================= */
const course = ref<any>(null)
const loading = ref(true)
const error = ref('')

const activeBlock = ref<any | null>(null)
const openIndex = ref(0)

/* progress */
const doneSet = reactive(new Set<string>())

/* block cache */
const blockCache = reactive(new Map<string, any>())

/* refs */
const videoRef = ref<HTMLVideoElement | null>(null)

/* heartbeat */
let heartbeatTimer: number | null = null
let lastTickAt = Date.now()

const progressPct = computed(() => {
  return Math.round(courseProgress.value?.percent_completed || 0)
})
const totalCount = computed(() => {
  let count = 0
  for (const sec of uiSections.value) {
    count += sec.items.length
  }
  return count
})
const doneCount = computed(() => doneSet.size)
// const progressPct = computed(() => {
//   return Math.round(courseProgress.value?.percent_completed || 0)
// })
async function refreshCourseProgress() {
  const res = await getCourseProgress(course.value.id)
  console.log('🔥 course progress API:', res)
  courseProgress.value = res
}

/* ================= API ================= */
async function getCourse(courseId: string) {
  const { data } = await api.get(`/content/courses/${courseId}/`)
  return data
}

async function getBlockDetail(blockId: string) {
  if (blockCache.has(blockId)) return blockCache.get(blockId)
  const { data } = await api.get(`/content/blocks/${blockId}/`)
  blockCache.set(blockId, data)
  return data
}

async function getBlockResume(blockId: string) {
  const { data } = await api.get(`/progress/tracking/heartbeat/blocks/${blockId}/`)
  return data?.instance || null
}

async function postHeartbeat(blockId: string, payload: any) {
  return api.post(`/progress/tracking/heartbeat/blocks/${blockId}/`, payload)
}

// async function getCourseProgress(courseId: string) {
//   const { data } = await api.get(`/progress/courses/${courseId}/progress/`)
//   return data.instance
// }
async function getCourseProgress(courseId: string) {
  const { data } = await api.get(`/progress/courses/${courseId}/progress/`)
  return data // ❌ KHÔNG phải data.instance
}

/* ================= UI BUILD ================= */
type UiSection = {
  id: string
  title: string
  items: any[]
}

const uiSections = ref<UiSection[]>([])

function buildUiSections() {
  const modules = course.value?.modules || course.value?.sections || []
  uiSections.value = modules.map((m: any, mi: number) => ({
    id: m.id ?? `m-${mi}`,
    title: m.title ?? `Chương ${mi + 1}`,
    items: (m.lessons || []).map((l: any) => ({
      id: l.id,
      title: l.title,
      contentBlocks: l.content_blocks || [],
      done: doneSet.has(String(l.id)),
    })),
  }))
}

/* ================= SELECT BLOCK ================= */
async function selectBlock(block: any) {
  stopHeartbeat()
  activeBlock.value = block

  const [blockDetail, resume] = await Promise.all([
    getBlockDetail(String(block.id)),
    getBlockResume(String(block.id)),
  ])

  // gán detail vào block
  if (block.type === 'rich_text') {
    startRichTextHeartbeat(block)
  }

  /* ===== VIDEO ===== */
  if (block.type === 'video') {
    const ts = resume?.interaction_data?.video_timestamp ?? 0
    requestAnimationFrame(() => {
      if (videoRef.value) {
        videoRef.value.currentTime = ts
        videoRef.value.play()
        startVideoHeartbeat(block)
      }
    })
  }

  /* ===== PDF / DOCX ===== */
  if (block.type === 'pdf' || block.type === 'docx') {
    block.__resume_page = resume?.interaction_data?.page ?? 1
  }

  /* ===== QUIZ ===== */
  if (block.type === 'quiz') {
    block.__resume_question = resume?.interaction_data?.current_question_index ?? 0
  }

  if (resume?.is_completed) {
    markLessonCompleted(block)
  }
}

/* ================= HEARTBEAT ================= */
function startVideoHeartbeat(block: any) {
  stopHeartbeat()
  lastTickAt = Date.now()

  heartbeatTimer = window.setInterval(async () => {
    if (!videoRef.value) return

    const now = Date.now()
    const delta = Math.floor((now - lastTickAt) / 1000)
    lastTickAt = now

    if (delta <= 0) return

    const res = await postHeartbeat(block.id, {
      time_spent_add: Math.min(delta, 30),
      interaction_data: {
        video_timestamp: videoRef.value.currentTime,
        playback_rate: videoRef.value.playbackRate,
      },
    })

    if (res.data?.is_completed) {
      markLessonCompleted(block)
      await refreshCourseProgress()
    }
  }, 30000)
}

function stopHeartbeat() {
  if (heartbeatTimer) {
    clearInterval(heartbeatTimer)
    heartbeatTimer = null
  }
}

/* ================= MARK DONE ================= */
async function markLessonCompleted(block: any) {
  if (!block?.lesson_id) return
  doneSet.add(String(block.lesson_id))
  buildUiSections()
}

/* ================= COURSE PROGRESS ================= */
const courseProgress = ref<any>(null)

// async function refreshCourseProgress() {
//   courseProgress.value = await getCourseProgress(course.value.id)
// }

/* ================= NAV ================= */
function toggle(i: number) {
  openIndex.value = openIndex.value === i ? -1 : i
}

function goBack() {
  router.back()
}

function startQuiz(block: any) {
  router.push({
    name: 'student-quiz',
    query: {
      block_id: String(block.id),
      course_id: String(course.value.id),
    },
  })
}

/* ================= LOAD COURSE ================= */
async function loadCourse() {
  loading.value = true
  try {
    const courseId = String(route.params.id)
    course.value = await getCourse(courseId)
    buildUiSections()
    await refreshCourseProgress()

    /* resume block */
    const resumeRes = await api.get(`/progress/courses/${courseId}/resume/`)
    const resumeBlockId = resumeRes.data?.instance?.block_id

    if (resumeBlockId) {
      const found = findBlockById(resumeBlockId)
      if (found) selectBlock(found)
    }
  } catch (e: any) {
    error.value = e?.message || 'Không thể tải khóa học'
  } finally {
    loading.value = false
  }
}

function findBlockById(blockId: string) {
  for (const sec of uiSections.value) {
    for (const lesson of sec.items) {
      const block = lesson.contentBlocks.find((b: any) => String(b.id) === String(blockId))
      if (block) return block
    }
  }
  return null
}

/* ================= CLEANUP ================= */
onBeforeUnmount(() => {
  stopHeartbeat()
  if (videoRef.value) {
    navigator.sendBeacon(
      `/progress/tracking/heartbeat/blocks/${activeBlock.value?.id}`,
      JSON.stringify({
        time_spent_add: 0,
        interaction_data: {
          video_timestamp: videoRef.value.currentTime,
          playback_rate: videoRef.value.playbackRate,
        },
      }),
    )
  }
})

/* ================= MOUNT ================= */
onMounted(loadCourse)
function onVideoPause(block: any) {
  if (!videoRef.value) return

  postHeartbeat(block.id, {
    time_spent_add: 0,
    interaction_data: {
      video_timestamp: videoRef.value.currentTime,
      playback_rate: videoRef.value.playbackRate,
    },
  })
}
function onVideoSeek(block: any) {
  if (!videoRef.value) return
  postHeartbeat(block.id, {
    time_spent_add: 0,
    interaction_data: {
      video_timestamp: videoRef.value.currentTime,
    },
  })
}
async function downloadAndMark(block: any) {
  const url = blockCache.get(String(block.id))?.payload?.file_url
  if (!url) return

  window.open(url, '_blank', 'noopener')

  // gửi heartbeat đánh dấu hoàn thành
  await api.post(`/progress/tracking/heartbeat/blocks/${block.id}/`, {
    time_spent_add: 60,
    interaction_data: {
      read_complete: true,
    },
  })

  markLessonCompleted(block)
}
function startPdfHeartbeat(block: any) {
  stopHeartbeat()

  heartbeatTimer = window.setInterval(() => {
    postHeartbeat(block.id, {
      time_spent_add: 30,
      interaction_data: {
        scroll_position: getPdfScrollPercent(),
      },
    })
  }, 30000)
}

function getPdfScrollPercent() {
  const iframe = document.querySelector('.pdf-frame') as HTMLIFrameElement
  if (!iframe?.contentWindow) return 0

  const doc = iframe.contentWindow.document
  const scrollTop = doc.documentElement.scrollTop || doc.body.scrollTop
  const scrollHeight = doc.documentElement.scrollHeight || doc.body.scrollHeight
  const clientHeight = doc.documentElement.clientHeight

  return Math.min(100, Math.round((scrollTop / (scrollHeight - clientHeight)) * 100))
}
const richTextRef = ref<HTMLElement | null>(null)

function startRichTextHeartbeat(block: any) {
  stopHeartbeat()

  heartbeatTimer = window.setInterval(() => {
    if (!richTextRef.value) return

    const el = richTextRef.value
    const scrollTop = el.scrollTop
    const scrollHeight = el.scrollHeight - el.clientHeight

    const percent = scrollHeight > 0 ? Math.round((scrollTop / scrollHeight) * 100) : 0

    postHeartbeat(block.id, {
      time_spent_add: 30,
      interaction_data: {
        scroll_position: percent,
      },
    })
  }, 30000)
}
</script>

<style scoped>
.lesson-player {
  --page-bg: #0b1220;
  --panel: #ffffff;
  --text: #0f172a;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #16a34a;
}
:root {
  --page-bg: #0b1220;
  --panel: #ffffff;
  --text: #0f172a;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #16a34a;
}

.lesson-player {
  /* background: var(--page-bg); */
  min-height: 100vh;
}
.container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 14px;
}

.topbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.link {
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 8px 12px;
  font-weight: 700;
  cursor: pointer;
}
.spacer {
  flex: 1;
}

.content {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 380px;
  gap: 14px;
}

/* LEFT */
.left {
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  border: 6px solid #000;
}

/* TABS */
.tabs {
  display: flex;
  gap: 0;
  background: #0b1220;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}
.tab {
  flex: 1;
  padding: 12px 16px;
  background: transparent;
  border: 0;
  color: #94a3b8;
  font-weight: 700;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 2px solid transparent;
}
.tab:hover {
  background: rgba(255, 255, 255, 0.05);
  color: #e2e8f0;
}
.tab.active {
  color: #fff;
  border-bottom-color: #16a34a;
  background: rgba(22, 163, 74, 0.1);
}

/* TAB CONTENT */
.tab-content {
  background: #000;
}

/* VIDEO */
.video-shell {
  background: #000;
  position: relative;
}
.video {
  width: 100%;
  aspect-ratio: 16/9;
  display: block;
  background: #000;
}
.video-empty {
  width: 100%;
  aspect-ratio: 16/9;
  background: linear-gradient(135deg, #0f172a, #111827);
  color: #e5e7eb;
  display: grid;
  place-items: center;
  padding: 18px;
  text-align: center;
  font-weight: 700;
  border: 1px dashed rgba(255, 255, 255, 0.2);
}

.video-title {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
  padding: 12px 14px;
  background: #0b1220;
  color: #e5e7eb;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.video-title h2 {
  font-size: 18px;
  font-weight: 800;
  margin: 0;
}
.video-title .subtitle {
  opacity: 0.85;
  font-size: 14px;
  margin: 0;
}

/* MATERIALS */
.materials-shell {
  background: #fff;
  min-height: 500px;
  max-height: calc(100vh - 200px);
  overflow-y: auto;
}
.materials-header {
  padding: 16px 20px;
  background: #f8fafc;
  border-bottom: 2px solid #e2e8f0;
}
.materials-header h2 {
  font-size: 20px;
  font-weight: 800;
  margin: 0 0 4px 0;
  color: var(--text);
}
.materials-header .subtitle {
  font-size: 13px;
  color: var(--muted);
  margin: 0;
}

/* CONTENT BLOCKS */
.content-blocks {
  padding: 20px;
}
.content-block {
  margin-bottom: 24px;
  padding: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
}

.block-text p {
  line-height: 1.7;
  color: var(--text);
  margin: 0;
  white-space: pre-wrap;
}

.block-image img {
  width: 100%;
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  display: block;
}

.block-video video {
  width: 100%;
  border-radius: 8px;
  background: #000;
}

.block-file {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fff;
  border: 1px solid #cbd5e1;
  border-radius: 10px;
}
.file-icon {
  font-size: 32px;
}
.file-info {
  flex: 1;
}
.file-name {
  font-weight: 700;
  color: var(--text);
  margin: 0 0 4px 0;
}
.file-link {
  display: inline-block;
  padding: 6px 12px;
  background: #16a34a;
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  border-radius: 8px;
  text-decoration: none;
}
.file-link:hover {
  background: #15803d;
}

.block-quiz {
  padding: 16px;
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
  border: 2px solid #0ea5e9;
  border-radius: 12px;
}
.quiz-header h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  color: #0c4a6e;
}
.quiz-header p {
  margin: 0 0 12px 0;
  color: #475569;
  font-size: 14px;
}
.btn-quiz {
  padding: 10px 20px;
  background: #0ea5e9;
  color: #fff;
  border: 0;
  border-radius: 10px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.2s;
}
.btn-quiz:hover {
  background: #0284c7;
  transform: translateY(-1px);
}

.block-unknown {
  padding: 12px;
  text-align: center;
  color: var(--muted);
}

.empty-state {
  padding: 40px;
  text-align: center;
  color: var(--muted);
  font-size: 14px;
}

/* RIGHT */
.right {
  position: relative;
}
.panel {
  position: sticky;
  top: 10px;
  background: var(--panel);
  border: 1px solid var(--line);
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

/* Progress head */
.progress-head {
  display: flex;
  gap: 12px;
  padding: 12px;
  border-bottom: 1px solid var(--line);
  align-items: center;
}
.circle {
  position: relative;
  width: 56px;
  height: 56px;
}
.c {
  transform: rotate(-90deg);
}
.bg {
  fill: none;
  stroke: #e5e7eb;
  stroke-width: 4;
  opacity: 0.9;
}
.fg {
  fill: none;
  stroke: var(--accent);
  stroke-width: 4;
  stroke-linecap: round;
  transition: stroke-dasharray 0.4s ease;
}

/* >>> SỬA MÀU CHỮ Ở ĐÂY <<< */
.pct {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-weight: 800;
  font-size: 12px;
  color: var(--text);
}
.meta h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 800;
  color: var(--text);
}
.meta .sub {
  color: var(--muted);
  font-size: 13px;
}
/* <<< HẾT PHẦN SỬA >>> */

/* Outline */
.outline {
  max-height: calc(100vh - 200px);
  overflow: auto;
  padding: 8px;
}
.sec {
  border-radius: 10px;
  overflow: hidden;
  margin-bottom: 8px;
  border: 1px solid var(--line);
  background: #fff;
}
.sec-head {
  width: 100%;
  text-align: left;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  background: #fff;
  border: 0;
  cursor: pointer;
}
.sec-head .name {
  font-weight: 800;
  flex: 1;
}
.sec-head .len {
  font-size: 12px;
  font-weight: 800;
  color: #475569;
  background: #f1f5f9;
  border: 1px solid #e2e8f0;
  border-radius: 999px;
  padding: 2px 8px;
}
.chev {
  width: 18px;
  height: 18px;
  fill: #475569;
}
.chev.open {
  transform: rotate(180deg);
}

.row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid var(--line);
  cursor: pointer;
  background: #fff;
}
.row:hover {
  background: #f8fafc;
}
.row.active {
  background: #e8f2ff;
}
.row.done .title {
  color: #16a34a;
}
.leftcell {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
}
.idx {
  width: 22px;
  height: 22px;
  display: grid;
  place-items: center;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 800;
  color: #64748b;
  background: #f8fafc;
}
.title {
  font-weight: 700;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.rightcell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.time {
  color: #64748b;
  font-size: 12px;
}
.state svg {
  width: 18px;
  height: 18px;
  stroke: #16a34a;
  stroke-width: 2;
  fill: none;
}

/* Accordion anim */
.acc-enter-from,
.acc-leave-to {
  max-height: 0;
  opacity: 0.2;
}
.acc-enter-to,
.acc-leave-from {
  max-height: 500px;
  opacity: 1;
}
.acc-enter-active,
.acc-leave-active {
  transition: all 0.18s ease-in-out;
}

/* ==== BUTTONS: đen/trắng, KHÔNG đổi màu khi reset/disabled ==== */
.btn {
  padding: 12px 20px;
  border-radius: 12px;
  font-weight: 800;
  border: 1.5px solid #e5e7eb;
  background: #fff;
  color: #0f172a;
  transition: all 0.15s ease;
  cursor: pointer;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.05);
}
.btn:hover:not(:disabled) {
  background: #f8fafc;
  border-color: #cbd5e1;
  transform: translateY(-1px);
}
.btn:disabled {
  opacity: 0.55;
  cursor: not-allowed;
  background: #fff !important;
  color: #0f172a !important;
  border-color: #e5e7eb !important;
  transform: none;
  box-shadow: none;
}
.btn.bw {
  /* alias rõ ràng cho style này */
  background: #fff;
  color: #0f172a;
  border-color: #e5e7eb;
}

/* BOTTOM NAV container */
.bottom-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 10px;
  padding: 12px;
  background: #0b1220;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}
.actions {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Responsive */
@media (max-width: 1200px) {
  .content {
    grid-template-columns: 1fr 340px;
  }
}
@media (max-width: 980px) {
  .content {
    grid-template-columns: 1fr;
  }
  .right {
    order: 2;
  }
  .left {
    order: 1;
  }
  .panel {
    position: static;
  }
  .outline {
    max-height: none;
  }
}
/* CỐ ĐỊNH LEFT */
.left {
  position: sticky;
  top: 12px;
  height: calc(80vh - 24px);
  overflow: auto;
}
.sec {
  margin-bottom: 10px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.sec-head {
  width: 100%;
  padding: 12px 14px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  font-weight: 800;
  background: #ffffff;
  cursor: pointer;
}

.sec-head .name {
  font-size: 15px;
}

.sec-head .len {
  font-size: 12px;
  font-weight: 700;
  background: #f1f5f9;
  border-radius: 999px;
  padding: 2px 8px;
}
.lesson-wrap {
  padding: 8px 0 4px 0;
}

.lesson-title {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px;
  font-weight: 700;
  font-size: 14px;
  color: #0f172a;
}

.lesson-title::before {
  content: attr(data-index);
  display: inline-grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 6px;
  background: #f1f5f9;
  font-size: 12px;
  font-weight: 800;
  color: #475569;
}
.blocks {
  margin-left: 36px;
  margin-top: 4px;
}

.block-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 6px 10px;
  margin: 4px 0;
  border-radius: 8px;
  font-size: 14px;
  color: #334155;
  cursor: pointer;
  transition:
    background 0.15s,
    color 0.15s;
}

.block-row:hover {
  background: #f1f5f9;
}

.block-row.active {
  background: #e0f2fe;
  color: #0369a1;
  font-weight: 700;
}

.block-row .icon {
  width: 18px;
  text-align: center;
}
.outline {
  max-height: calc(100vh - 160px);
  overflow-y: auto;
  padding: 10px;
}
.quiz-shell {
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 16px;
  text-align: center;
  color: #e5e7eb;
}
.doc-viewer {
  height: 100%;
}

.file-shell {
  height: calc(100vh - 120px);
  display: grid;
  place-items: center;
  background: #000;
}

.file-card {
  max-width: 420px;
  width: 100%;
  padding: 32px;
  border-radius: 16px;
  background: #0b1220;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-align: center;
  color: #e5e7eb;
}

.file-icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.file-title {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 8px;
}

.file-desc {
  font-size: 14px;
  color: #94a3b8;
  margin-bottom: 20px;
}
.doc-viewer {
  height: 100%;
}

.doc-viewer iframe {
  width: 100%;
  height: 100%;
  border: none;
}
.docx-viewer {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center; /* dọc */
  justify-content: center; /* ngang */
}

.docx-card {
  background: #fff;
  padding: 32px 40px;
  border-radius: 16px;
  text-align: center;
  max-width: 420px;
  width: 100%;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.12);
}

.docx-card .icon {
  font-size: 48px;
  margin-bottom: 12px;
}

.docx-card h3 {
  font-size: 18px;
  font-weight: 800;
  margin-bottom: 6px;
}

.docx-card p {
  color: #64748b;
  margin-bottom: 20px;
}

.docx-card .btn {
  padding: 12px 22px;
  border-radius: 999px;
  font-weight: 700;
}
.rich-text-viewer {
  display: flex;
  justify-content: center;
  padding: 32px;
  width: 100%;
}

.rich-text-card {
  width: 100%;
  max-width: 760px;
  background: #ffffff;
  border-radius: 14px;
  padding: 32px;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.08);
  line-height: 1.75;
  font-size: 16px;
  color: #0f172a;
}

.rich-text-card .title {
  font-size: 22px;
  font-weight: 800;
  margin-bottom: 16px;
}

.rich-text-card .content p {
  margin-bottom: 12px;
}

.rich-text-card .content ul {
  padding-left: 20px;
  margin-bottom: 12px;
}

.rich-text-card .content li {
  margin-bottom: 6px;
}
</style>
