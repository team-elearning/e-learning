<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { studentCoursesApi } from '../api/student-courses.api'
import type { QuizAttempt, StudentQuizQuestion, QuizAttemptResult } from '../types/course.types'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  CheckCircle,
  AlertCircle,
  Clock,
  ChevronRight,
  ChevronLeft,
  Save,
  Flag,
} from 'lucide-vue-next'

const props = defineProps<{
  quizId: string
  title: string
}>()

const emit = defineEmits(['finish'])

const attempt = ref<QuizAttempt | null>(null)
const currentQuestion = ref<StudentQuizQuestion | null>(null)
const isLoading = ref(false)
const isSaving = ref(false)
const currentQuestionIndex = ref(0)
const quizResult = ref<QuizAttemptResult | null>(null)

const questionOptions = computed(() => {
  if (!currentQuestion.value) return []
  // Ưu tiên shuffled_options nếu có (từ backend)
  if (currentQuestion.value.shuffled_options && currentQuestion.value.shuffled_options.length > 0) {
    return currentQuestion.value.shuffled_options
  }
  // Fallback to prompt.options (theo cấu trúc JSON mới)
  return currentQuestion.value.prompt?.options || []
})

// Draft Data
const currentAnswer = ref<any>(null)
let saveTimeout: any = null

watch(
  () => props.quizId,
  (newId) => {
    if (newId) {
      // Reset state
      attempt.value = null
      currentQuestion.value = null
      currentQuestionIndex.value = 0
      quizResult.value = null
      currentAnswer.value = null
      initQuiz()
    }
  },
)

const initQuiz = async () => {
  isLoading.value = true
  try {
    const res = await studentCoursesApi.startQuizAttempt(props.quizId)
    attempt.value = res.data
    // Load first question
    if (attempt.value.questions_order.length > 0) {
      currentQuestionIndex.value = 0
      const firstQ = attempt.value.questions_order[0]
      if (firstQ) await loadQuestion(firstQ)
    }
  } catch (error) {
    ElMessage.error('Không thể bắt đầu bài kiểm tra')
  } finally {
    isLoading.value = false
  }
}

const loadQuestion = async (questionId: string) => {
  isLoading.value = true
  // Reset answer
  currentAnswer.value = null
  try {
    if (!attempt.value) return
    const res = await studentCoursesApi.getQuizQuestion(attempt.value.attempt_id, questionId)
    currentQuestion.value = res.data

    // Resume answer state
    if (res.data.current_answer) {
      // Adapt format if needed, depending on type
      // For now assume API returns same structure as we send
      if (res.data.type === 'multiple_choice_single') {
        currentAnswer.value = res.data.current_answer.selected_id
      } else if (res.data.type === 'multiple_choice_multi') {
        currentAnswer.value = res.data.current_answer.selected_ids || []
      } else if (res.data.type === 'short_answer') {
        currentAnswer.value = res.data.current_answer.text
      } else if (res.data.type === 'true_false') {
        // TF might need conversion if API returns boolean but we use radio strings?
        // Assuming boolean is fine
        currentAnswer.value = res.data.current_answer.selected_value
      }
    } else {
      // Init empty
      if (res.data.type === 'multiple_choice_multi') {
        currentAnswer.value = []
      }
    }
  } catch (error) {
    ElMessage.error('Không thể tải câu hỏi')
  } finally {
    isLoading.value = false
  }
}

const handleAnswerChange = () => {
  // Debounce save
  if (saveTimeout) clearTimeout(saveTimeout)
  saveTimeout = setTimeout(() => {
    saveDraft()
  }, 1000)
}

const formatAnswerPayload = () => {
  if (!currentQuestion.value) return null
  const type = currentQuestion.value.type
  const val = currentAnswer.value

  if (val === null || val === undefined || val === '') return null

  if (type === 'multiple_choice_single') {
    return { selected_id: val }
  }
  if (type === 'multiple_choice_multi') {
    return { selected_ids: val }
  }
  if (type === 'true_false') {
    return { selected_value: val }
  }
  if (type === 'short_answer') {
    return { text: val }
  }
  return { answer: val }
}

const saveDraft = async () => {
  if (!attempt.value || !currentQuestion.value) return
  const payload = formatAnswerPayload()
  if (!payload) return

  isSaving.value = true
  try {
    await studentCoursesApi.saveQuestionDraft(attempt.value.attempt_id, currentQuestion.value.id, {
      question_type: currentQuestion.value.type,
      answer_data: payload,
    })
  } catch (error) {
    // Silent fail or toast?
    console.error('Autosave failed')
  } finally {
    isSaving.value = false
  }
}

