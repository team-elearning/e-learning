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
        <!-- LEFT: VIDEO & CONTENT -->
        <div class="left">
          <div v-if="!activeBlock" class="empty-state">
            <!-- <p>👈 Chọn một nội dung để bắt đầu học</p> -->
          </div>

          <!-- VIDEO -->
          <video
            v-else-if="activeBlock.type === 'video'"
            class="video"
            controls
            :src="blockCache.get(String(activeBlock.id))?.payload?.video_url"
          />

          <!-- QUIZ -->
          <div v-else-if="activeBlock.type === 'quiz'" class="quiz-shell">
            <h2>{{ activeBlock.title }}</h2>
            <button class="btn" @click="startQuiz(activeBlock)">Bắt đầu làm bài</button>
          </div>

          <!-- FILE -->
          <!-- <div v-else class="file-shell">
            <h2>{{ activeBlock.title }}</h2>
            <a
              :href="blockCache.get(String(activeBlock.id))?.payload?.file_url"
              target="_blank"
              class="btn"
            >
              Tải tài liệu
            </a>
          </div> -->

          <!-- <div v-else-if="activeBlock.type === 'pdf'" class="doc-viewer">
            <iframe
              :src="blockCache.get(String(activeBlock.id))?.payload?.file_url"
              frameborder="0"
            />
          </div> -->
          <!-- <div v-else-if="activeBlock.type === 'docx'" class="file-shell">
            <div class="file-card">
              <div class="file-icon">📄</div>

              <h2 class="file-title">
                {{ activeBlock.title || 'Tài liệu Word' }}
              </h2>

              <p class="file-desc">Tải về để xem trên máy tính hoặc điện thoại</p>

              <button class="btn" @click="downloadFile(activeBlock)">
                ⬇️ Tải file Word (.docx)
              </button>
            </div>
          </div> -->
          <!-- <div v-else-if="activeBlock.type === 'docx'" class="doc-viewer">
            <iframe
              :src="officeViewerUrl(activeBlock)"
              frameborder="0"
              width="100%"
              height="100%"
            />
            <div class="download-btn-wrapper">
              <button class="btn" @click="downloadFile(activeBlock)">
                ⬇️ Tải file Word (.docx)
              </button>
            </div>
          </div> -->

          <div
            v-else-if="activeBlock.type === 'pdf' || activeBlock.type === 'docx'"
            class="doc-viewer"
          >
            <iframe
              :src="googleViewerUrl(activeBlock)"
              frameborder="0"
              width="100%"
              height="100%"
            />
            <!-- <div class="download-btn-wrapper">
              <button class="btn" @click="downloadFile(activeBlock)">
                ⬇️ Tải file {{ activeBlock.type.toUpperCase() }}
              </button>
            </div> -->
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
                    :style="{ strokeDasharray: dash + ', 100' }"
                    d="M18 2a16 16 0 1 1 0 32a16 16 0 1 1 0-32"
                  />
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
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import api from '@/config/axios'

/* ======================
   ROUTER
====================== */
const router = useRouter()
const route = useRoute()

/* ======================
   REFS (template cần)
====================== */
const videoRef = ref<HTMLVideoElement | null>(null)
const outlineRef = ref<HTMLElement | null>(null)

/* ======================
   STATE
====================== */
const course = ref<any>(null)
const courseLoading = ref(true)
const courseError = ref('')

const openIndex = ref<number>(0)
const cur = ref<{ si: number; li: number }>({ si: 0, li: 0 })
// const activeTab = ref<'video' | 'materials'>('video')
const activeBlock = ref<any | null>(null)

const doneSet = reactive(new Set<string>())

/* Block detail cache */
const blockCache = reactive(new Map<string, any>())
const blockLoading = ref(false)
const blockError = ref('')
const docSrc = computed(() => {
  const url = blockCache.get(String(activeBlock.id))?.payload?.file_url
  if (activeBlock.type === 'pdf') return url
  return `https://docs.google.com/gview?url=${encodeURIComponent(url)}&embedded=true`
})
const docxViewerOk = ref(true)

// function officeViewerUrl(block: any) {
//   return `https://view.officeapps.live.com/op/view.aspx?src=${encodeURIComponent(
//     block.payload.file_url,
//   )}`
// }

// function officeViewerUrl(block: any) {
//   const directUrl = block?.payload?.file_url
//   if (!directUrl) return ''
//   // Encode để tránh lỗi ký tự đặc biệt trong signed URL
//   return `https://view.officeapps.live.com/op/embed.aspx?src=${encodeURIComponent(directUrl)}`
// }
function googleViewerUrl(block: any) {
  const directUrl = blockCache.get(String(block.id))?.payload?.file_url
  if (!directUrl) return ''

  // Encode kỹ để tránh lỗi ký tự
  const encodedUrl = encodeURIComponent(directUrl)
  return `https://docs.google.com/gview?url=${encodedUrl}&embedded=true`
}
function downloadFile(block: any) {
  const url = block?.payload?.file_url
  if (!url) return
  window.open(url, '_blank', 'noopener')
}

/* ======================
   API HELPERS (fallback endpoint)
====================== */
async function getCourseStructure(courseId: string) {
  return api.get(`/content/courses/${courseId}/`)
}

