<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { teacherCourseApi, type CreateModuleDto } from '../../../api/teacher-course.api'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  GripVertical,
  Edit2,
  Trash2,
  ChevronDown,
  ChevronRight,
  FileText,
  Video,
  HelpCircle,
  Layout,
} from 'lucide-vue-next'
import draggable from 'vuedraggable'
import TeacherCourseLessonContent from './TeacherCourseLessonContent.vue'

const vFocus = {
  mounted: (el: any) => el.focus(),
}

const props = defineProps<{ courseId: string }>()

const modules = ref<any[]>([])
const isLoading = ref(false)
const showAddModule = ref(false)
const newModuleTitle = ref('')

const expandedModules = ref<Set<string>>(new Set())
const addingLessonToModuleId = ref<string | null>(null)
const newLessonTitle = ref('')

// Editing State
const editingModuleId = ref<string | null>(null)
const editingLessonId = ref<string | null>(null)
const editTitle = ref('')

// Content Editor State
const showContentEditor = ref(false)
const activeLessonId = ref('')
const activeLessonTitle = ref('')

function openContentEditor(lesson: any) {
  activeLessonId.value = lesson.id
  activeLessonTitle.value = lesson.title
  showContentEditor.value = true
}

function startAddingLesson(moduleId: string) {
  addingLessonToModuleId.value = moduleId
  newLessonTitle.value = ''
}

function toggleModule(moduleId: string) {
  if (expandedModules.value.has(moduleId)) {
    expandedModules.value.delete(moduleId)
  } else {
    expandedModules.value.add(moduleId)
  }
}

async function fetchModules(background = false) {
  if (!background) isLoading.value = true
  try {
    const res = await teacherCourseApi.getModules(props.courseId)
    modules.value = res.data
  } catch (error) {
    ElMessage.error('Lỗi tải danh sách chương')
  } finally {
    isLoading.value = false
  }
}

async function handleCreateModule() {
  if (!newModuleTitle.value.trim()) return
  try {
    await teacherCourseApi.createModule(props.courseId, { title: newModuleTitle.value })
    newModuleTitle.value = ''
    showAddModule.value = false
    ElMessage.success('Tạo chương mới thành công')
    fetchModules(true)
  } catch (error) {
    ElMessage.error('Không thể tạo chương')
  }
}

async function handleDeleteModule(moduleId: string) {
  try {
    await ElMessageBox.confirm(
      'Bạn có chắc chắn muốn xóa chương này và toàn bộ bài học bên trong?',
      'Xác nhận xóa',
      {
        type: 'warning',
        confirmButtonText: 'Xóa',
        cancelButtonText: 'Hủy',
      },
    )
    await teacherCourseApi.deleteModule(moduleId)
    ElMessage.success('Đã xóa chương')
    modules.value = modules.value.filter((m) => m.id !== moduleId)
  } catch {
    // cancelled
  }
}

async function onModuleDrop(evt: any) {
  // Optimistic Update is tricky with full list replacement api
  // We just call API with new order
  const module_ids = modules.value.map((m) => m.id)
  try {
    await teacherCourseApi.reorderModules(props.courseId, module_ids)
    // Silent success
  } catch (error) {
    ElMessage.error('Lỗi khi lưu thứ tự')
    fetchModules(true) // revert
  }
}

// --- Module Editing ---
function startEditModule(module: any) {
  editingModuleId.value = module.id
  editTitle.value = module.title
  editingLessonId.value = null // Close other edits
}

async function saveEditModule() {
  if (!editingModuleId.value || !editTitle.value.trim()) return
  const id = editingModuleId.value
  const title = editTitle.value
  try {
    await teacherCourseApi.updateModule(id, { title })
    const m = modules.value.find((x) => x.id === id)
    if (m) m.title = title
    ElMessage.success('Cập nhật tên chương thành công')
    editingModuleId.value = null
  } catch (error) {
    ElMessage.error('Lỗi cập nhật tên chương')
  }
}

// --- Lessons Logic ---

async function handleCreateLesson(moduleId: string) {
  if (!newLessonTitle.value.trim()) return

  try {
    await teacherCourseApi.createLesson(moduleId, { title: newLessonTitle.value })
    ElMessage.success('Thêm bài học thành công')
    newLessonTitle.value = ''
    addingLessonToModuleId.value = null
    // Refresh to get new lesson
    await fetchModules(true)
    // Auto expand
    expandedModules.value.add(moduleId)
  } catch (error) {
    ElMessage.error('Không thể tạo bài học')
  }
}

async function handleDeleteLesson(lessonId: string) {
  try {
    await ElMessageBox.confirm('Bạn có chắc muốn xóa bài học này?', 'Xác nhận', {
      type: 'warning',
      confirmButtonText: 'Xóa',
    })
    await teacherCourseApi.deleteLesson(lessonId)
    ElMessage.success('Đã xóa bài học')
    await fetchModules(true)
  } catch {
    // cancelled
  }
}