const nextQuestion = async () => {
  // Ensure draft is saved
  await saveDraft()
  if (!attempt.value) return

  const nextIndex = currentQuestionIndex.value + 1
  if (nextIndex < attempt.value.questions_order.length) {
    currentQuestionIndex.value = nextIndex
    const questionId = attempt.value.questions_order[nextIndex]
    if (questionId) await loadQuestion(questionId)
  }
}

const prevQuestion = async () => {
  // Ensure draft is saved
  await saveDraft()
  if (!attempt.value) return

  const prevIndex = currentQuestionIndex.value - 1
  if (prevIndex >= 0) {
    currentQuestionIndex.value = prevIndex
    const questionId = attempt.value.questions_order[prevIndex]
    if (questionId) await loadQuestion(questionId)
  }
}

const jumpToQuestion = async (index: number) => {
  if (index === currentQuestionIndex.value) return
  await saveDraft()
  if (!attempt.value) return
  currentQuestionIndex.value = index
  const questionId = attempt.value.questions_order[index]
  if (questionId) await loadQuestion(questionId)
}

const handleSubmitQuiz = async () => {
  try {
    await ElMessageBox.confirm(
      'Bạn có chắc chắn muốn nộp bài? Bạn sẽ không thể sửa lại bài làm sau khi nộp.',
      'Xác nhận nộp bài',
      {
        confirmButtonText: 'Nộp bài',
        cancelButtonText: 'Kiểm tra lại',
        type: 'warning',
      },
    )

    // Save last answer
    await saveDraft()

    if (!attempt.value) return
    isLoading.value = true

    const res = await studentCoursesApi.finishQuizAttempt(attempt.value.attempt_id)
    quizResult.value = res.data
    // Show result
  } catch {
    // Cancelled
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  initQuiz()
})
</script>

