<script setup lang="ts">
import { reactive, watch, computed } from 'vue'
import type { QuizSettings } from '@/modules/courses/types/quiz.types'
import { Save } from 'lucide-vue-next'

const props = defineProps<{
  initialData: QuizSettings
  isSaving: boolean
}>()

const emit = defineEmits<{
  (e: 'submit', data: Partial<QuizSettings>): void
}>()

const form = reactive<Partial<QuizSettings>>({
  title: '',
  description: '',
  time_limit: null,
  pass_score: 0,
  max_attempts: 0,
  grading_method: 'highest',
  shuffle_questions: false,
  show_correct_answer: false,
  is_published: false,
})

const isPassScoreInvalid = computed(() => {
  const value = form.pass_score
  return typeof value === 'number' && value > 10
})

watch(
  () => props.initialData,
  (newVal) => {
    if (newVal) {
      Object.assign(form, newVal)
    }
  },
  { immediate: true },
)

function onSubmit() {
  emit('submit', form)
}

const gradingMethods = [
  { label: 'Điểm cao nhất', value: 'highest' },
  { label: 'Điểm trung bình', value: 'average' },
  { label: 'Lần làm đầu tiên', value: 'first' },
  { label: 'Lần làm cuối cùng', value: 'last' },
]
</script>

<template>
  <div class="space-y-6">
    <!-- Basic Info -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h3 class="text-lg font-semibold text-slate-900 mb-4 border-b border-slate-100 pb-2">
        Thông tin cơ bản
      </h3>
      <div class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Tên bài kiểm tra</label>
          <input
            v-model="form.title"
            type="text"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
          />
        </div>

        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Mô tả / Hướng dẫn</label>
          <textarea
            v-model="form.description"
            rows="4"
            class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 transition-all"
            placeholder="Nhập hướng dẫn làm bài cho học viên..."
          ></textarea>
          <p class="text-xs text-slate-500 mt-1">Hỗ trợ HTML cơ bản.</p>
        </div>
      </div>
    </div>

    <!-- Configuration -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Time Settings -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 class="text-lg font-semibold text-slate-900 mb-4 border-b border-slate-100 pb-2">
          Thời gian
        </h3>
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1"
              >Thời gian làm bài (Phút)</label
            >
            <div class="relative">
              <input
                v-model.number="form.time_limit"
                type="number"
                min="0"
                placeholder="0 = Không giới hạn"
                class="w-full pl-3 pr-12 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
              />
              <span class="absolute right-3 top-2 text-slate-400 text-sm">phút</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Grading -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
        <h3 class="text-lg font-semibold text-slate-900 mb-4 border-b border-slate-100 pb-2">
          Điểm số & Lượt làm
        </h3>
        <div class="space-y-4">
          <div>
          <label class="block text-sm font-medium text-slate-700 mb-1"
              >Điểm đạt (Pass Score)</label
          >
          <input
            v-model.number="form.pass_score"
            type="number"
            min="0"
            max="10"
            step="0.1"
            class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            :class="isPassScoreInvalid ? 'border-red-400' : 'border-slate-300'"
          />
          <p v-if="isPassScoreInvalid" class="mt-1 text-xs text-red-600">
            Điểm đạt không được vượt quá 10.
          </p>
        </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Số lần làm tối đa</label>
            <input
              v-model.number="form.max_attempts"
              type="number"
              min="0"
              placeholder="0 = Không giới hạn"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500"
            />
          </div>
          <div>
            <label class="block text-sm font-medium text-slate-700 mb-1">Cách tính điểm</label>
            <select
              v-model="form.grading_method"
              class="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 bg-white"
            >
              <option v-for="method in gradingMethods" :key="method.value" :value="method.value">
                {{ method.label }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Behavior -->
    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h3 class="text-lg font-semibold text-slate-900 mb-4 border-b border-slate-100 pb-2">
        Cấu hình hành vi
      </h3>
      <div class="space-y-4">
        <label
          class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
        >
          <input
            type="checkbox"
            v-model="form.shuffle_questions"
            class="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500 border-gray-300"
          />
          <div>
            <span class="font-medium text-slate-900 block">Đảo câu hỏi</span>
            <span class="text-xs text-slate-500"
              >Thứ tự câu hỏi sẽ được xáo trộn mỗi lần làm bài.</span
            >
          </div>
        </label>

        <label
          class="flex items-center gap-3 p-3 border border-slate-200 rounded-lg cursor-pointer hover:bg-slate-50 transition-colors"
        >
          <input
            type="checkbox"
            v-model="form.show_correct_answer"
            class="w-5 h-5 text-indigo-600 rounded focus:ring-indigo-500 border-gray-300"
          />
          <div>
            <span class="font-medium text-slate-900 block">Hiển thị đáp án</span>
            <span class="text-xs text-slate-500"
              >Cho phép học viên xem đáp án đúng sau khi nộp bài.</span
            >
          </div>
        </label>

        <label
          class="flex items-center gap-3 p-3 border border-emerald-200 bg-emerald-50 rounded-lg cursor-pointer hover:bg-emerald-100 transition-colors"
        >
          <input
            type="checkbox"
            v-model="form.is_published"
            class="w-5 h-5 text-emerald-600 rounded focus:ring-emerald-500 border-emerald-300"
          />
          <div>
            <span class="font-medium text-emerald-900 block">Xuất bản (Publish)</span>
            <span class="text-xs text-emerald-700">Công khai bài kiểm tra này cho học viên.</span>
          </div>
        </label>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex justify-end pt-4 pb-12">
      <button
        @click="onSubmit"
        :disabled="isSaving"
        class="flex items-center gap-2 px-6 py-2.5 bg-indigo-600 text-white font-semibold rounded-lg hover:bg-indigo-700 focus:ring-4 focus:ring-indigo-500/30 transition-all disabled:opacity-70 shadow-lg shadow-indigo-500/20"
      >
        <Save v-if="!isSaving" class="w-5 h-5" />
        <span
          v-else
          class="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"
        ></span>
        {{ isSaving ? 'Đang lưu...' : 'Lưu cài đặt' }}
      </button>
    </div>
  </div>
</template>
