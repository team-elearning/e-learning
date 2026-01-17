<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter, onBeforeRouteLeave } from 'vue-router'
import { studentCoursesApi } from '../../api/student-courses.api'
import type { Course, BlockDetail, CourseModule } from '../../types/course.types'
import { ElMessage } from 'element-plus'
import StudentQuizPlayer from '../../components/StudentQuizPlayer.vue'
import {
  ArrowLeft,
  Menu,
  ChevronRight,
  ChevronDown,
  FileText,
  Video,
  HelpCircle,
  AlignLeft,
} from 'lucide-vue-next'

const route = useRoute()
const router = useRouter()
const courseId = route.params.id as string

const course = ref<Course | null>(null)
const activeBlock = ref<BlockDetail | null>(null)
const isLoadingCourse = ref(false)
const isLoadingBlock = ref(false)
const expandedModules = ref<Set<string>>(new Set())
const videoUrl = ref<string>('')

// Tracking state
let heartbeatInterval: any = null
let lastHeartbeatTime = 0

// Helper to get icon component
const getIcon = (type: string) => {
  switch (type) {
    case 'video':
      return Video
    case 'quiz':
      return HelpCircle
    case 'pdf':
    case 'docx':
      return FileText
    default:
      return AlignLeft
  }
}

async function fetchCourseFromApi() {
  isLoadingCourse.value = true
  try {
    const res = await studentCoursesApi.getCourseDetail(courseId)
    const data = res.data
    course.value = data

    const firstModuleId = data.modules?.[0]?.id
    if (firstModuleId) {
      expandedModules.value.add(firstModuleId)
    }
  } catch (error) {
    ElMessage.error('Không thể tải thông tin khóa học')
  } finally {
    isLoadingCourse.value = false
  }
}

async function handleBlockClick(blockId: string) {
  // Stop tracking previous block before switching
  await stopHeartbeat()

  // Revoke previous blob URL if it exists
  if (videoUrl.value && videoUrl.value.startsWith('blob:')) {
    URL.revokeObjectURL(videoUrl.value)
  }
  videoUrl.value = ''

  isLoadingBlock.value = true
  try {
    const res = await studentCoursesApi.getBlockDetail(blockId)
    activeBlock.value = res.data

    if (activeBlock.value?.type === 'video') {
      const vidSource = activeBlock.value.payload.url || activeBlock.value.payload.video_url
      if (vidSource) videoUrl.value = vidSource
      console.log('Video URL:', videoUrl.value)
    }

    // Start tracking new block
    await initBlockTracking(blockId)
  } catch (error) {
    ElMessage.error('Không thể tải nội dung bài học')
  } finally {
    isLoadingBlock.value = false
  }
}

// --- Tracking Logic ---

async function initBlockTracking(blockId: string) {
  try {
    const res = await studentCoursesApi.getBlockHeartbeat(blockId)
    const instance = res.data.instance

    // UI Resume Logic
    if (instance && instance.interaction_data) {
      // Example: Scroll resume
      if (instance.interaction_data.scroll_position) {
        // Use setTimeout to wait for DOM render
        setTimeout(() => {
          const mainContent = document.querySelector('main > div:last-child')
          if (mainContent) {
            mainContent.scrollTop = instance.interaction_data.scroll_position
          }
        }, 500)
      }
      // Note: Video resume would go here if we had a player ref
    }

    startHeartbeat(blockId)
  } catch (error) {
    console.error('Tracking init failed', error)
  }
}

function startHeartbeat(blockId: string) {
  if (heartbeatInterval) clearInterval(heartbeatInterval)

  lastHeartbeatTime = Date.now()
  heartbeatInterval = setInterval(() => {
    sendHeartbeat(blockId)
  }, 30000) // 30 seconds
}

async function stopHeartbeat() {
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval)
    heartbeatInterval = null
  }
  // Send final update if we have an active block
  if (activeBlock.value) {
    await sendHeartbeat(activeBlock.value.id)
  }
}

async function sendHeartbeat(blockId: string) {
  const now = Date.now()
  const diffSeconds = Math.floor((now - lastHeartbeatTime) / 1000)

  if (diffSeconds <= 0) return

  // Cap time spent at 300s to avoid huge spikes
  const timeToAdd = Math.min(diffSeconds, 300)

  // Reset timer
  lastHeartbeatTime = now

  const mainContent = document.querySelector('main > div:last-child')
  const interactionData: any = {
    scroll_position: mainContent ? mainContent.scrollTop : 0,
  }

  try {
    const payload = {
      time_spent_add: timeToAdd,
      interaction_data: interactionData,
    }
    const res = await studentCoursesApi.sendBlockHeartbeat(blockId, payload)

    // Check completion status from backend
    if (res.data.is_completed) {
      // Refresh course progress or mark block as done in UI
      // TODO: Emit event or update local block status
      updateCourseProgress()
    }
  } catch (error) {
    // Silent fail
  }
}

