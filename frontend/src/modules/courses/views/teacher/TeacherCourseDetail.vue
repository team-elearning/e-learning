<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { coursesApi } from '../../api/courses.api'
import type { Course, ContentBlock, BlockDetail, Quiz } from '../../types/course.types'
import { ElMessage } from 'element-plus'
import TeacherQuizPreview from './components/TeacherQuizPreview.vue'

const route = useRoute()
const router = useRouter()
const courseId = route.params.id as string

const course = ref<Course | null>(null)
const isLoading = ref(false)
const activeBlockId = ref<string | null>(null)
const blockDetail = ref<BlockDetail | null>(null)
const quizDetail = ref<Quiz | null>(null)
const isLoadingBlock = ref(false)

// Fetch Course Tree
async function fetchCourseDetail() {
  isLoading.value = true
  try {
    const res = await coursesApi.getCourseDetail(courseId)
    course.value = res.data

    // Auto select first block if available
    const firstModule = res.data.modules?.[0]
    const firstLesson = firstModule?.lessons?.[0]
    const firstBlock = firstLesson?.content_blocks?.[0]
    if (firstBlock) {
      selectBlock(firstBlock)
    }
  } catch (error) {
    ElMessage.error('Không thể tải thông tin khóa học')
  } finally {
    isLoading.value = false
  }
}

// Fetch Content Block Detail
async function selectBlock(block: ContentBlock) {
  if (activeBlockId.value === block.id) return

  activeBlockId.value = block.id
  isLoadingBlock.value = true
  blockDetail.value = null // clear prev
  quizDetail.value = null

  try {
    const res = await coursesApi.getBlockDetail(block.id)
    blockDetail.value = res.data

    if (res.data.type === 'quiz' && res.data.payload.quiz_id) {
      const quizRes = await coursesApi.getQuizDetail(res.data.payload.quiz_id)
      quizDetail.value = quizRes.data
    }
  } catch (error) {
    ElMessage.error('Không thể tải nội dung bài học')
  } finally {
    isLoadingBlock.value = false
  }
}

function getIcon(type: string) {
  switch (type) {
    case 'video':
      return '🎥'
    case 'quiz':
      return '❓'
    case 'rich_text':
      return '📄'
    case 'pdf':
      return '📕'
    case 'docx':
      return '📘'
    default:
      return '📄'
  }
}

function getTypeLabel(type: string) {
  switch (type) {
    case 'video':
      return 'Video'
    case 'quiz':
      return 'Bài kiểm tra'
    case 'rich_text':
      return 'Bài đọc'
    case 'pdf':
      return 'Tài liệu PDF'
    case 'docx':
      return 'Tài liệu Word'
    default:
      return 'Tài liệu'
  }
}

onMounted(() => {
  if (courseId) {
    fetchCourseDetail()
  }
})
</script>

