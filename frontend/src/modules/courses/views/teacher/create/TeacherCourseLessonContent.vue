<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { teacherCourseApi, type CreateBlockDto } from '../../../api/teacher-course.api'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Trash2,
  GripVertical,
  Type,
  Video,
  FileCheck,
  FileText,
  X,
  Folder,
  File,
  Youtube,
  UploadCloud,
  Loader2,
  Edit2, // Added Edit2
} from 'lucide-vue-next'
import draggable from 'vuedraggable'
import axios from 'axios'

const props = defineProps<{
  lessonId: string
  lessonTitle: string
  modelValue: boolean
}>()

const emit = defineEmits(['update:modelValue'])

const blocks = ref<any[]>([])
const isLoading = ref(false)
const isSaving = ref(false)
const isUploading = ref(false)

// New block state
const showAddBlock = ref(false)
const showMediaOptions = ref(false) // Toggle media selection
const selectedType = ref<CreateBlockDto['type'] | null>(null)

// Creation State
const newBlockTitle = ref('')

// Editing State
const editingBlockId = ref<string | null>(null)
const editingBlockData = ref({
  title: '',
  content: '', // html_content
  url: '',
  file_id: '',
  filename: '',
  duration: 0,
  has_existing_file: false,
})

const renderTypeIcon = (type: string) => {
  switch (type) {
    case 'video':
      return Video
    case 'quiz':
      return FileCheck
    case 'rich_text':
      return Type
    case 'pdf':
    case 'docx':
      return FileText
    default:
      return FileText
  }
}

async function fetchBlocks() {
  isLoading.value = true
  try {
    const res = await teacherCourseApi.getBlocks(props.lessonId)
    // Assuming API returns array of blocks
    blocks.value = res.data
  } catch (error) {
    ElMessage.error('Không thể tải nội dung bài học')
  } finally {
    isLoading.value = false
  }
}

async function handleAddBlock(type: CreateBlockDto['type']) {
  selectedType.value = type
  showAddBlock.value = true
  showMediaOptions.value = false // Close menu
  newBlockTitle.value = ''
}

const getVideoDuration = (file: File): Promise<number> => {
  return new Promise((resolve) => {
    const video = document.createElement('video')
    video.preload = 'metadata'
    video.onloadedmetadata = () => {
      window.URL.revokeObjectURL(video.src)
      resolve(Math.round(video.duration))
    }
    video.onerror = () => resolve(0)
    video.src = URL.createObjectURL(file)
  })
}

async function handleFileUpload(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  // Extract duration if video
  if (editingBlockData.value.title && file.type.startsWith('video/')) {
    editingBlockData.value.duration = await getVideoDuration(file)
  }

  isUploading.value = true
  try {
    // 1. Init Upload
    const initRes = await teacherCourseApi.uploadInit({
      filename: file.name,
      file_type: file.type,
      file_size: file.size,
      component: 'lesson_material',
    })
    const { file_id, upload_url, upload_fields } = initRes.data

    // 2. Upload to S3
    const formData = new FormData()
    Object.entries(upload_fields).forEach(([key, value]) => {
      formData.append(key, value)
    })
    formData.append('file', file)

    // await axios.post(upload_url, formData, {
    //   headers: { 'Content-Type': 'multipart/form-data' },
    // })

    const s3Res = await axios.post(upload_url, formData, {
      validateStatus: (s) => (s >= 200 && s < 300) || s === 204,
    })
    console.log('S3 upload status:', s3Res.status)

    // 3. Confirm
    await teacherCourseApi.uploadConfirm(file_id)

    // Success
    editingBlockData.value.file_id = file_id
    editingBlockData.value.filename = file.name

    ElMessage.success('Tải file thành công')
  } catch (error) {
    console.error(error)
    ElMessage.error('Tải file thất bại')
  } finally {
    isUploading.value = false
  }
}