async function onLessonDrop(evt: any, moduleId: string) {
  const module = modules.value.find((m) => m.id === moduleId)
  if (!module || !module.lessons) return

  const lessonIds = module.lessons.map((l: any) => l.id)
  try {
    // Assuming backend handles reorder within the same module
    // If moving between modules, 'evt' would need more inspection
    await teacherCourseApi.reorderLessons(props.courseId, moduleId, lessonIds)
  } catch (error) {
    ElMessage.error('Lỗi lưu thứ tự bài học')
    fetchModules(true)
  }
}

// --- Lesson Editing ---
function startEditLesson(lesson: any) {
  editingLessonId.value = lesson.id
  editTitle.value = lesson.title
  editingModuleId.value = null // Close other edits
}

async function saveEditLesson(moduleId: string) {
  if (!editingLessonId.value || !editTitle.value.trim()) return
  const id = editingLessonId.value
  const title = editTitle.value
  try {
    await teacherCourseApi.updateLesson(id, { title })

    // Update local state without fetch
    const module = modules.value.find((m) => m.id === moduleId)
    if (module && module.lessons) {
      const l = module.lessons.find((x: any) => x.id === id)
      if (l) l.title = title
    }

    ElMessage.success('Cập nhật tên bài học thành công')
    editingLessonId.value = null
  } catch (error) {
    ElMessage.error('Lỗi cập nhật tên bài học')
  }
}

onMounted(() => {
  fetchModules()
})
</script>

