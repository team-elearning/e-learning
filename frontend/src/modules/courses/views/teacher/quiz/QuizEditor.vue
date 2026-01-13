<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { instructorQuizApi } from '@/modules/courses/api/instructor-quiz.api'
import type { QuizSettings, QuizQuestion, QuestionType } from '@/modules/courses/types/quiz.types'
import { Settings, List, ArrowLeft, Trash2, Activity, CheckCircle2, AlertCircle } from 'lucide-vue-next'

import QuizSettingsForm from './components/QuizSettingsForm.vue'
import QuizQuestionList from './components/QuizQuestionList.vue'

const route = useRoute()
const router = useRouter()
const quizId = route.params.quizId as string
const courseId = route.params.courseId as string // dự phòng nếu cần dùng sau

const activeTab = ref<'questions' | 'settings'>('questions')
const isLoading = ref(false)
const isQuestionsLoading = ref(false)
const isSaving = ref(false)
const isCreating = ref(false)

const loadingState = computed(() => isLoading.value || isQuestionsLoading.value)

const quiz = ref<QuizSettings | null>(null)
const questions = ref<QuizQuestion[]>([])

async function fetchQuizDetail() {
  isLoading.value = true
  try {
    const res = await instructorQuizApi.getQuizDetail(quizId)
    quiz.value = res.data

    // Ưu tiên dữ liệu câu hỏi trả về kèm chi tiết; nếu không có thì gọi API riêng
    if (Array.isArray((res.data as any).questions) && (res.data as any).questions.length) {
      questions.value = (res.data as any).questions
    } else {
      await fetchQuestions()
    }
  } catch (error) {
    ElMessage.error('Không thể tải thông tin bài kiểm tra')
    console.error(error)
  } finally {
    isLoading.value = false
  }
}

async function fetchQuestions() {
  isQuestionsLoading.value = true
  try {
    const res = await instructorQuizApi.getQuestions(quizId)
    const payload = res.data as any
    const next =
      (Array.isArray(payload?.instance) && payload.instance) ||
      (Array.isArray(payload?.questions) && payload.questions) ||
      (Array.isArray(payload) && payload) ||
      []
    questions.value = next
  } catch (error) {
    console.error('Không thể tải danh sách câu hỏi', error)
    // Giữ nguyên danh sách cũ nếu lỗi để tránh bị trống
  } finally {
    isQuestionsLoading.value = false
  }
}

async function handleUpdateSettings(data: Partial<QuizSettings>) {
  isSaving.value = true
  try {
    const res = await instructorQuizApi.updateQuizSettings(quizId, data)
    quiz.value = Object.assign({}, quiz.value, res.data)
    ElMessage.success('Cập nhật cấu hình thành công')
  } catch (error) {
    ElMessage.error('Cập nhật thất bại')
  } finally {
    isSaving.value = false
  }
}

async function handleDeleteQuiz() {
  try {
    await ElMessageBox.confirm(
      'Bạn có chắc chắn muốn xóa bài kiểm tra này? Hành động này không thể hoàn tác.',
      'Cảnh báo xóa',
      {
        confirmButtonText: 'Xóa vĩnh viễn',
        cancelButtonText: 'Hủy',
        type: 'warning',
      },
    )

    await instructorQuizApi.deleteQuiz(quizId)
    ElMessage.success('Xóa bài kiểm tra thành công')
    router.back()
  } catch (error: any) {
    if (error !== 'cancel') {
      const msg = error.response?.data?.message || 'Không thể xóa bài kiểm tra'
      ElMessage.error(msg)
    }
  }
}

function goBack() {
  router.back()
}

// Xử lý câu hỏi
async function handleCreateQuestion(type: QuestionType) {
  if (isCreating.value) return
  isCreating.value = true
  try {
    const res = await instructorQuizApi.createQuestion(quizId, { type })
    const created = (res.data as any).instance || res.data

    // Thêm tạm để hiển thị ngay rồi gọi lại server để đảm bảo thứ tự/đủ dữ liệu
    if (created) {
      questions.value = [...questions.value, created]
    }
    await fetchQuestions()
    ElMessage.success('Đã thêm câu hỏi mới')
  } catch (e) {
    ElMessage.error('Không thể tạo câu hỏi')
  } finally {
    isCreating.value = false
  }
}