<template>
  <div class="flex h-[calc(100vh-64px)] bg-white">
    <!-- Sidebar: Course Structure -->
    <div class="w-80 flex-shrink-0 border-r border-slate-200 flex flex-col bg-slate-50">
      <div class="p-4 border-b border-slate-200 bg-white">
        <button
          @click="router.push('/teacher/courses')"
          class="text-xs font-semibold text-slate-500 hover:text-[rgb(var(--primary))] mb-2 flex items-center gap-1"
        >
          ← Quay lại
        </button>
        <h2 class="font-bold text-gray-800 line-clamp-2" :title="course?.title">
          {{ course?.title || 'Đang tải...' }}
        </h2>
      </div>

      <div class="flex-1 overflow-auto custom-scrollbar p-2 space-y-2">
        <div v-if="isLoading" class="p-4 text-center text-slate-400 text-sm">
          Đang tải cấu trúc...
        </div>

        <div v-else-if="!course?.modules?.length" class="p-8 text-center text-slate-400 text-sm">
          Chưa có nội dung
        </div>

        <!-- Modules List -->
        <div v-for="(mod, mIdx) in course?.modules" :key="mod.id" class="mb-4">
          <div
            class="px-2 py-1.5 font-bold text-slate-700 text-sm bg-slate-100 rounded-lg mb-2 truncate"
          >
            Chương {{ mIdx + 1 }}: {{ mod.title }}
          </div>

          <!-- Lessons List -->
          <div
            v-for="(lesson, lIdx) in mod.lessons"
            :key="lesson.id"
            class="ml-2 pl-2 border-l-2 border-slate-200 mb-2"
          >
            <div class="text-xs font-semibold text-slate-500 mb-1 px-2">
              Bài {{ lIdx + 1 }}: {{ lesson.title }}
            </div>

            <!-- Blocks List -->
            <button
              v-for="(block, bIdx) in lesson.content_blocks"
              :key="block.id"
              @click="selectBlock(block)"
              class="w-full text-left px-3 py-2 rounded-lg text-sm flex items-center gap-2 transition-all"
              :class="
                activeBlockId === block.id
                  ? 'bg-[rgb(var(--primary))] text-white shadow-md'
                  : 'text-slate-600 hover:bg-slate-200'
              "
            >
              <span class="text-base" :class="activeBlockId === block.id ? '' : 'text-slate-400'">{{
                getIcon(block.type)
              }}</span>
              <span class="truncate"> {{ bIdx + 1 }}: {{ block.title }}</span>
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Main Content Area -->
    <div class="flex-1 overflow-auto bg-slate-100 p-6 lg:p-10 flex flex-col items-center">
      <div
        class="w-full max-w-4xl bg-white rounded-2xl shadow-sm border border-slate-200 min-h-[500px] flex flex-col"
      >
        <!-- Header -->
        <div class="p-6 border-b border-slate-100 flex justify-between items-start">
          <div>
            <div
              class="text-xs font-bold uppercase tracking-wider text-[rgb(var(--primary))] mb-1"
              v-if="blockDetail"
            >
              {{ getTypeLabel(blockDetail.type) }}
            </div>
            <h1 class="text-2xl font-bold text-gray-900" v-if="blockDetail">
              {{ blockDetail.title }}
            </h1>
            <div v-if="isLoadingBlock" class="h-8 w-64 bg-slate-200 rounded animate-pulse"></div>
          </div>
        </div>

        <!-- Content Body -->
        <div class="p-6 flex-1 relative">
          <div v-if="isLoadingBlock" class="space-y-4">
            <div class="h-4 bg-slate-200 rounded w-full animate-pulse"></div>
            <div class="h-4 bg-slate-200 rounded w-5/6 animate-pulse"></div>
            <div
              class="h-64 bg-slate-100 rounded w-full animate-pulse flex items-center justify-center text-slate-300 text-4xl"
            >
              🖼️
            </div>
          </div>

          <div v-else-if="blockDetail" class="w-full min-h-full">
            <!-- Video Player -->
            <div
              v-if="blockDetail.type === 'video' && blockDetail.payload.video_url"
              class="aspect-video bg-black rounded-xl overflow-hidden shadow-lg"
            >
              <video controls class="w-full h-full" :src="blockDetail.payload.video_url">
                Trình duyệt của bạn không hỗ trợ video.
              </video>
            </div>

            <!-- PDF/Docx Link (Preview Placeholder) -->
            <div
              v-else-if="['pdf', 'docx'].includes(blockDetail.type)"
              class="flex flex-col items-center justify-center h-full py-10 border-2 border-dashed border-slate-200 rounded-xl bg-slate-50"
            >
              <div class="text-6xl mb-4">{{ blockDetail.type === 'pdf' ? '📕' : '📘' }}</div>
              <h3 class="text-lg font-bold text-gray-800 mb-2">Tài liệu đính kèm</h3>
              <p class="text-slate-500 mb-6 text-center max-w-md">
                Bạn có thể xem trước hoặc tải xuống tài liệu này.
              </p>
              <a
                v-if="blockDetail.payload.file_url"
                :href="blockDetail.payload.file_url"
                target="_blank"
                class="px-6 py-2.5 bg-[rgb(var(--primary))] text-white rounded-lg font-semibold shadow hover:bg-blue-700 transition"
              >
                Tải xuống / Xem tài liệu
              </a>
              <div v-else class="text-red-500 text-sm">Đường dẫn file bị lỗi</div>
            </div>

            <!-- Rich Text -->
            <div v-else-if="blockDetail.type === 'rich_text'" class="prose max-w-none">
              <div
                v-if="blockDetail.payload.html_content || blockDetail.payload.content"
                v-html="blockDetail.payload.html_content || blockDetail.payload.content"
              ></div>
              <div v-else class="text-slate-400 italic">Nội dung văn bản trống</div>
            </div>

            <!-- Quiz Placeholder -->
            <div v-else-if="blockDetail.type === 'quiz'" class="w-full">
              <TeacherQuizPreview v-if="quizDetail" :quiz="quizDetail" />
              <div v-else class="flex flex-col items-center justify-center py-20">
                <div v-if="isLoadingBlock" class="animate-pulse flex flex-col items-center">
                  <div class="h-8 w-8 bg-slate-200 rounded-full mb-2"></div>
                  <div class="h-4 w-32 bg-slate-200 rounded"></div>
                </div>
                <div v-else class="text-center">
                  <div class="text-4xl mb-2">❓</div>
                  <p class="text-slate-500">Không tìm thấy thông tin bài kiểm tra</p>
                </div>
              </div>
            </div>

            <!-- Fallback -->
            <div v-else class="flex flex-col items-center justify-center h-full text-slate-400">
              <p>Không hỗ trợ định dạng này</p>
            </div>
          </div>

          <div v-else class="flex flex-col items-center justify-center h-full text-slate-400">
            <div class="text-4xl mb-4">👈</div>
            <p>Chọn một bài học từ danh sách bên trái để bắt đầu</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 6px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: transparent;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background-color: #cbd5e1;
  border-radius: 20px;
}
</style>