async function updateCourseProgress() {
  try {
    const res = await studentCoursesApi.getCourseProgress(courseId)
    // Update course level progress if displayed
    // For now just log or we can patch 'course' ref if it matches structure
    console.log('Course Progress:', res.data)
  } catch (e) {
    // ignore
  }
}

async function resumeLearning() {
  isLoadingBlock.value = true
  try {
    const res = await studentCoursesApi.getCourseResume(courseId)
    if (res.data.block_id) {
      await handleBlockClick(res.data.block_id)
    } else {
      ElMessage.info('Bạn chưa bắt đầu khóa học này hoặc đã hoàn thành.')
    }
  } catch (error) {
    ElMessage.error('Không thể lấy thông tin học tiếp')
  } finally {
    isLoadingBlock.value = false
  }
}

// Lifecycle hooks for tracking cancellation
onBeforeUnmount(() => {
  stopHeartbeat()
})

onBeforeRouteLeave(async (to, from, next) => {
  await stopHeartbeat()
  next()
})

function toggleModule(moduleId: string) {
  if (expandedModules.value.has(moduleId)) {
    expandedModules.value.delete(moduleId)
  } else {
    expandedModules.value.add(moduleId)
  }
}

function goBack() {
  router.push('/student/courses')
}

onMounted(() => {
  fetchCourseFromApi()
  // Establish media session for accessing protected content (videos, files)
  studentCoursesApi.getMediaCookies().catch(() => {
    console.warn('Failed to establish media session')
  })
})
</script>