async function handleDeleteQuestion(questionId: string) {
  try {
    await ElMessageBox.confirm('Bạn có chắc muốn xóa câu hỏi này?', 'Xóa câu hỏi', {
      type: 'warning',
    })
    await instructorQuizApi.deleteQuestion(questionId)
    questions.value = questions.value.filter((q) => q.id !== questionId)
    ElMessage.success('Đã xóa câu hỏi')
  } catch (e) {
    // bỏ qua khi hủy
  }
}

async function handleQuestionUpdated(question: QuizQuestion) {
  const idx = questions.value.findIndex((q) => q.id === question.id)
  if (idx !== -1) {
    const next = [...questions.value]
    next[idx] = question
    questions.value = next
  } else {
    questions.value = [...questions.value, question]
  }
}

onMounted(() => {
  fetchQuizDetail()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 flex flex-col">
    <!-- Header -->
    <header class="bg-white border-b border-slate-200 sticky top-0 z-20">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <div class="flex items-center gap-4">
            <button
              @click="goBack"
              class="p-2 hover:bg-slate-100 rounded-full text-slate-500 transition-colors"
            >
              <ArrowLeft class="w-5 h-5" />
            </button>
            <div>
              <h1 class="text-lg font-bold text-slate-900 flex items-center gap-2">
                <Activity class="w-5 h-5 text-indigo-600" />
                {{ quiz?.title || 'Đang tải...' }}
              </h1>
              <p class="text-xs text-slate-500" v-if="!isLoading">
                {{ questions.length }} câu hỏi ·
                {{ quiz?.time_limit ? quiz.time_limit + ' phút' : 'Không giới hạn' }}
              </p>
            </div>
          </div>

          <div class="flex items-center gap-3">
            <button
              v-if="activeTab === 'settings'"
              @click="handleDeleteQuiz"
              class="px-4 py-2 text-red-600 bg-red-50 hover:bg-red-100 rounded-lg text-sm font-semibold transition-colors flex items-center gap-2"
            >
              <Trash2 class="w-4 h-4" /> Xóa đề thi
            </button>
            <div class="h-6 w-px bg-slate-200 mx-2"></div>
            <span
              v-if="quiz?.is_published"
              class="px-3 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium flex items-center gap-1"
            >
              <CheckCircle2 class="w-3 h-3" /> Đã xuất bản
            </span>
            <span
              v-else
              class="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-medium flex items-center gap-1"
            >
              <AlertCircle class="w-3 h-3" /> Bản nháp
            </span>
          </div>
        </div>

        <!-- Tabs -->
        <div class="flex items-center gap-8 -mb-px">
          <button
            @click="activeTab = 'questions'"
            :class="[
              'pb-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2',
              activeTab === 'questions'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700',
            ]"
          >
            <List class="w-4 h-4" /> Danh sách câu hỏi
          </button>
          <button
            @click="activeTab = 'settings'"
            :class="[
              'pb-4 text-sm font-medium border-b-2 transition-colors flex items-center gap-2',
              activeTab === 'settings'
                ? 'border-indigo-600 text-indigo-600'
                : 'border-transparent text-slate-500 hover:text-slate-700',
            ]"
          >
            <Settings class="w-4 h-4" /> Cấu hình
          </button>
        </div>
      </div>
    </header>

    <!-- Content -->
    <main class="flex-1 max-w-7xl mx-auto w-full px-4 sm:px-6 lg:px-8 py-8">
      <div v-loading="loadingState" class="min-h-[400px]">
        <div v-if="activeTab === 'questions'" class="space-y-6">
          <QuizQuestionList
            :questions="questions"
            :loading="isQuestionsLoading"
            @create="handleCreateQuestion"
            @delete="handleDeleteQuestion"
            @update="handleQuestionUpdated"
          />
        </div>

        <div v-else-if="activeTab === 'settings'" class="max-w-3xl mx-auto">
          <QuizSettingsForm
            v-if="quiz"
            :initial-data="quiz"
            :is-saving="isSaving"
            @submit="handleUpdateSettings"
          />
        </div>
      </div>
    </main>
  </div>
</template>