async function getBlockDetail(blockId: any) {
  const key = String(blockId)
  if (blockCache.has(key)) return blockCache.get(key)

  // ưu tiên contract: /blocks/{id}/
  try {
    const { data } = await api.get(`/content/blocks/${blockId}/`)

    blockCache.set(key, data)
    return data
  } catch (e) {
    // fallback: /blocks/detail/{id}/
    const { data } = await api.get(`/content/blocks/${blockId}/`)

    blockCache.set(key, data)
    return data
  }
}

/* ======================
   BUILD UI SECTIONS (modules -> lessons)
====================== */
type UiLesson = {
  id: string | number
  title: string
  durationMinutes?: number
  contentBlocks: any[]
  done?: boolean
}
type UiSection = { id: string | number; title: string; items: UiLesson[] }
const uiSections = ref<UiSection[]>([])

function buildUiSectionsFromCourse() {
  const mods = course.value?.modules || course.value?.sections || []
  uiSections.value = (mods || []).map((m: any, mi: number) => ({
    id: m.id ?? `m-${mi}`,
    title: m.title ?? `Chương ${mi + 1}`,
    items: (m.lessons || []).map((l: any) => ({
      id: l.id,
      title: l.title,
      durationMinutes: l.durationMinutes,
      done: doneSet.has(String(l.id)),
      hasVideo: (l.content_blocks || []).some((b: any) => b.type === 'video'),
      hasQuiz: (l.content_blocks || []).some((b: any) => b.type === 'quiz'),
      contentBlocks: l.content_blocks || [],
    })),
  }))
}

/* ======================
   DERIVED
====================== */
const flat = computed<UiLesson[]>(() => uiSections.value.flatMap((s) => s.items))
const totalCount = computed(() => flat.value.length)
const doneCount = computed(() => flat.value.filter((l) => l.done).length)
const progressPct = computed(() =>
  Math.round((doneCount.value / Math.max(1, totalCount.value)) * 100),
)
const dash = computed(() => progressPct.value)

async function selectBlock(block: any) {
  activeBlock.value = block
  await getBlockDetail(block.id)
}

/* ======================
   UTILS (template cần)
====================== */
function formatDuration(min?: number) {
  if (!min || min <= 0) return '—'
  return `${min}m`
}

function findById(id: any) {
  for (let si = 0; si < uiSections.value.length; si++) {
    const li = uiSections.value[si].items.findIndex((x: any) => String(x.id) === String(id))
    if (li >= 0) return { si, li }
  }
  return null
}

/* ======================
   NAV / UI ACTIONS
====================== */
function goBack() {
  window.history.length > 1 ? window.history.back() : router.push('/student/courses')
}

function toggle(i: number) {
  openIndex.value = openIndex.value === i ? -1 : i
}

function goToLesson(si: number, li: number) {
  cur.value = { si, li }
  openIndex.value = si

  const id = uiSections.value?.[si]?.items?.[li]?.id
  if (id != null) router.replace({ params: { ...route.params, lessonId: String(id) } })

  // tab mặc định sẽ được set trong watcher currentLesson
}

function markDone(id?: string | number | null) {
  if (!id) return
  doneSet.add(String(id))
  // cập nhật done flag trong uiSections
  buildUiSectionsFromCourse()
}

// function startQuiz(block: any) {
//   // TODO: sau này route quiz riêng
//   alert(`Quiz: ${block?.title || block?.id}`)
// }
function startQuiz(block: any) {
  if (!block?.id) {
    alert('Không tìm thấy bài kiểm tra')
    return
  }

  // course id đang học
  const courseId = course.value?.id || route.params.id

  router.push({
    name: 'student-quiz',
    query: {
      block_id: String(block.id), // dùng để gọi /content/blocks/{id}/ -> lấy quiz_id
      course_id: String(courseId), // context khóa học (RẤT NÊN)
    },
  })
}

/* ======================
   LAZY LOAD: blocks detail
====================== */

/* ======================
   LOAD COURSE
====================== */
async function loadCourse() {
  courseLoading.value = true
  courseError.value = ''
  try {
    const id = route.params.id
    const res = await getCourseStructure(id)
    course.value = res.data

    buildUiSectionsFromCourse()

    // nhảy theo lessonId nếu có
    const lessonId = route.params.lessonId
    if (lessonId) {
      const found = findById(lessonId)
      if (found) {
        cur.value = found
        openIndex.value = found.si
      } else {
        cur.value = { si: 0, li: 0 }
        openIndex.value = 0
      }
    } else {
      cur.value = { si: 0, li: 0 }
      openIndex.value = 0
    }

    // load video detail cho bài đầu
  } catch (e: any) {
    const status = e?.response?.status
    if (status === 403) {
      // chưa enrolled -> về trang giới thiệu khóa học
      router.replace(`/student/courses/${route.params.id}`)
      return
    }
    courseError.value = e?.message || 'Không thể tải khóa học.'
  } finally {
    courseLoading.value = false
  }
}

watch(
  () => activeBlock.value?.id,
  async (id) => {
    if (!id) return
    await getBlockDetail(id)
  },
)
/* ======================
   MOUNT
====================== */
onMounted(loadCourse)
</script>

<style scoped>
:root {
  --page-bg: #0b1220;
  --panel: #ffffff;
  --text: #0f172a;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #16a34a;
}

.lesson-player {
  background: var(--page-bg);
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
  stroke-dasharray: 0 100;
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
</style>