<template>
  <div class="flex h-screen bg-white">
    <!-- Sidebar: Course Content -->
    <aside class="w-80 border-r border-slate-200 flex flex-col bg-slate-50">
      <div class="h-16 flex items-center px-4 border-b border-white bg-white sticky top-0 z-10">
        <button
          @click="goBack"
          class="p-2 -ml-2 hover:bg-slate-100 rounded-full text-slate-500 mr-2"
        >
          <ArrowLeft class="w-5 h-5" />
        </button>
        <h2 class="font-bold text-gray-900 truncate flex-1" :title="course?.title">
          {{ course?.title || 'Đang tải...' }}
        </h2>
      </div>

      <div class="flex-1 overflow-y-auto p-4 space-y-4">
        <div v-if="isLoadingCourse" class="space-y-4">
          <div v-for="i in 3" :key="i" class="h-12 bg-slate-200 rounded animate-pulse"></div>
        </div>

        <div v-else-if="course?.modules" class="space-y-2">
          <div
            v-for="(mod, moduleIndex) in course.modules"
            :key="mod.id"
            class="rounded-lg overflow-hidden border border-slate-200 bg-white"
          >
            <!-- Module Header -->
            <button
              @click="toggleModule(mod.id)"
              class="w-full flex items-center justify-between p-3 bg-slate-50 hover:bg-slate-100 transition-colors text-left"
            >
              <span class="font-semibold text-sm text-gray-800">
                Chương {{ moduleIndex + 1 }}: {{ mod.title }}
              </span>
              <component
                :is="expandedModules.has(mod.id) ? ChevronDown : ChevronRight"
                class="w-4 h-4 text-slate-500"
              />
            </button>

            <!-- Lessons List -->
            <div v-show="expandedModules.has(mod.id)" class="bg-white">
              <div
                v-for="(lesson, lessonIndex) in mod.lessons"
                :key="lesson.id"
                class="border-t border-slate-100"
              >
                <div
                  class="px-4 py-2 bg-slate-50/50 text-xs font-semibold text-slate-500 uppercase tracking-wider"
                >
                  Bài {{ lessonIndex + 1 }}: {{ lesson.title }}
                </div>
                <div>
                  <button
                    v-for="(block, blockIndex) in lesson.content_blocks"
                    :key="block.id"
                    @click="handleBlockClick(block.id)"
                    :class="[
                      'w-full flex items-center gap-3 px-4 py-3 text-sm transition-colors border-l-4',
                      activeBlock?.id === block.id
                        ? 'border-[rgb(var(--primary))] bg-indigo-50 text-[rgb(var(--primary))] font-medium'
                        : 'border-transparent text-slate-600 hover:bg-slate-50 hover:text-gray-900',
                    ]"
                  >
                    <component :is="getIcon(block.type)" class="w-4 h-4 flex-shrink-0" />
                    <span class="truncate"> {{ blockIndex + 1 }}: {{ block.title }}</span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </aside>

    <!-- Main Content -->
    <main class="flex-1 flex flex-col h-full overflow-hidden relative">
      <div
        v-if="!activeBlock && !isLoadingCourse"
        class="flex-1 overflow-y-auto bg-white p-8 lg:px-12"
      >
        <div class="max-w-3xl mx-auto pt-10">
          <div class="w-16 h-16 bg-indigo-50 rounded-2xl flex items-center justify-center mb-6">
            <span class="text-3xl">👋</span>
          </div>

          <h1 class="text-3xl font-bold text-gray-900 mb-4">{{ course?.title }}</h1>

          <div class="prose prose-lg text-slate-600 mb-8">
            <p v-if="course?.description">{{ course.description }}</p>
            <p v-else class="italic text-slate-400">Giảng viên chưa thêm mô tả cho khóa học này.</p>
          </div>

          <div class="bg-indigo-50/50 border border-indigo-100 rounded-xl p-6">
            <div class="flex items-center gap-3 text-indigo-900 font-medium mb-2">
              <Menu class="w-5 h-5" />
              Hướng dẫn học tập
            </div>
            <p class="text-indigo-700/80 text-sm mb-4">
              Hãy chọn một bài học từ danh sách bên trái để bắt đầu. Bạn có thể theo dõi tiến độ học
              tập của mình thông qua các bài kiểm tra và bài thực hành.
            </p>
            <button
              @click="resumeLearning"
              class="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition shadow-sm flex items-center gap-2"
            >
              Học tiếp <ChevronRight class="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      <div
        v-if="isLoadingBlock"
        class="absolute inset-0 flex items-center justify-center bg-white/80 z-20"
      >
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-600"></div>
      </div>

      <div v-if="activeBlock" class="flex-1 overflow-y-auto bg-white p-8 lg:px-12">
        <div class="max-w-4xl mx-auto">
          <div class="mb-6 pb-6 border-b border-slate-100">
            <div
              class="flex items-center gap-2 text-slate-500 mb-2 text-sm uppercase font-semibold tracking-wide"
            >
              <component :is="getIcon(activeBlock.type)" class="w-4 h-4" />
              {{
                activeBlock.type === 'rich_text'
                  ? 'Bài đọc'
                  : activeBlock.type === 'video'
                    ? 'Video'
                    : activeBlock.type === 'quiz'
                      ? 'Bài kiểm tra'
                      : 'Tài liệu'
              }}
            </div>
            <h1 class="text-3xl font-bold text-gray-900">{{ activeBlock.title }}</h1>
          </div>

          <!-- Content Renderer -->
          <div class="prose prose-slate max-w-none">
            <!-- Rich Text -->
            <div
              v-if="activeBlock.type === 'rich_text'"
              v-html="activeBlock.payload.html_content"
            ></div>

            <!-- Video -->
            <div
              v-else-if="activeBlock.type === 'video'"
              class="aspect-video bg-black rounded-xl overflow-hidden shadow-lg"
            >
              <video
                v-if="videoUrl"
                :src="videoUrl"
                class="w-full h-full"
                controls
                playsinline
                preload="metadata"
                controlsList="nodownload"
              ></video>
              <!-- <video
                v-if="videoUrl"
                :src="videoUrl"
                class="w-full h-full"
                controls
                playsinline
                preload="metadata"
                controlsList="nodownload"
                crossorigin="use-credentials"
              ></video> -->
              <!-- <iframe
                v-if="activeBlock.payload.video_url"
                :src="activeBlock.payload.video_url"
                class="w-full h-full"
                frameborder="0"
                allow="
                  accelerometer;
                  autoplay;
                  clipboard-write;
                  encrypted-media;
                  gyroscope;
                  picture-in-picture;
                "
                allowfullscreen
              ></iframe> -->
              <div v-else class="w-full h-full flex items-center justify-center text-white/50">
                Video chưa sẵn sàng
              </div>
            </div>

            <!-- Quiz Player -->
            <div v-else-if="activeBlock.type === 'quiz'" class="h-[calc(100vh-200px)] -mx-8 -my-6">
              <StudentQuizPlayer
                v-if="activeBlock.payload.quiz_id"
                :quiz-id="activeBlock.payload.quiz_id"
                :title="activeBlock.title"
                @finish="handleBlockClick(activeBlock.id)"
              />
              <div v-else class="text-center p-10 text-slate-500">
                Bài kiểm tra chưa được cấu hình.
              </div>
            </div>

            <!-- File/PDF/Docx -->
            <div
              v-else-if="['pdf', 'docx'].includes(activeBlock.type)"
              class="bg-slate-50 border border-slate-200 rounded-xl p-6 flex flex-col items-center justify-center text-center"
            >
              <FileText class="w-12 h-12 text-slate-400 mb-4" />
              <h3 class="text-lg font-bold text-gray-900 mb-2">Tài liệu đính kèm</h3>
              <p class="text-slate-500 mb-6">Tải về hoặc xem trực tiếp tài liệu này.</p>
              <a
                v-if="activeBlock.payload.file_url"
                :href="activeBlock.payload.file_url"
                target="_blank"
                class="text-blue-600 hover:underline font-medium"
              >
                Mở tài liệu
              </a>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>