async function startEditing(block: any) {
  editingBlockId.value = block.id
  // Reset form data first
  editingBlockData.value = {
    title: block.title,
    content: '',
    url: '',
    file_id: '',
    filename: '',
    duration: 0,
    has_existing_file: false,
  }

  // Fetch full details
  try {
    const res = await teacherCourseApi.getBlockDetail(block.id)
    // Handle both { instance: ... } (Spec A) and direct object (Spec B)
    const data = res.data as any
    const instance = data.instance || data
    const payload = instance.payload || ({} as any)

    if (instance.type === 'rich_text') {
      editingBlockData.value.content = payload.html_content || ''
    } else if (instance.type === 'video') {
      editingBlockData.value.filename = payload.file_name || ''
      editingBlockData.value.duration = payload.duration || 0
      if (payload.file_name) {
        editingBlockData.value.has_existing_file = true
      }
    } else if (['pdf', 'docx'].includes(instance.type)) {
      editingBlockData.value.filename = payload.file_name || ''
      if (payload.file_name) {
        editingBlockData.value.has_existing_file = true
      }
    }
  } catch (error) {
    console.error('Failed to load block details:', error)
    ElMessage.error('Không thể tải chi tiết nội dung')
  }
}

function cancelEditing() {
  editingBlockId.value = null
  editingBlockData.value = {
    title: '',
    content: '',
    url: '',
    file_id: '',
    filename: '',
    duration: 0,
    has_existing_file: false,
  }
}

function clearEditingFile() {
  editingBlockData.value.file_id = ''
  editingBlockData.value.filename = ''
  editingBlockData.value.duration = 0
  editingBlockData.value.has_existing_file = false
}

async function saveEditBlock() {
  const blockId = editingBlockId.value
  if (!blockId) return

  isSaving.value = true
  try {
    const blockType = blocks.value.find((b) => b.id === blockId)?.type
    if (!blockType) return

    // Update Payload (Promote Assets / Sync Metadata)
    let updatePayload: any = {}

    // Always update title
    if (editingBlockData.value.title) {
      updatePayload.title = editingBlockData.value.title
    }

    if (blockType === 'rich_text') {
      updatePayload.payload = {
        html_content: editingBlockData.value.content,
      }
    } else if (blockType === 'video') {
      // Priority: Uploaded File > URL
      if (editingBlockData.value.file_id) {
        updatePayload.payload = {
          staging_video_id: editingBlockData.value.file_id,
          duration: editingBlockData.value.duration || 0,
        }
      }
      // Note: If block already has video, we might not send anything unless changed
    } else if (['pdf', 'docx'].includes(blockType)) {
      if (editingBlockData.value.file_id) {
        updatePayload.payload = {
          staging_file_id: editingBlockData.value.file_id,
          file_name: editingBlockData.value.filename,
        }
      }
    } else if (blockType === 'quiz') {
      updatePayload.payload = {
        title: editingBlockData.value.title,
      }
    }

    await teacherCourseApi.updateBlock(blockId, updatePayload)
    ElMessage.success('Cập nhật nội dung thành công')
    editingBlockId.value = null
    fetchBlocks()
  } catch (error) {
    ElMessage.error('Lỗi cập nhật')
  } finally {
    isSaving.value = false
  }
}

async function saveNewBlock() {
  if (!selectedType.value) return
  if (!newBlockTitle.value) {
    ElMessage.warning('Vui lòng nhập tiêu đề')
    return
  }

  isSaving.value = true
  try {
    // 1. Create Shell Block
    const createPayload: CreateBlockDto = {
      type: selectedType.value,
      title: newBlockTitle.value,
      position: blocks.value.length + 1, // Simple position logic
    }

    await teacherCourseApi.createBlock(props.lessonId, createPayload)

    ElMessage.success('Tạo khối nội dung thành công')
    showAddBlock.value = false
    selectedType.value = null
    newBlockTitle.value = ''
    fetchBlocks()
  } catch (error) {
    ElMessage.error('Lỗi khi tạo khối nội dung')
  } finally {
    isSaving.value = false
  }
}

