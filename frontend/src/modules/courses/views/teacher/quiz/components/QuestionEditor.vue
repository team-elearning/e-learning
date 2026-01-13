<script setup lang="ts">
import { ref, watch, reactive } from 'vue'
import type {
  QuizQuestion,
  AnswerPayload,
  QuestionPromptOption,
} from '@/modules/courses/types/quiz.types'
import { instructorQuizApi } from '@/modules/courses/api/instructor-quiz.api'
import { ElMessage } from 'element-plus'
import { Save, Trash } from 'lucide-vue-next'

const props = defineProps<{
  question: QuizQuestion
}>()

const emit = defineEmits<{
  (e: 'update', question: QuizQuestion): void
}>()

const isSaving = ref(false)

const form = reactive<{
  score: number
  promptText: string
  options: QuestionPromptOption[]
  answerPayload: AnswerPayload
}>({
  score: 1,
  promptText: '',
  options: [],
  answerPayload: {},
})

watch(
  () => props.question,
  (newVal) => {
    if (!newVal) return

    const prompt = newVal.prompt || {}
    const answerPayload = newVal.answer_payload || {}

    form.score = typeof newVal.score === 'number' ? newVal.score : 1
    form.promptText = (prompt as any).text || (prompt as any).content || ''
    form.options = Array.isArray(prompt.options) ? [...prompt.options] : []

    form.answerPayload = JSON.parse(JSON.stringify(answerPayload || {}))

    if (newVal.type.includes('multiple_choice') && form.options.length === 0) {
      form.options = [
        { id: crypto.randomUUID(), text: '' },
        { id: crypto.randomUUID(), text: '' },
      ]
    }

    if (
      newVal.type === 'multiple_choice_multi' &&
      !Array.isArray((form.answerPayload as any).correct_ids)
    ) {
      ;(form.answerPayload as any).correct_ids = []
    }
  },
  { immediate: true },
)

async function handleSave() {
  isSaving.value = true
  try {
    const payload: Partial<QuizQuestion> = {
      score: form.score,
      prompt: {
        ...props.question.prompt,
        content: form.promptText,
        text: form.promptText,
        options: form.options,
      },
      answer_payload: form.answerPayload,
    }

    const res = await instructorQuizApi.updateQuestion(props.question.id, payload)
    emit('update', res.data.instance)
    ElMessage.success('Đã lưu câu hỏi')
  } catch (error) {
    ElMessage.error('Lưu thất bại')
    console.error(error)
  } finally {
    isSaving.value = false
  }
}

function addOption() {
  form.options.push({ id: crypto.randomUUID(), text: '' })
}

function removeOption(idx: number) {
  form.options.splice(idx, 1)
}

function setCorrectOption(optionId: string) {
  if (props.question.type === 'multiple_choice_single') {
    ;(form.answerPayload as any).correct_id = optionId
  } else if (props.question.type === 'multiple_choice_multi') {
    const current = ((form.answerPayload as any).correct_ids as string[]) || []
    if (current.includes(optionId)) {
      ;(form.answerPayload as any).correct_ids = current.filter((id) => id !== optionId)
    } else {
      ;(form.answerPayload as any).correct_ids = [...current, optionId]
    }
  }
}

function isOptionCorrect(optionId: string) {
  if (props.question.type === 'multiple_choice_single') {
    return (form.answerPayload as any).correct_id === optionId
  }
  if (props.question.type === 'multiple_choice_multi') {
    return ((form.answerPayload as any).correct_ids as string[] | undefined)?.includes(optionId)
  }
  return false
}

function setTrueFalse(val: boolean) {
  ;(form.answerPayload as any).correct_value = val
}
</script>

