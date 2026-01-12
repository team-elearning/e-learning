<script setup lang="ts">
import type { Quiz, Question, QuizOption } from '../../../types/course.types'

defineProps<{
  quiz: Quiz
}>()

function isCorrect(q: Question, optionId: string): boolean {
  if (q.type === 'multiple_choice_single') {
    return q.answer_payload.correct_id === optionId
  }
  if (q.type === 'multiple_choice_multi') {
    return q.answer_payload.correct_ids?.includes(optionId) || false
  }
  return false
}

function getQuestionTypeLabel(type: string): string {
  const map: Record<string, string> = {
    multiple_choice_single: 'Chọn một đáp án',
    multiple_choice_multi: 'Chọn nhiều đáp án',
    true_false: 'Đúng / Sai',
    short_answer: 'Câu trả lời ngắn',
  }
  return map[type] || type
}
</script>

<template>
  <div class="w-full max-w-3xl mx-auto pb-10">
    <div class="mb-8 border-b border-slate-200 pb-6">
      <h2 class="text-2xl font-bold text-gray-900 mb-2">
        {{ quiz.title || 'Bài kiểm tra không tên' }}
      </h2>
      <div class="flex items-center gap-4 text-sm text-slate-500">
        <div class="flex items-center gap-1">
          <span>❓</span> {{ quiz.questions.length }} câu hỏi
        </div>
      </div>
    </div>

    <div class="space-y-8">
      <div
        v-for="(q, index) in quiz.questions"
        :key="q.id"
        class="bg-white rounded-xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow"
      >
        <!-- Question Header -->
        <div class="flex gap-4 mb-4">
          <div
            class="h-8 min-w-[32px] rounded-lg bg-indigo-50 text-[rgb(var(--primary))] font-bold flex items-center justify-center text-sm"
          >
            {{ index + 1 }}
          </div>
          <div class="flex-1">
            <div class="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">
              {{ getQuestionTypeLabel(q.type) }}
            </div>
            <h3 class="font-semibold text-gray-900 text-lg leading-snug">
              {{ q.prompt.content }}
            </h3>
          </div>
        </div>

        <!-- Render Options based on Type -->
        <div class="pl-[48px] space-y-3">
          <!-- Multiple Choice (Single & Multi) -->
          <template v-if="['multiple_choice_single', 'multiple_choice_multi'].includes(q.type)">
            <div
              v-for="opt in q.prompt.options"
              :key="opt.id"
              class="group flex items-start gap-3 p-3 rounded-lg border transition-all"
              :class="
                isCorrect(q, opt.id)
                  ? 'bg-emerald-50 border-emerald-200 shadow-sm'
                  : 'bg-white border-slate-100 text-slate-600'
              "
            >
              <div
                class="mt-0.5 w-5 h-5 flex items-center justify-center border transition-colors"
                :class="[
                  q.type === 'multiple_choice_single' ? 'rounded-full' : 'rounded-md',
                  isCorrect(q, opt.id)
                    ? 'bg-emerald-500 border-emerald-500 text-white'
                    : 'border-slate-300 bg-white',
                ]"
              >
                <span v-if="isCorrect(q, opt.id)" class="text-[10px]">✓</span>
              </div>
              <div class="flex-1 text-sm font-medium">
                {{ opt.text }}
              </div>
            </div>
          </template>

          <!-- True / False -->
          <template v-else-if="q.type === 'true_false'">
            <div class="flex gap-4">
              <div
                class="flex-1 p-4 rounded-lg border text-center font-bold cursor-default transition-all"
                :class="
                  q.answer_payload.correct_value === true
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-700 shadow-sm ring-1 ring-emerald-200'
                    : 'bg-white border-slate-200 text-slate-400 opacity-60'
                "
              >
                Đúng (True)
              </div>
              <div
                class="flex-1 p-4 rounded-lg border text-center font-bold cursor-default transition-all"
                :class="
                  q.answer_payload.correct_value === false
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-700 shadow-sm ring-1 ring-emerald-200'
                    : 'bg-white border-slate-200 text-slate-400 opacity-60'
                "
              >
                Sai (False)
              </div>
            </div>
          </template>

          <!-- Short Answer -->
          <template v-else-if="q.type === 'short_answer'">
            <div class="bg-slate-50 border border-slate-200 rounded-lg p-4">
              <div class="text-xs text-slate-500 font-bold uppercase mb-2">Đáp án chấp nhận:</div>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="(ans, i) in q.answer_payload.accepted_texts"
                  :key="i"
                  class="px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm font-medium border border-emerald-200"
                >
                  {{ ans }}
                </span>
              </div>
            </div>
          </template>

          <!-- Fallback -->
          <template v-else>
            <div class="text-sm text-slate-400 italic">
              Loại câu hỏi này chưa được hỗ trợ hiển thị xem trước.
            </div>
          </template>

          <!-- Explanation (if any) -->
          <div v-if="q.answer_payload.explanation" class="mt-4 pt-3 border-t border-slate-100">
            <div class="text-xs font-bold text-slate-500 flex items-center gap-1 mb-1">
              <span>💡</span> Giải thích:
            </div>
            <div class="text-sm text-slate-600 italic">
              {{ q.answer_payload.explanation }}
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