async function deleteBlock(blockId: string) {
  try {
    await ElMessageBox.confirm('Bạn có chắc muốn xóa nội dung này?', 'Xác nhận xóa', {
      type: 'warning',
    })
    await teacherCourseApi.deleteBlock(blockId)
    blocks.value = blocks.value.filter((b) => b.id !== blockId)
    ElMessage.success('Đã xóa nội dung')
  } catch {}
}

async function onBlockDrop() {
  const ids = blocks.value.map((b) => b.id)
  try {
    await teacherCourseApi.reorderBlocks(props.lessonId, ids)
  } catch {
    ElMessage.error('Lỗi lưu thứ tự')
    fetchBlocks()
  }
}

function close() {
  emit('update:modelValue', false)
}

onMounted(() => {
  if (props.modelValue) {
    fetchBlocks()
  }
  // Establish media session for previewing content
  teacherCourseApi.getMediaCookies().catch(() => {
    console.warn('Failed to establish media session')
  })
})
</script>

<template>
  <div v-if="modelValue" class="fixed inset-0 z-50 flex justify-end">
    <!-- Backdrop -->
    <div class="absolute inset-0 bg-black/30 backdrop-blur-sm" @click="close"></div>

    <!-- Drawer Panel -->
    <div
      class="relative w-full max-w-2xl bg-white h-full shadow-2xl flex flex-col animate-in slide-in-from-right duration-300"
    >
      <!-- Header -->
      <div
        class="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50/50"
      >
        <div>
          <h3 class="font-bold text-gray-900 text-lg">Nội dung bài học</h3>
          <p class="text-sm text-slate-500 line-clamp-1">{{ lessonTitle }}</p>
        </div>
        <button
          @click="close"
          class="p-2 hover:bg-slate-100 rounded-lg text-slate-400 hover:text-slate-600 transition"
        >
          <X class="w-5 h-5" />
        </button>
      </div>

      <!-- Body -->
      <div class="flex-1 overflow-y-auto p-6 bg-slate-50">
        <!-- Block List -->
        <div v-if="isLoading">
          <div v-for="i in 3" :key="i" class="h-20 bg-white rounded-xl mb-3 animate-pulse"></div>
        </div>

        <div v-else class="space-y-4">
          <draggable
            v-model="blocks"
            group="blocks"
            item-key="id"
            handle=".block-drag"
            @end="onBlockDrop"
          >
            <template #item="{ element: block }">
              <div>
                <!-- Edit Form Mode -->
                <div
                  v-if="editingBlockId === block.id"
                  class="bg-white p-4 rounded-xl border-2 border-indigo-500 shadow-lg mb-3"
                >
                  <h4 class="font-bold text-gray-800 mb-3 flex items-center gap-2">
                    <Edit2 class="w-4 h-4 text-indigo-500" /> Sửa nội dung: {{ block.type }}
                  </h4>

                  <div class="space-y-4">
                    <!-- Title Edit -->
                    <div>
                      <label class="block text-xs font-semibold text-slate-500 uppercase mb-1"
                        >Tiêu đề</label
                      >
                      <input
                        v-model="editingBlockData.title"
                        class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      />
                    </div>

                    <!-- Rich text Edit -->
                    <div v-if="block.type === 'rich_text'">
                      <label class="block text-xs font-semibold text-slate-500 uppercase mb-1">
                        Nội dung văn bản
                      </label>
                      <textarea
                        v-model="editingBlockData.content"
                        rows="6"
                        class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                      ></textarea>
                    </div>

                    <!-- Video Link/Upload -->
                    <div v-if="block.type === 'video'">
                      <!-- Link -->
                      <div class="mb-3">
                        <label class="block text-xs font-semibold text-slate-500 uppercase mb-1"
                          >Link Youtube/Vimeo</label
                        >
                        <input
                          v-model="editingBlockData.url"
                          type="url"
                          class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm"
                          placeholder="https://..."
                        />
                      </div>

                      <!-- Upload Area -->
                      <label class="block text-xs font-semibold text-slate-500 uppercase mb-1"
                        >Hoặc Tải Video Mới</label
                      >
                      <div
                        v-if="!editingBlockData.file_id && !editingBlockData.has_existing_file"
                        class="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:bg-slate-50 relative"
                      >
                        <input
                          type="file"
                          class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                          accept="video/*"
                          @change="handleFileUpload"
                        />
                        <div v-if="isUploading">Đang tải lên...</div>
                        <div v-else>Kéo thả hoặc chọn video</div>
                      </div>
                      <div v-else class="flex items-center gap-2 p-2 bg-indigo-50 rounded">
                        <Video class="w-5 h-5 text-indigo-600" />
                        <span class="text-sm truncate flex-1">{{ editingBlockData.filename }}</span>
                        <button @click="clearEditingFile" class="text-red-500">
                          <X class="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <!-- PDF/Docx -->
                    <div v-if="['pdf', 'docx'].includes(block.type)">
                      <label class="block text-xs font-semibold text-slate-500 uppercase mb-1"
                        >File Tài Liệu</label
                      >
                      <div
                        v-if="!editingBlockData.file_id && !editingBlockData.has_existing_file"
                        class="border-2 border-dashed border-slate-300 rounded-lg p-6 text-center hover:bg-slate-50 relative"
                      >
                        <input
                          type="file"
                          class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                          accept=".pdf,.doc,.docx"
                          @change="handleFileUpload"
                        />
                        <div v-if="isUploading">Đang tải lên...</div>
                        <div v-else>Chọn file tài liệu</div>
                      </div>
                      <div v-else class="flex items-center gap-2 p-2 bg-indigo-50 rounded">
                        <FileText class="w-5 h-5 text-indigo-600" />
                        <span class="text-sm truncate flex-1">{{ editingBlockData.filename }}</span>
                        <button @click="clearEditingFile" class="text-red-500">
                          <X class="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    <!-- Buttons -->
                    <div class="flex justify-end gap-2 pt-2 border-t border-slate-100">
                      <button
                        @click="cancelEditing"
                        class="px-3 py-1.5 text-slate-500 text-sm hover:bg-slate-100 rounded"
                      >
                        Hủy
                      </button>
                      <button
                        @click="saveEditBlock"
                        :disabled="isSaving || isUploading"
                        class="px-3 py-1.5 bg-indigo-600 text-white text-sm rounded hover:bg-indigo-700 disabled:opacity-50"
                      >
                        {{ isSaving ? 'Đang lưu...' : 'Lưu cập nhật' }}
                      </button>
                    </div>
                  </div>
                </div>

                <!-- View Mode -->
                <div
                  v-else
                  class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-3 group flex items-start gap-4 hover:border-indigo-300 transition-colors"
                >
                  <div class="block-drag mt-1 cursor-grab text-slate-300 hover:text-slate-500">
                    <GripVertical class="w-5 h-5" />
                  </div>

                  <div class="p-2 bg-indigo-50 rounded-lg text-indigo-600">
                    <component :is="renderTypeIcon(block.type)" class="w-5 h-5" />
                  </div>

                  <div class="flex-1 cursor-pointer" @click="startEditing(block)">
                    <h4 class="font-bold text-gray-800">{{ block.title }}</h4>
                    <p class="text-xs text-slate-500 uppercase mt-1">
                      {{ block.type }}
                      <span v-if="block.duration" class="ml-2 bg-slate-100 px-1 rounded"
                        >{{ Math.floor(block.duration / 60) }}:{{
                          (block.duration % 60).toString().padStart(2, '0')
                        }}</span
                      >
                    </p>
                  </div>

                  <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <button
                      class="p-2 hover:bg-indigo-50 text-slate-400 hover:text-indigo-600 rounded"
                      @click="startEditing(block)"
                      title="Chỉnh sửa nội dung"
                    >
                      <Edit2 class="w-4 h-4" />
                    </button>
                    <button
                      class="p-2 hover:bg-red-50 text-slate-400 hover:text-red-500 rounded"
                      @click="deleteBlock(block.id)"
                      title="Xóa nội dung"
                    >
                      <Trash2 class="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </draggable>

          <div
            v-if="blocks.length === 0 && !showAddBlock"
            class="text-center py-10 border-2 border-dashed border-slate-200 rounded-xl"
          >
            <p class="text-slate-500">Bài học này chưa có nội dung</p>
          </div>
        </div>

        <!-- Add Block Form (Simple) -->
        <div
          v-if="showAddBlock"
          class="mt-4 bg-white p-4 rounded-xl border border-indigo-100 shadow-sm animate-in fade-in zoom-in-95"
        >
          <h4 class="font-bold text-gray-800 mb-3">Thêm nội dung: {{ selectedType }}</h4>

          <div class="space-y-3">
            <div>
              <label class="block text-xs font-semibold text-slate-500 uppercase mb-1"
                >Tiêu đề</label
              >
              <input
                v-model="newBlockTitle"
                class="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Nhập tiêu đề cho nội dung này..."
                v-focus
                @keyup.enter="saveNewBlock"
              />
            </div>

            <!-- Actions -->
            <div class="flex justify-end gap-2 mt-4">
              <button
                @click="showAddBlock = false"
                class="px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50 rounded border border-slate-200"
              >
                Hủy
              </button>

              <button
                @click="saveNewBlock"
                :disabled="isSaving"
                class="px-3 py-1.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded flex items-center gap-2 disabled:opacity-60"
              >
                <span v-if="isSaving" class="animate-spin">⌛</span>
                Tạo mới
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <div
        v-if="!showAddBlock && !showMediaOptions"
        class="p-4 bg-white border-t border-slate-200 grid grid-cols-3 gap-2"
      >
        <button
          @click="handleAddBlock('rich_text')"
          class="flex flex-col items-center gap-1 p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition"
        >
          <Type class="w-5 h-5 text-slate-600" />
          <span class="text-xs font-medium text-slate-600">Văn bản</span>
        </button>

        <button
          @click="showMediaOptions = true"
          class="flex flex-col items-center gap-1 p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition"
        >
          <Folder class="w-5 h-5 text-indigo-600" />
          <span class="text-xs font-medium text-slate-600">Tài liệu / Media</span>
        </button>

        <button
          @click="handleAddBlock('quiz')"
          class="flex flex-col items-center gap-1 p-3 rounded-lg hover:bg-slate-50 border border-slate-100 transition"
        >
          <FileCheck class="w-5 h-5 text-green-600" />
          <span class="text-xs font-medium text-slate-600">Trắc nghiệm</span>
        </button>
      </div>

      <div
        v-if="showMediaOptions && !showAddBlock"
        class="p-4 bg-slate-50 border-t border-slate-200 animate-in slide-in-from-bottom-2"
      >
        <div class="flex justify-between items-center mb-3">
          <h5 class="text-sm font-bold text-slate-700">Chọn loại tài liệu</h5>
          <button @click="showMediaOptions = false" class="text-slate-400 hover:text-slate-600">
            <X class="w-4 h-4" />
          </button>
        </div>

        <div class="grid grid-cols-3 gap-2">
          <button
            @click="handleAddBlock('video')"
            class="flex flex-col items-center gap-1 p-3 bg-white rounded-lg border border-slate-200 hover:border-indigo-300 transition"
          >
            <Youtube class="w-5 h-5 text-red-600" />
            <span class="text-xs text-slate-600">Video</span>
          </button>

          <button
            @click="handleAddBlock('pdf')"
            class="flex flex-col items-center gap-1 p-3 bg-white rounded-lg border border-slate-200 hover:border-indigo-300 transition"
          >
            <FileText class="w-5 h-5 text-orange-600" />
            <span class="text-xs text-slate-600">PDF</span>
          </button>

          <button
            @click="handleAddBlock('docx')"
            class="flex flex-col items-center gap-1 p-3 bg-white rounded-lg border border-slate-200 hover:border-indigo-300 transition"
          >
            <File class="w-5 h-5 text-blue-600" />
            <span class="text-xs text-slate-600">Word</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
