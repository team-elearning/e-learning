<script setup lang="ts">
import { ref, reactive, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  teacherCourseApi,
  type UpdateCourseDto,
  type CreateCourseDto,
} from '../../../api/teacher-course.api'
import type { Course } from '../../../types/course.types'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Loader2, Save } from 'lucide-vue-next'

const props = defineProps<{ course: Course }>()
const emit = defineEmits(['updated'])
const router = useRouter()

const isSubmitting = ref(false)

// Init form with props
const form = reactive<UpdateCourseDto>({
  title: props.course.title,
  description: props.course.description || '',
  price: Number(props.course.price) || 0,
  grade: props.course.grade ? Number(props.course.grade) : undefined,
  subject:
    typeof props.course.subject === 'object'
      ? (props.course.subject as any).id
      : props.course.subject,
  published: props.course.published,
})

async function handleSave() {
  isSubmitting.value = true
  try {
    const payload: UpdateCourseDto = {}

    // Compare and add to payload
    if (form.title !== props.course.title) payload.title = form.title
    if (form.description !== (props.course.description || ''))
      payload.description = form.description
    if (form.published !== props.course.published) payload.published = form.published

    // Check specific fields if they differ
    if (Number(form.price) !== Number(props.course.price || 0)) payload.price = form.price
    if (Number(form.grade) !== Number(props.course.grade)) payload.grade = form.grade

    // Subject handling: Only update if changed (simple string comparison usually)
    const currentSubjectId =
      typeof props.course.subject === 'object'
        ? (props.course.subject as any).id
        : props.course.subject
    if (form.subject !== currentSubjectId) {
      payload.subject = form.subject
    }

    if (Object.keys(payload).length === 0) {
      ElMessage.info('Không có thay đổi nào')
      isSubmitting.value = false
      return
    }

    await teacherCourseApi.updateCourse(props.course.id, payload)
    ElMessage.success('Lưu thay đổi thành công')
    emit('updated')
  } catch (error) {
    ElMessage.error('Không thể lưu thay đổi')
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm(
      'Bạn có chắc chắn muốn xóa khóa học này không? Hành động này không thể hoàn tác.',
      'Cảnh báo xóa khóa học',
      {
        confirmButtonText: 'Xóa vĩnh viễn',
        cancelButtonText: 'Hủy',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )

    await teacherCourseApi.deleteCourse(props.course.id)
    ElMessage.success('Đã xóa khóa học thành công')
    router.replace('/teacher/courses')
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('Không thể xóa khóa học')
    }
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto py-6">
    <!-- Simple Form similar to Create but with Save button -->
    <div class="space-y-6">
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Tên khóa học</label>
        <input
          v-model="form.title"
          class="w-full px-4 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
        />
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Mô tả</label>
        <textarea
          v-model="form.description"
          rows="5"
          class="w-full px-4 py-2 border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-indigo-500"
        ></textarea>
      </div>

      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Trạng thái</label>
        <div class="flex items-center gap-3">
          <el-switch
            v-model="form.published"
            active-text="Công khai (Published)"
            inactive-text="Nháp (Draft)"
          />
        </div>
      </div>

      <div class="pt-6">
        <button
          @click="handleSave"
          :disabled="isSubmitting"
          class="bg-indigo-600 text-white px-6 py-2.5 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center gap-2 shadow-sm"
        >
          <Loader2 v-if="isSubmitting" class="w-5 h-5 animate-spin" />
          <Save v-else class="w-5 h-5" />
          Lưu thay đổi
        </button>
      </div>

      <!-- Danger Zone -->
      <div class="pt-8 border-t border-slate-200 mt-8">
        <h3 class="text-lg font-medium text-red-600 mb-4">Vùng nguy hiểm</h3>
        <div
          class="bg-red-50 border border-red-200 rounded-lg p-5 flex items-center justify-between"
        >
          <div>
            <p class="font-medium text-red-800">Xóa khóa học này</p>
            <p class="text-sm text-red-600 mt-1">
              Một khi đã xóa, không thể khôi phục lại dữ liệu. Hãy chắc chắn.
            </p>
          </div>
          <button
            @click="handleDelete"
            class="bg-white border border-red-300 text-red-600 px-4 py-2 rounded-lg font-medium hover:bg-red-50 transition shadow-sm hover:text-red-700 hover:border-red-400"
          >
            Xóa khóa học
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
