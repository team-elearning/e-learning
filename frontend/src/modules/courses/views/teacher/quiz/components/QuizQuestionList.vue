<script setup lang="ts">
import { ref, watch } from 'vue'
import type { QuizQuestion, QuestionType } from '@/modules/courses/types/quiz.types'
import { Plus, GripVertical, ChevronDown, Trash2 } from 'lucide-vue-next'
import { ElDropdown, ElDropdownMenu, ElDropdownItem } from 'element-plus'

import QuestionEditor from './QuestionEditor.vue'

const props = defineProps<{
  questions: QuizQuestion[]
  loading?: boolean
}>()

const emit = defineEmits<{
  (e: 'create', type: QuestionType): void
  (e: 'delete', id: string): void
  (e: 'update', question: QuizQuestion): void
}>()

const expandedQuestions = ref(new Set<string>())
const lastIds = ref<string[]>([])

function setExpanded(next: Set<string>) {
  expandedQuestions.value = next
}

function toggleExpand(id: string) {
  const next = new Set(expandedQuestions.value)
  if (next.has(id)) {
    next.delete(id)
  } else {
    next.add(id)
  }
  setExpanded(next)
}

function handleCreate(type: QuestionType) {
  emit('create', type)
}

// Tự động mở câu hỏi đầu tiên và câu hỏi vừa thêm
watch(
  () => props.questions.map((q) => q.id),
  (newIds) => {
    const prevIds = lastIds.value
    const added = newIds.find((id) => !prevIds.includes(id))

    const next = new Set(expandedQuestions.value)
    if (added) {
      next.add(added)
    } else if (!prevIds.length && newIds[0]) {
      next.add(newIds[0])
    }
    setExpanded(next)
    lastIds.value = [...newIds]
  },
  { immediate: true },
)

function getQuestionTypeLabel(type: QuestionType) {
  const map: Record<string, string> = {
    multiple_choice_single: 'Trắc nghiệm (1 đáp án)',
    multiple_choice_multi: 'Trắc nghiệm (nhiều đáp án)',
    true_false: 'Đúng / Sai',
    short_answer: 'Trả lời ngắn',
    essay: 'Tự luận',
    fill_in_the_blank: 'Điền vào chỗ trống',
    matching: 'Nối đáp án',
    ordering: 'Sắp xếp',
    numeric: 'Số học',
  }
  return map[type] || type
}

const questionTypes: { type: QuestionType; label: string }[] = [
  { type: 'multiple_choice_single', label: 'Trắc nghiệm (1 đáp án)' },
  { type: 'multiple_choice_multi', label: 'Trắc nghiệm (nhiều đáp án)' },
  { type: 'true_false', label: 'Đúng / Sai' },
  { type: 'short_answer', label: 'Trả lời ngắn' },
  { type: 'essay', label: 'Tự luận' },
]
</script>

<template>
  <div class="space-y-4 pb-20">
    <!-- Empty State -->
    <div
      v-if="!loading && questions.length === 0"
      class="text-center py-12 bg-white rounded-xl border-2 border-dashed border-slate-200"
    >
      <div class="w-16 h-16 bg-slate-50 rounded-full flex items-center justify-center mx-auto mb-4">
        <Plus class="w-8 h-8 text-slate-400" />
      </div>
      <h3 class="text-lg font-medium text-slate-900">Chưa có câu hỏi nào</h3>
      <p class="text-slate-500 mb-6 max-w-sm mx-auto">
        Vui lòng thêm câu hỏi mới để bắt đầu xây dựng đề thi.
      </p>

      <el-dropdown trigger="click" @command="handleCreate">
        <button
          class="px-5 py-2 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition shadow-lg shadow-indigo-500/30 flex items-center gap-2 mx-auto"
        >
          <Plus class="w-5 h-5" /> Thêm câu hỏi
        </button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item v-for="t in questionTypes" :key="t.type" :command="t.type">
              {{ t.label }}
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>

    <!-- Question List -->
    <div v-else class="space-y-4">
      <div
        v-for="(q, index) in questions"
        :key="q.id"
        class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden transition-all group"
        :class="{ 'ring-2 ring-indigo-500/20 border-indigo-500/50': expandedQuestions.has(q.id) }"
      >
        <!-- Header (Click to expand) -->
        <div
          class="flex items-center p-4 cursor-pointer select-none bg-slate-50 hover:bg-slate-100 transition-colors"
          @click="toggleExpand(q.id)"
        >
          <div class="mr-3 cursor-move text-slate-400 hover:text-slate-600">
            <GripVertical class="w-5 h-5" />
          </div>

          <div
            class="flex items-center justify-center w-8 h-8 bg-white border border-slate-200 rounded-lg text-sm font-bold text-slate-700 mr-4 shadow-sm"
          >
            {{ index + 1 }}
          </div>

          <div class="flex-1 min-w-0">
            <div
              class="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-slate-500 mb-0.5"
            >
              <span class="px-2 py-0.5 bg-slate-200 rounded text-slate-600">{{
                getQuestionTypeLabel(q.type)
              }}</span>
              <span v-if="q.score > 0" class="text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded"
                >{{ q.score }} điểm</span
              >
            </div>
            <h4
              class="font-medium text-slate-900 truncate"
              v-html="
                q.prompt.text ||
                q.prompt.content ||
                '<span class=\'text-slate-400 italic\'>Chưa có nội dung câu hỏi</span>'
              "
            ></h4>
          </div>

          <div class="flex items-center gap-2 ml-4">
            <button
              @click.stop="emit('delete', q.id)"
              class="p-2 text-slate-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
              title="Xóa"
            >
              <Trash2 class="w-4 h-4" />
            </button>
            <ChevronDown
              class="w-5 h-5 text-slate-400 transition-transform duration-200"
              :class="{ 'rotate-180': expandedQuestions.has(q.id) }"
            />
          </div>
        </div>

        <!-- Editor Body -->
        <div
          v-if="expandedQuestions.has(q.id)"
          class="border-t border-slate-200 p-6 animate-in slide-in-from-top-2 duration-200"
        >
          <QuestionEditor :question="q" @update="(u) => emit('update', u)" />
        </div>
      </div>

      <!-- Add Button at bottom -->
      <div class="flex justify-center pt-4">
        <el-dropdown trigger="click" @command="handleCreate">
          <button
            class="px-5 py-2 bg-white border border-slate-200 text-slate-700 rounded-lg font-semibold hover:bg-slate-50 hover:border-slate-300 transition shadow-sm flex items-center gap-2"
          >
            <Plus class="w-5 h-5 text-indigo-600" /> Thêm câu hỏi mới
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item v-for="t in questionTypes" :key="t.type" :command="t.type">
                {{ t.label }}
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>