<template>
  <div class="max-w-4xl mx-auto h-full flex flex-col">
    <!-- Result View -->
    <div
      v-if="quizResult"
      class="bg-white rounded-2xl shadow-sm border border-slate-200 p-8 flex-1 overflow-y-auto"
    >
      <div class="text-center mb-8">
        <div
          v-if="quizResult.is_passed"
          class="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6"
        >
          <CheckCircle class="w-10 h-10 text-green-600" />
        </div>
        <div
          v-else
          class="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6"
        >
          <AlertCircle class="w-10 h-10 text-red-600" />
        </div>

        <h2 class="text-3xl font-bold text-gray-900 mb-2">
          {{
            quizResult.is_passed
              ? 'Chúc mừng! Bạn đã đạt yêu cầu'
              : 'Tiếc quá! Bạn chưa đạt yêu cầu'
          }}
        </h2>
        <p class="text-slate-500 mb-6">
          Điểm số của bạn:
          <span class="text-2xl font-bold text-indigo-600"
            >{{ quizResult.score }} / {{ quizResult.max_score }}</span
          >
          <span class="ml-2 text-sm text-slate-400">({{ quizResult.percentage }}%)</span>
        </p>

        <div class="grid grid-cols-1 sm:grid-cols-2 gap-4 text-left max-w-2xl mx-auto mb-6">
          <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <span class="text-sm text-slate-500">Số câu đúng</span>
            <div class="text-xl font-bold text-green-600">
              {{ quizResult.items.filter((i) => i.is_correct).length }}
            </div>
          </div>
          <div class="bg-slate-50 p-4 rounded-xl border border-slate-200">
            <span class="text-sm text-slate-500">Số câu sai</span>
            <div class="text-xl font-bold text-red-600">
              {{ quizResult.items.filter((i) => !i.is_correct).length }}
            </div>
          </div>
        </div>

        <button
          @click="$emit('finish')"
          class="bg-slate-900 text-white px-6 py-3 rounded-xl font-semibold hover:bg-slate-800 transition shadow-lg shadow-slate-200"
        >
          Quay lại bài học
        </button>
      </div>

      <!-- Detailed Review List -->
      <div class="max-w-3xl mx-auto space-y-6">
        <h3 class="text-xl font-bold text-gray-800 border-b pb-4 mb-6">Chi tiết bài làm</h3>
        <div
          v-for="(item, idx) in quizResult.items"
          :key="item.question_id"
          class="border rounded-xl p-6 transition-colors"
          :class="
            item.is_correct ? 'border-green-200 bg-green-50/30' : 'border-red-200 bg-red-50/30'
          "
        >
          <!-- Question Header -->
          <div class="flex items-start gap-4 mb-4">
            <span
              class="flex-shrink-0 w-8 h-8 flex items-center justify-center rounded-full text-sm font-bold"
              :class="item.is_correct ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'"
            >
              {{ idx + 1 }}
            </span>
            <div class="flex-1">
              <h4 class="font-semibold text-gray-900 text-lg mb-2">{{ item.question_text }}</h4>

              <!-- Options Display (Read-only context) -->
              <div
                v-if="item.options && item.options.length > 0"
                class="mb-4 pl-4 border-l-2 border-slate-200 space-y-1"
              >
                <div v-for="opt in item.options" :key="opt.id" class="text-sm text-slate-600">
                  <span class="font-bold text-slate-800">{{ opt.id }}.</span> {{ opt.text }}
                </div>
              </div>

              <!-- Answer Assessment -->
              <div class="grid grid-cols-1 md:grid-cols-2 gap-4 bg-white/60 p-4 rounded-lg">
                <div>
                  <div class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                    Câu trả lời của bạn
                  </div>
                  <div
                    class="font-medium"
                    :class="item.is_correct ? 'text-green-700' : 'text-red-700'"
                  >
                    {{ item.user_answer_text || '(Chưa trả lời)' }}
                  </div>
                </div>
                <div v-if="!item.is_correct">
                  <div class="text-xs font-bold uppercase tracking-wider text-slate-500 mb-1">
                    Đáp án đúng
                  </div>
                  <div class="font-medium text-green-700">
                    {{ item.correct_answer_text }}
                  </div>
                </div>
              </div>

              <!-- Feedback -->
              <div v-if="item.feedback" class="mt-4 text-sm text-slate-600 italic">
                <span class="font-bold">Giải thích:</span> {{ item.feedback }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quiz Interface -->
    <div v-else-if="attempt" class="flex flex-col h-full bg-slate-50/50">
      <!-- Header -->
      <div
        class="bg-white border-b border-slate-200 px-6 py-4 flex items-center justify-between sticky top-0 z-20"
      >
        <div>
          <h2 class="font-bold text-gray-900 text-lg">{{ title }}</h2>
          <div class="flex items-center gap-2 text-sm text-slate-500">
            <Clock class="w-4 h-4" />
            <span>Thời gian còn lại: --:--</span>
          </div>
        </div>
        <button
          @click="handleSubmitQuiz"
          class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 transition"
        >
          Nộp bài
        </button>
      </div>

      <!-- Main Body -->
      <div class="flex-1 overflow-hidden flex flex-col md:flex-row">
        <!-- Question Content -->
        <div class="flex-1 overflow-y-auto p-6 md:p-8">
          <div v-if="isLoading" class="space-y-4 animate-pulse">
            <div class="h-6 bg-slate-200 rounded w-3/4"></div>
            <div class="h-32 bg-slate-200 rounded"></div>
            <div class="h-10 bg-slate-200 rounded"></div>
          </div>
          <div
            v-else-if="currentQuestion"
            class="bg-white rounded-2xl shadow-sm border border-slate-200 p-6 md:p-8 min-h-[400px]"
          >
            <div class="flex items-start justify-between mb-6">
              <span class="bg-indigo-50 text-indigo-700 font-bold px-3 py-1 rounded-md text-sm"
                >Câu {{ currentQuestionIndex + 1 }}</span
              >
              <div
                v-if="isSaving"
                class="flex items-center gap-1 text-xs text-green-600 font-medium"
              >
                <Save class="w-3 h-3 animate-bounce" /> Đang lưu...
              </div>
              <div v-else class="text-xs text-slate-400">Đã lưu</div>
            </div>

            <div class="prose prose-lg mb-8" v-html="currentQuestion.prompt.content"></div>

            <!-- Multiple Choice Single -->
            <div v-if="currentQuestion.type === 'multiple_choice_single'" class="space-y-3">
              <label
                v-for="opt in questionOptions"
                :key="opt.id"
                class="flex items-center p-4 border rounded-xl cursor-pointer hover:bg-indigo-50/50 transition-colors"
                :class="
                  currentAnswer === opt.id
                    ? 'border-2 border-indigo-500 bg-indigo-50'
                    : 'border-slate-200'
                "
              >
                <input
                  type="radio"
                  name="mc-single"
                  :value="opt.id"
                  v-model="currentAnswer"
                  @change="handleAnswerChange"
                  class="w-5 h-5 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                />
                <span class="ml-3 font-medium text-gray-700">{{ opt.text }}</span>
              </label>
            </div>

            <!-- Multiple Choice Multi -->
            <div v-else-if="currentQuestion.type === 'multiple_choice_multi'" class="space-y-3">
              <label
                v-for="opt in questionOptions"
                :key="opt.id"
                class="flex items-center p-4 border rounded-xl cursor-pointer hover:bg-indigo-50/50 transition-colors"
                :class="
                  currentAnswer?.includes(opt.id)
                    ? 'border-2 border-indigo-500 bg-indigo-50'
                    : 'border-slate-200'
                "
              >
                <input
                  type="checkbox"
                  :value="opt.id"
                  v-model="currentAnswer"
                  @change="handleAnswerChange"
                  class="rounded w-5 h-5 text-indigo-600 focus:ring-indigo-500 border-gray-300"
                />
                <span class="ml-3 font-medium text-gray-700">{{ opt.text }}</span>
              </label>
            </div>

            <!-- True/False -->
            <div v-else-if="currentQuestion.type === 'true_false'" class="flex gap-4">
              <label
                class="flex-1 flex flex-col items-center justify-center p-6 border-2 rounded-xl cursor-pointer hover:bg-indigo-50/50 transition-colors text-center"
                :class="
                  currentAnswer === true ? 'border-green-500 bg-green-50' : 'border-slate-200'
                "
              >
                <input
                  type="radio"
                  name="tf"
                  :value="true"
                  v-model="currentAnswer"
                  @change="handleAnswerChange"
                  class="sr-only"
                />
                <span
                  class="text-lg font-bold"
                  :class="currentAnswer === true ? 'text-green-700' : 'text-gray-600'"
                  >ĐÚNG</span
                >
              </label>
              <label
                class="flex-1 flex flex-col items-center justify-center p-6 border-2 rounded-xl cursor-pointer hover:bg-indigo-50/50 transition-colors text-center"
                :class="currentAnswer === false ? 'border-red-500 bg-red-50' : 'border-slate-200'"
              >
                <input
                  type="radio"
                  name="tf"
                  :value="false"
                  v-model="currentAnswer"
                  @change="handleAnswerChange"
                  class="sr-only"
                />
                <span
                  class="text-lg font-bold"
                  :class="currentAnswer === false ? 'text-red-700' : 'text-gray-600'"
                  >SAI</span
                >
              </label>
            </div>

            <!-- Short Answer -->
            <div v-else-if="currentQuestion.type === 'short_answer'" class="space-y-3">
              <textarea
                v-model="currentAnswer"
                @input="handleAnswerChange"
                rows="4"
                placeholder="Nhập câu trả lời của bạn..."
                class="w-full p-4 border border-slate-300 rounded-xl focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none font-medium"
              ></textarea>
            </div>
          </div>

          <!-- Footer Nav -->
          <div class="mt-8 flex items-center justify-between">
            <button
              @click="prevQuestion"
              :disabled="currentQuestionIndex === 0"
              class="px-4 py-2 text-slate-600 hover:text-indigo-600 font-medium disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              <ChevronLeft class="w-5 h-5" /> Câu trước
            </button>
            <button
              @click="nextQuestion"
              :disabled="!attempt || currentQuestionIndex === attempt.questions_order.length - 1"
              class="px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
            >
              Câu tiếp theo <ChevronRight class="w-5 h-5" />
            </button>
          </div>
        </div>

        <!-- Right Sidebar: Question Palette -->
        <div class="w-full md:w-72 bg-white border-l border-slate-200 p-6 overflow-y-auto">
          <h3 class="font-bold text-gray-900 mb-4">Danh sách câu hỏi</h3>
          <div class="grid grid-cols-5 gap-2">
            <button
              v-for="(qid, idx) in attempt.questions_order"
              :key="qid"
              @click="jumpToQuestion(idx)"
              class="h-10 w-10 rounded-lg text-sm font-bold flex items-center justify-center transition-all"
              :class="[
                currentQuestionIndex === idx
                  ? 'bg-indigo-600 text-white shadow-lg shadow-indigo-200'
                  : 'bg-slate-100 text-slate-600 hover:bg-slate-200',
              ]"
            >
              {{ idx + 1 }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