<template>
  <div class="max-w-4xl mx-auto py-6">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-lg font-bold text-gray-900">Nội dung khóa học</h2>
      <button
        @click="showAddModule = true"
        class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition flex items-center gap-2"
      >
        <Plus class="w-4 h-4" /> Thêm chương
      </button>
    </div>

    <!-- Add Module Form -->
    <div
      v-if="showAddModule"
      class="bg-indigo-50 border border-indigo-100 rounded-xl p-4 mb-4 animate-in fade-in slide-in-from-top-2"
    >
      <h3 class="font-semibold text-indigo-900 mb-3">Thêm chương mới</h3>
      <div class="flex gap-2">
        <input
          v-model="newModuleTitle"
          type="text"
          placeholder="Nhập tên chương (VD: Chương 1: Giới thiệu)"
          class="flex-1 px-4 py-2 border border-indigo-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 bg-white"
          @keyup.enter="handleCreateModule"
        />
        <button
          @click="handleCreateModule"
          class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-medium hover:bg-indigo-700 transition"
        >
          Lưu
        </button>
        <button
          @click="showAddModule = false"
          class="bg-white text-slate-600 px-4 py-2 rounded-lg font-medium hover:bg-slate-50 transition border border-slate-200"
        >
          Hủy
        </button>
      </div>
    </div>

    <!-- Modules List -->
    <div v-if="isLoading" class="space-y-4">
      <div class="h-16 bg-slate-100 rounded-xl animate-pulse" v-for="i in 3" :key="i"></div>
    </div>

    <div v-else class="space-y-4">
      <draggable
        v-model="modules"
        group="modules"
        @end="onModuleDrop"
        item-key="id"
        handle=".drag-handle"
        :animation="200"
      >
        <template #item="{ element: module }">
          <div class="bg-white border border-slate-200 rounded-xl overflow-hidden group mb-4">
            <div
              class="bg-slate-50 px-4 py-3 flex items-center gap-3 border-b border-slate-100 cursor-pointer select-none"
              @click="toggleModule(module.id)"
            >
              <div class="drag-handle cursor-grab text-slate-400 hover:text-slate-600 p-1">
                <GripVertical class="w-5 h-5" />
              </div>
              <div
                class="text-slate-500 transition-transform duration-200"
                :class="{ 'rotate-90': expandedModules.has(module.id) }"
              >
                <ChevronRight class="w-5 h-5" />
              </div>

              <!-- Title or Edit Input -->
              <div class="flex-1 font-bold text-gray-800" v-if="editingModuleId !== module.id">
                {{ module.title }}
              </div>
              <div class="flex-1 flex gap-2" v-else @click.stop>
                <input
                  v-model="editTitle"
                  class="px-2 py-1 border border-indigo-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm w-full"
                  @keyup.enter="saveEditModule"
                  @keyup.esc="editingModuleId = null"
                  v-focus
                  ref="editModuleInput"
                />
                <button
                  @click="saveEditModule"
                  class="text-indigo-600 text-xs font-bold px-2 hover:bg-indigo-50 rounded"
                >
                  Lưu
                </button>
                <button
                  @click="editingModuleId = null"
                  class="text-slate-500 text-xs px-2 hover:bg-slate-100 rounded"
                >
                  Hủy
                </button>
              </div>

              <div class="flex items-center gap-2" v-if="editingModuleId !== module.id">
                <button
                  class="p-2 text-slate-400 hover:text-indigo-600 transition"
                  @click.stop="startEditModule(module)"
                >
                  <Edit2 class="w-4 h-4" />
                </button>
                <button
                  @click.stop="handleDeleteModule(module.id)"
                  class="p-2 text-slate-400 hover:text-red-600 transition"
                >
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>

            <!-- Lessons Container -->
            <div v-if="expandedModules.has(module.id)" class="bg-white">
              <draggable
                v-model="module.lessons"
                group="lessons"
                item-key="id"
                handle=".lesson-drag"
                @end="(e: any) => onLessonDrop(e, module.id)"
                class="divide-y divide-slate-100"
              >
                <template #item="{ element: lesson }">
                  <div
                    class="pl-12 pr-4 py-3 flex items-center gap-3 hover:bg-slate-50 group/lesson"
                  >
                    <div class="lesson-drag cursor-grab text-slate-300 hover:text-slate-500">
                      <GripVertical class="w-4 h-4" />
                    </div>
                    <div class="p-1.5 bg-indigo-50 rounded text-indigo-600">
                      <FileText class="w-4 h-4" />
                    </div>

                    <!-- Lesson Title or Edit -->
                    <div
                      class="flex-1 text-sm font-medium text-slate-700"
                      v-if="editingLessonId !== lesson.id"
                    >
                      {{ lesson.title }}
                    </div>
                    <div class="flex-1 flex gap-2" v-else>
                      <input
                        v-model="editTitle"
                        class="px-2 py-1 border border-indigo-300 rounded focus:outline-none focus:ring-1 focus:ring-indigo-500 text-sm w-full"
                        @keyup.enter="saveEditLesson(module.id)"
                        @keyup.esc="editingLessonId = null"
                        v-focus
                      />
                      <button
                        @click="saveEditLesson(module.id)"
                        class="text-indigo-600 text-xs font-bold px-2 hover:bg-indigo-50 rounded"
                      >
                        Lưu
                      </button>
                      <button
                        @click="editingLessonId = null"
                        class="text-slate-500 text-xs px-2 hover:bg-slate-100 rounded"
                      >
                        Hủy
                      </button>
                    </div>

                    <div
                      class="flex items-center gap-2 opacity-0 group-hover/lesson:opacity-100 transition-opacity"
                      v-if="editingLessonId !== lesson.id"
                    >
                      <button
                        class="p-1.5 text-slate-400 hover:text-indigo-600 flex items-center gap-1 bg-white border border-slate-200 rounded px-2"
                        @click="openContentEditor(lesson)"
                      >
                        <Layout class="w-3 h-3" />
                        <span class="text-xs">Nội dung</span>
                      </button>
                      <button
                        class="p-1.5 text-slate-400 hover:text-indigo-600"
                        @click="startEditLesson(lesson)"
                      >
                        <Edit2 class="w-3.5 h-3.5" />
                      </button>
                      <button
                        @click="handleDeleteLesson(lesson.id)"
                        class="p-1.5 text-slate-400 hover:text-red-600"
                      >
                        <Trash2 class="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </template>
              </draggable>

              <!-- Add Lesson Form -->
              <div
                v-if="addingLessonToModuleId === module.id"
                class="pl-12 pr-4 py-3 bg-indigo-50/50"
              >
                <div class="flex gap-2">
                  <input
                    v-model="newLessonTitle"
                    ref="accor"
                    class="flex-1 px-3 py-1.5 text-sm border border-indigo-200 rounded focus:outline-none focus:border-indigo-500"
                    placeholder="Nhập tên bài học..."
                    @keyup.enter="handleCreateLesson(module.id)"
                  />
                  <button
                    @click="handleCreateLesson(module.id)"
                    class="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded font-medium"
                  >
                    Lưu
                  </button>
                  <button
                    @click="addingLessonToModuleId = null"
                    class="px-3 py-1.5 bg-white border border-slate-200 text-slate-600 text-sm rounded"
                  >
                    Hủy
                  </button>
                </div>
              </div>

              <!-- Add Lesson Button -->
              <div
                v-else
                class="p-3 pl-12 flex items-center text-slate-500 hover:text-indigo-600 hover:bg-slate-50 cursor-pointer transition text-sm font-medium"
                @click="startAddingLesson(module.id)"
              >
                <Plus class="w-4 h-4 mr-2" /> Thêm bài học
              </div>
            </div>
          </div>
        </template>
      </draggable>

      <div
        v-if="modules.length === 0"
        class="text-center py-12 text-slate-500 bg-white border border-slate-200 border-dashed rounded-xl"
      >
        Chưa có nội dung nào. Hãy bắt đầu bằng việc thêm chương mới.
      </div>

      <!-- Content Drawer -->
      <TeacherCourseLessonContent
        v-if="showContentEditor"
        v-model="showContentEditor"
        :lesson-id="activeLessonId"
        :lesson-title="activeLessonTitle"
      />
    </div>
  </div>
</template>