<template>
  <div class="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-6">
    <div class="flex items-start justify-between gap-4">
      <div class="space-y-1">
        <p class="text-xs uppercase tracking-wide text-slate-400">Câu hỏi #{{ question.order }}</p>
        <h3 class="text-lg font-semibold text-slate-900">Chỉnh sửa câu hỏi</h3>
      </div>
      <div class="flex items-center gap-3">
        <div class="flex items-center gap-2 text-sm text-slate-600">
          <span class="text-xs uppercase font-semibold text-slate-400">Điểm</span>
          <input
            v-model.number="form.score"
            type="number"
            min="0"
            class="w-16 px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
          />
        </div>
        <span class="px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
          {{ question.type }}
        </span>
      </div>
    </div>

    <div class="space-y-2">
      <label class="block text-sm font-medium text-slate-700">Đề bài</label>
      <textarea
        v-model="form.promptText"
        rows="3"
        class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
        placeholder="Nhập nội dung câu hỏi..."
      ></textarea>
    </div>

    <div>
      <label class="block text-sm font-semibold text-slate-700 mb-2">Cấu hình đáp án</label>

      <div v-if="question.type.includes('multiple_choice')" class="space-y-2">
        <div
          v-for="(opt, idx) in form.options"
          :key="opt.id"
          class="group flex items-center gap-3 p-3 border border-slate-200 rounded-lg bg-slate-50"
        >
          <button
            @click="setCorrectOption(opt.id)"
            class="w-8 h-8 rounded-full border flex items-center justify-center transition-all"
            :class="[
              isOptionCorrect(opt.id)
                ? 'border-green-500 bg-green-500 text-white'
                : 'border-slate-300 hover:border-green-400 text-transparent',
            ]"
            :title="isOptionCorrect(opt.id) ? 'Đáp án đúng' : 'Chọn làm đáp án đúng'"
          >
            <span v-if="isOptionCorrect(opt.id)" class="text-[10px] font-bold">&#10003;</span>
          </button>

          <input
            v-model="opt.text"
            type="text"
            class="flex-1 px-3 py-2 bg-white border border-slate-200 rounded-lg focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all text-sm"
            :placeholder="`Lựa chọn ${idx + 1}`"
          />

          <button
            @click="removeOption(idx)"
            class="p-2 text-slate-300 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
          >
            <Trash class="w-4 h-4" />
          </button>
        </div>

        <button
          @click="addOption"
          class="text-sm font-medium text-indigo-600 hover:text-indigo-700 mt-1 flex items-center gap-1"
        >
          + Thêm lựa chọn
        </button>
      </div>

      <div v-else-if="question.type === 'true_false'" class="space-y-3">
        <label class="block text-sm font-medium text-slate-700">Chọn đáp án đúng</label>
        <div class="flex gap-4">
          <button
            @click="setTrueFalse(true)"
            class="px-6 py-3 rounded-lg border-2 font-semibold transition-all flex items-center gap-2"
            :class="
              form.answerPayload.correct_value === true
                ? 'border-green-500 bg-green-50 text-green-700'
                : 'border-slate-200 text-slate-600 hover:border-green-200'
            "
          >
            ĐÚNG
            <span v-if="form.answerPayload.correct_value === true" class="text-green-600"
              >&#10003;</span
            >
          </button>

          <button
            @click="setTrueFalse(false)"
            class="px-6 py-3 rounded-lg border-2 font-semibold transition-all flex items-center gap-2"
            :class="
              form.answerPayload.correct_value === false
                ? 'border-red-500 bg-red-50 text-red-700'
                : 'border-slate-200 text-slate-600 hover:border-red-200'
            "
          >
            SAI
            <span v-if="form.answerPayload.correct_value === false" class="text-red-600"
              >&#10003;</span
            >
          </button>
        </div>
      </div>

      <div
        v-else-if="['short_answer', 'essay'].includes(question.type)"
        class="p-4 bg-slate-50 rounded-lg border border-slate-200 text-sm text-slate-600 space-y-3"
      >
        <div>
          <span v-if="question.type === 'essay'">Câu hỏi tự luận sẽ được chấm thủ công.</span>
          <span v-else>Học viên nhập đáp án văn bản; cấu hình đáp án chấp nhận bên dưới.</span>
        </div>

        <div v-if="question.type === 'short_answer'" class="space-y-2">
          <label class="block text-xs font-bold uppercase text-slate-500">Đáp án chấp nhận</label>
          <textarea
            class="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm"
            placeholder="Mỗi dòng một đáp án..."
            :value="(form.answerPayload as any).accepted_texts?.join('\n')"
            @input="
              (e: any) => ((form.answerPayload as any).accepted_texts = e.target.value.split('\n'))
            "
          ></textarea>
        </div>
      </div>

      <div v-else class="text-slate-500 italic text-sm">
        Trình chỉnh sửa cho dạng câu hỏi này sẽ sớm có.
      </div>
    </div>

    <div class="pt-4 border-t border-slate-100 space-y-2">
      <label class="block text-sm font-medium text-slate-700">Giải thích đáp án</label>
      <textarea
        v-model="(form.answerPayload as any).explanation"
        rows="2"
        class="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 text-sm"
        placeholder="Hiển thị lời giải cho học viên sau khi nộp bài..."
      ></textarea>
    </div>

    <div class="flex justify-end pt-2">
      <button
        @click="handleSave"
        :disabled="isSaving"
        class="px-4 py-2 bg-indigo-600 text-white text-sm font-semibold rounded-lg hover:bg-indigo-700 transition shadow-sm flex items-center gap-2 disabled:opacity-70"
      >
        <Save class="w-4 h-4" />
        {{ isSaving ? 'Đang lưu...' : 'Lưu câu hỏi' }}
      </button>
    </div>
  </div>
</template>
