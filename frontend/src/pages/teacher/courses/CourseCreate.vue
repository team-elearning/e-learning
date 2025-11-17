<template>
  <div class="container-wrapper">
    <h1 class="page-title">Tạo khoá học mới</h1>

    <form @submit.prevent="submit" class="course-form">
      <div class="form-grid">
        <label class="form-field md:col-span-2">
          <span class="label-text">Tên khoá học <b class="text-rose-600">*</b></span>
          <input
            ref="titleRef"
            v-model.trim="f.title"
            class="input-field"
            :class="{ 'ring-2 ring-rose-500 border-rose-500': Boolean(titleErr) }"
            placeholder="Ví dụ: Toán 5 (Hỗ trợ học bộ Cánh diều)"
            aria-invalid="true"
            @input="titleErr = ''"
          />
          <p v-if="titleErr" class="error-text">{{ titleErr }}</p>
        </label>

        <label class="form-field">
          <span class="label-text">Môn học</span>
          <select v-model="f.subject" class="input-field">
            <option value="Toán">Toán</option>
            <option value="Tiếng Việt">Tiếng Việt</option>
            <option value="Tiếng Anh">Tiếng Anh</option>
            <option value="Khoa học">Khoa học</option>
            <option value="Lịch sử">Lịch sử</option>
          </select>
        </label>

        <label class="form-field">
          <span class="label-text">Khối lớp</span>
          <select v-model="f.grade" class="input-field">
            <option value="1">Lớp 1</option>
            <option value="2">Lớp 2</option>
            <option value="3">Lớp 3</option>
            <option value="4">Lớp 4</option>
            <option value="5">Lớp 5</option>
          </select>
        </label>

        <div class="form-field md:col-span-2">
          <span class="label-text"
            >Ảnh khoá học <i class="text-gray-500 font-normal">(tuỳ chọn)</i></span
          >
          <div class="file-upload-area">
            <input
              ref="fileInput"
              type="file"
              accept="image/*"
              class="hidden"
              @change="onPickCover"
            />
            <button type="button" class="btn-secondary" @click="fileInput?.click()">
              Chọn ảnh bìa
            </button>
            <span v-if="coverFile" class="file-info">
              {{ coverFile.name }} — {{ Math.round(coverFile.size / 1024) }} KB
            </span>
            <span v-else class="file-info text-gray-500">Chưa có ảnh nào được chọn</span>
          </div>
          <img v-if="coverPreview" :src="coverPreview" alt="Xem trước ảnh" class="image-preview" />
          <p class="hint-text">Hỗ trợ: JPG/PNG. Tối đa 2MB. (Không bắt buộc)</p>
          <p v-if="coverErr" class="error-text">{{ coverErr }}</p>
        </div>

        <label class="form-field md:col-span-2">
          <span class="label-text">Mô tả</span>
          <textarea
            v-model.trim="f.description"
            rows="4"
            class="input-field resize-y"
            placeholder="Mô tả chi tiết về khóa học"
          ></textarea>
        </label>

        <label class="form-field md:col-span-2">
          <span class="label-text"
            >Tags <i class="text-gray-500 font-normal">(phân cách bởi dấu phẩy)</i></span
          >
          <input
            v-model="tagsInput"
            class="input-field"
            placeholder="Ví dụ: toan, lop 5, canh dieu"
            @input="updateTags"
          />
          <p class="hint-text">Tags giúp học sinh tìm kiếm khoá học dễ dàng hơn.</p>
        </label>

        <!-- Modules -->
        <div class="form-field md:col-span-2">
          <div class="flex items-center justify-between mb-4">
            <span class="label-text">Chương học (Modules)</span>
            <button type="button" class="btn-secondary" @click="addModule">+ Thêm chương</button>
          </div>

          <div v-for="(module, moduleIndex) in f.modules" :key="moduleIndex" class="module-card">
            <div class="module-header">
              <h3 class="module-title">Chương {{ moduleIndex + 1 }}</h3>
              <button
                type="button"
                class="text-rose-600 hover:text-rose-700"
                @click="removeModule(moduleIndex)"
              >
                ✕
              </button>
            </div>

            <label class="block mb-4">
              <span class="label-text">Tên chương</span>
              <input
                v-model="module.title"
                class="input-field"
                placeholder="Ví dụ: Chương 1: Ôn tập và bổ sung về số tự nhiên"
              />
            </label>

            <div class="lessons-section">
              <div class="flex items-center justify-between mb-3">
                <span class="label-text">Bài học</span>
                <button type="button" class="btn-secondary text-sm" @click="addLesson(moduleIndex)">
                  + Thêm bài học
                </button>
              </div>

              <div
                v-for="(lesson, lessonIndex) in module.lessons"
                :key="lessonIndex"
                class="lesson-card"
              >
                <div class="lesson-header">
                  <h4 class="lesson-title">Bài {{ lessonIndex + 1 }}</h4>
                  <button
                    type="button"
                    class="text-rose-600 hover:text-rose-700"
                    @click="removeLesson(moduleIndex, lessonIndex)"
                  >
                    ✕
                  </button>
                </div>

                <div class="lesson-content">
                  <label class="block mb-3">
                    <span class="label-text">Tiêu đề bài học</span>
                    <input
                      v-model="lesson.title"
                      class="input-field"
                      placeholder="Ví dụ: Bài 1: Ôn tập về số tự nhiên"
                    />
                  </label>

                  <!-- ĐÃ BỎ 'Loại nội dung' sau tiêu đề bài học -->

                  <div class="content-blocks-section">
                    <div class="flex items-center justify-between mb-3">
                      <span class="label-text">Nội dung bài học</span>
                      <button
                        type="button"
                        class="btn-secondary text-sm"
                        @click="addContentBlock(moduleIndex, lessonIndex)"
                      >
                        + Thêm nội dung
                      </button>
                    </div>

                    <div
                      v-for="(block, blockIndex) in lesson.content_blocks"
                      :key="blockIndex"
                      class="content-block-card"
                    >
                      <div class="content-block-header">
                        <span class="font-medium">Phần {{ blockIndex + 1 }}</span>
                        <button
                          type="button"
                          class="text-rose-600 hover:text-rose-700"
                          @click="removeContentBlock(moduleIndex, lessonIndex, blockIndex)"
                        >
                          ✕
                        </button>
                      </div>

                      <div class="content-block-body">
                        <label class="block mb-3">
                          <span class="label-text">Loại nội dung</span>
                          <select
                            v-model="block.type"
                            class="input-field"
                            @change="resetBlockPayload(block)"
                          >
                            <option value="text">Văn bản</option>
                            <option value="image">Hình ảnh</option>
                            <option value="video">Video</option>
                            <option value="pdf">PDF</option>
                            <option value="docx">DOCX</option>
                            <option value="quiz">Bài kiểm tra</option>
                          </select>
                        </label>

                        <!-- TEXT -->
                        <div v-if="block.type === 'text'" class="space-y-3">
                          <label class="block">
                            <span class="label-text">Nội dung văn bản</span>
                            <textarea
                              v-model="block.payload.text"
                              rows="3"
                              class="input-field resize-y"
                              placeholder="Nhập nội dung văn bản..."
                            ></textarea>
                          </label>
                        </div>

                        <!-- IMAGE -->
                        <div v-else-if="block.type === 'image'" class="space-y-3">
                          <div class="file-upload-area">
                            <input
                              :ref="
                                (el) =>
                                  setFileInputRef(el, 'image', moduleIndex, lessonIndex, blockIndex)
                              "
                              type="file"
                              accept="image/*"
                              class="hidden"
                              @change="
                                (e) =>
                                  handleFileUpload(e, 'image', moduleIndex, lessonIndex, blockIndex)
                              "
                            />
                            <button
                              type="button"
                              class="btn-secondary"
                              @click="
                                triggerFileInput('image', moduleIndex, lessonIndex, blockIndex)
                              "
                            >
                              Chọn hình ảnh
                            </button>
                            <span v-if="block.payload.image_file" class="file-info">
                              {{ block.payload.image_file.name }} —
                              {{ Math.round(block.payload.image_file.size / 1024) }} KB
                            </span>
                            <span v-else class="file-info text-gray-500"
                              >Chưa có ảnh nào được chọn</span
                            >
                          </div>
                          <img
                            v-if="block.payload.image_preview"
                            :src="block.payload.image_preview"
                            alt="Xem trước ảnh"
                            class="image-preview-small"
                          />
                          <label class="block">
                            <span class="label-text">Chú thích</span>
                            <input
                              v-model="block.payload.caption"
                              class="input-field"
                              placeholder="Hình ảnh minh họa"
                            />
                          </label>
                          <p class="hint-text">Hỗ trợ: JPG/PNG. Tối đa 5MB.</p>
                        </div>

                        <!-- VIDEO -->
                        <div v-else-if="block.type === 'video'" class="space-y-3">
                          <div class="file-upload-area">
                            <input
                              :ref="
                                (el) =>
                                  setFileInputRef(el, 'video', moduleIndex, lessonIndex, blockIndex)
                              "
                              type="file"
                              accept="video/*"
                              class="hidden"
                              @change="
                                (e) =>
                                  handleFileUpload(e, 'video', moduleIndex, lessonIndex, blockIndex)
                              "
                            />
                            <button
                              type="button"
                              class="btn-secondary"
                              @click="
                                triggerFileInput('video', moduleIndex, lessonIndex, blockIndex)
                              "
                            >
                              Chọn video
                            </button>
                            <span v-if="block.payload.video_file" class="file-info">
                              {{ block.payload.video_file.name }} —
                              {{ (block.payload.video_file.size / 1024 / 1024).toFixed(1) }} MB
                            </span>
                            <span v-else class="file-info text-gray-500"
                              >Chưa có video nào được chọn</span
                            >
                          </div>
                          <video
                            v-if="block.payload.video_preview"
                            :src="block.payload.video_preview"
                            controls
                            class="video-preview-small"
                          ></video>
                          <p class="hint-text">Hỗ trợ: MP4, WebM, MOV. Tối đa 200MB.</p>

                          <div v-if="block.payload.uploading" class="text-sm text-gray-600">
                            Đang upload video... {{ block.payload.progress || 0 }}%
                          </div>
                        </div>

                        <!-- PDF / DOCX -->
                        <div v-else-if="['pdf', 'docx'].includes(block.type)" class="space-y-3">
                          <div class="file-upload-area">
                            <input
                              :ref="
                                (el) =>
                                  setFileInputRef(el, 'file', moduleIndex, lessonIndex, blockIndex)
                              "
                              type="file"
                              :accept="block.type === 'pdf' ? '.pdf' : '.docx,.doc'"
                              class="hidden"
                              @change="
                                (e) =>
                                  handleFileUpload(e, 'file', moduleIndex, lessonIndex, blockIndex)
                              "
                            />
                            <button
                              type="button"
                              class="btn-secondary"
                              @click="
                                triggerFileInput('file', moduleIndex, lessonIndex, blockIndex)
                              "
                            >
                              Chọn file {{ block.type.toUpperCase() }}
                            </button>
                            <span v-if="block.payload.file" class="file-info">
                              {{ block.payload.file.name }} —
                              {{ Math.round(block.payload.file.size / 1024) }} KB
                            </span>
                            <span v-else class="file-info text-gray-500"
                              >Chưa có file nào được chọn</span
                            >
                          </div>
                          <label v-if="block.type === 'pdf'" class="block">
                            <span class="label-text">Tên file (tuỳ chọn)</span>
                            <input
                              v-model="block.payload.filename"
                              class="input-field"
                              placeholder="Tóm tắt lý thuyết.pdf"
                            />
                          </label>
                          <p class="hint-text">
                            {{
                              block.type === 'pdf'
                                ? 'Hỗ trợ: PDF. Tối đa 10MB.'
                                : 'Hỗ trợ: DOCX, DOC. Tối đa 5MB.'
                            }}
                          </p>
                        </div>

                        <!-- QUIZ -->
                        <div v-else-if="block.type === 'quiz'" class="space-y-4">
                          <label class="block">
                            <span class="label-text">Tiêu đề bài kiểm tra</span>
                            <input
                              v-model="block.payload.title"
                              class="input-field"
                              placeholder="Bài tập tổng hợp Chương 2: Số thập phân"
                            />
                          </label>

                          <label class="block">
                            <span class="label-text">Thời gian làm bài</span>
                            <input
                              v-model="block.payload.time_limit"
                              class="input-field"
                              placeholder="00:45:00"
                            />
                          </label>

                          <div class="questions-section">
                            <div class="flex items-center justify-between mb-3">
                              <span class="label-text">Câu hỏi</span>
                              <button
                                type="button"
                                class="btn-secondary text-sm"
                                @click="addQuestion(block)"
                              >
                                + Thêm câu hỏi
                              </button>
                            </div>

                            <div
                              v-for="(question, questionIndex) in block.payload.questions"
                              :key="questionIndex"
                              class="question-card"
                            >
                              <div class="question-header">
                                <span class="font-medium">Câu {{ questionIndex + 1 }}</span>
                                <button
                                  type="button"
                                  class="text-rose-600 hover:text-rose-700"
                                  @click="removeQuestion(block, questionIndex)"
                                >
                                  ✕
                                </button>
                              </div>

                              <div class="question-body space-y-3">
                                <label class="block">
                                  <span class="label-text">Loại câu hỏi</span>
                                  <select
                                    v-model="question.type"
                                    class="input-field"
                                    @change="resetQuestionPayload(question, block, questionIndex)"
                                  >
                                    <option value="multiple_choice_single">Chọn một đáp án</option>
                                    <option value="multiple_choice_multi">Chọn nhiều đáp án</option>
                                    <option value="true_false">Đúng/Sai</option>
                                    <option value="fill_in_the_blank">Điền vào chỗ trống</option>
                                  </select>
                                </label>

                                <label class="block">
                                  <span class="label-text">Nội dung câu hỏi</span>
                                  <textarea
                                    v-model="question.prompt.text"
                                    rows="2"
                                    class="input-field resize-y"
                                    placeholder="Nhập nội dung câu hỏi..."
                                  ></textarea>
                                </label>

                                <!-- Multiple choice (single) -->
                                <div
                                  v-if="question.type === 'multiple_choice_single'"
                                  class="space-y-2"
                                >
                                  <span class="label-text">Lựa chọn</span>
                                  <div
                                    v-for="(choice, choiceIndex) in question.answer_payload.choices"
                                    :key="choiceIndex"
                                    class="choice-item"
                                  >
                                    <div class="flex items-center gap-2">
                                      <input
                                        v-model="choice.id"
                                        class="input-field w-12"
                                        placeholder="ID"
                                      />
                                      <input
                                        v-model="choice.text"
                                        class="input-field flex-1"
                                        placeholder="Nội dung lựa chọn"
                                      />
                                      <label class="flex items-center gap-1">
                                        <input
                                          type="radio"
                                          :name="`question-${moduleIndex}-${lessonIndex}-${blockIndex}-${questionIndex}-correct`"
                                          :value="choiceIndex"
                                          v-model="
                                            selectedCorrectChoice[
                                              getQuestionKey(block, questionIndex)
                                            ]
                                          "
                                          @change="setCorrectChoice(question, choiceIndex)"
                                        />
                                        <span class="text-sm">Đúng</span>
                                      </label>
                                      <button
                                        type="button"
                                        class="text-rose-600"
                                        @click="removeChoice(question, choiceIndex)"
                                      >
                                        ✕
                                      </button>
                                    </div>
                                  </div>
                                  <button
                                    type="button"
                                    class="btn-secondary text-sm"
                                    @click="addChoice(question)"
                                  >
                                    + Thêm lựa chọn
                                  </button>
                                </div>

                                <!-- True/False -->
                                <div v-else-if="question.type === 'true_false'" class="space-y-2">
                                  <label class="flex items-center gap-2">
                                    <input
                                      type="radio"
                                      :name="`question-${moduleIndex}-${lessonIndex}-${blockIndex}-${questionIndex}-tf`"
                                      :value="true"
                                      v-model="question.answer_payload.answer"
                                    />
                                    <span>Đúng</span>
                                  </label>
                                  <label class="flex items-center gap-2">
                                    <input
                                      type="radio"
                                      :name="`question-${moduleIndex}-${lessonIndex}-${blockIndex}-${questionIndex}-tf`"
                                      :value="false"
                                      v-model="question.answer_payload.answer"
                                    />
                                    <span>Sai</span>
                                  </label>
                                </div>

                                <label class="block">
                                  <span class="label-text">Gợi ý (tuỳ chọn)</span>
                                  <input
                                    v-model="question.hint.text"
                                    class="input-field"
                                    placeholder="Gợi ý cho học sinh..."
                                  />
                                </label>
                              </div>
                            </div>
                          </div>
                        </div>
                        <!-- END QUIZ -->
                      </div>
                    </div>
                  </div>
                </div>
              </div>
              <!-- END LESSON -->
            </div>
          </div>
        </div>
      </div>

      <div class="form-actions">
        <button type="button" class="btn-cancel" @click="router.back()">Huỷ</button>
        <button class="btn-primary" :class="{ 'opacity-60 pointer-events-none': submitting }">
          {{ submitting ? 'Đang tạo…' : 'Tạo khoá học' }}
        </button>
      </div>
    </form>

    <!-- Notification modal -->
    <transition
      enter-active-class="transition-opacity duration-150 ease-out"
      leave-active-class="transition-opacity duration-150 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="notificationModal.open"
        class="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4"
        role="dialog"
        aria-modal="true"
        @click.self="notificationModal.open = false"
      >
        <div
          class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl outline-none"
        >
          <div class="mb-4 flex items-center gap-3">
            <div
              :class="[
                'p-2 rounded-full',
                notificationModal.type === 'success'
                  ? 'bg-green-100 text-green-600'
                  : 'bg-amber-100 text-amber-600',
              ]"
            >
              <span v-if="notificationModal.type === 'success'">✓</span>
              <span v-else>⚠</span>
            </div>
            <h3 class="text-lg font-bold text-slate-800">{{ notificationModal.title }}</h3>
          </div>

          <div class="mb-6">
            <p class="text-slate-700">{{ notificationModal.message }}</p>
          </div>

          <div class="flex justify-end">
            <button type="button" class="btn-primary" @click="notificationModal.open = false">
              OK
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// ================== AUTH HEADER ==================
const getAuthHeaders = () => {
  const token = localStorage.getItem('access')
  return token
    ? {
        Authorization: `Bearer ${token}`,
      }
    : {}
}

// Helper để tạo key duy nhất cho mỗi câu hỏi
const getQuestionKey = (block: any, questionIndex: number) =>
  `${block.type}-${questionIndex}-${Date.now()}`

const selectedCorrectChoice = ref<Record<string, number>>({})

// Refs cho file inputs nội dung (image/video/pdf/docx)
const fileInputRefs = ref<Record<string, HTMLInputElement>>({})

/** Form chính */
const f = reactive({
  title: '',
  subject: 'Toán',
  grade: '5',
  description: '',
  tags: [] as string[],
  published: true,
  modules: [] as Array<{
    title: string
    position: number
    lessons: Array<{
      title: string
      position: number
      content_type: string
      published?: boolean
      content_blocks: Array<{
        type: string
        position: number
        payload: any
      }>
    }>
  }>,
})

// Modal thông báo
const notificationModal = reactive({
  open: false,
  type: 'success' as 'success' | 'error',
  title: '',
  message: '',
})

// ========== TAGS ==========
const tagsInput = ref('')
const updateTags = () => {
  f.tags = tagsInput.value
    .split(',')
    .map((tag) => tag.trim())
    .filter((tag) => tag.length > 0)
}

// ========== MEDIA UPLOAD ==========
type MediaComponent = 'lesson_material' | 'course_thumbnail'

interface UploadMediaResponse {
  id: string
  original_filename: string
  uploaded_at: string
  status: string
  component: string
  url: string
}

/** Upload 1 file lên /api/media/upload/ */
async function uploadMedia(
  file: File,
  component: MediaComponent = 'lesson_material',
  contentTypeStr: string,
  onUploadProgress?: (percent: number) => void,
): Promise<UploadMediaResponse> {
  const formData = new FormData()
  formData.append('file', file)
  formData.append('component', component)
  formData.append('content_type_str', contentTypeStr)

  const { data } = await axios.post<UploadMediaResponse>('/api/media/upload/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
      ...getAuthHeaders(),
    },
    onUploadProgress: (e) => {
      if (!e.total || !onUploadProgress) return
      const percent = Math.round((e.loaded * 100) / e.total)
      onUploadProgress(percent)
    },
  })

  return data
}

// ========== KHÔNG CẦN uploadAllFiles NỮA ==========
/* ---------- Log payload thực tế + chuẩn bị data gửi API ---------- */
const logActualPayload = async () => {
  try {
    const actualPayload = {
      title: f.title,
      image_id: coverImageId.value,
      description: f.description,
      categories: [f.subject],
      tags: f.tags,
      grade: f.grade,
      published: f.published,
      modules: f.modules,
    }

    console.log('🎯 PAYLOAD THỰC TẾ SẼ GỬI:')
    console.log('=========================================')
    console.log(JSON.stringify(actualPayload, null, 2))
    console.log('=========================================')
    console.log('📊 THÔNG TIN PAYLOAD:')
    console.log(`- Tổng số modules: ${actualPayload.modules.length}`)
    console.log(
      `- Tổng số lessons: ${actualPayload.modules.reduce(
        (acc, module) => acc + module.lessons.length,
        0,
      )}`,
    )
    console.log(
      `- Tổng số content blocks: ${actualPayload.modules.reduce(
        (acc, module) =>
          acc + module.lessons.reduce((acc2, lesson) => acc2 + lesson.content_blocks.length, 0),
        0,
      )}`,
    )

    return actualPayload
  } catch (error) {
    console.error('❌ Lỗi khi tạo payload:', error)
    showNotification('error', 'Lỗi', 'Không thể tạo payload để xem')
    throw error
  }
}

/* ---------- File input refs cho content blocks ---------- */
const setFileInputRef = (
  el: any,
  type: string,
  moduleIndex: number,
  lessonIndex: number,
  blockIndex: number,
) => {
  if (el) {
    const key = `${type}-${moduleIndex}-${lessonIndex}-${blockIndex}`
    fileInputRefs.value[key] = el
  }
}

const triggerFileInput = (
  type: string,
  moduleIndex: number,
  lessonIndex: number,
  blockIndex: number,
) => {
  const key = `${type}-${moduleIndex}-${lessonIndex}-${blockIndex}`
  fileInputRefs.value[key]?.click()
}

const MAX_IMAGE_SIZE = 5 * 1024 * 1024
const MAX_VIDEO_SIZE = 200 * 1024 * 1024
const MAX_FILE_SIZE = 10 * 1024 * 1024

// UPLOAD NGAY KHI CHỌN FILE
const handleFileUpload = async (
  event: Event,
  fileType: 'image' | 'video' | 'file',
  moduleIndex: number,
  lessonIndex: number,
  blockIndex: number,
) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  const block = f.modules[moduleIndex].lessons[lessonIndex].content_blocks[blockIndex]

  if (!file) return

  // Giới hạn dung lượng
  const maxSizes: Record<string, number> = {
    image: MAX_IMAGE_SIZE, // 5MB
    video: MAX_VIDEO_SIZE, // 200MB
    file: MAX_FILE_SIZE, // 10MB
  }

  if (file.size > maxSizes[fileType]) {
    showNotification(
      'error',
      'Lỗi',
      `File vượt quá dung lượng cho phép (${maxSizes[fileType] / 1024 / 1024}MB)`,
    )
    input.value = ''
    return
  }

  // Preview/local state trước cho user thấy
  if (fileType === 'image') {
    block.payload.image_file = file
    if (block.payload.image_preview) URL.revokeObjectURL(block.payload.image_preview)
    block.payload.image_preview = URL.createObjectURL(file)
  } else if (fileType === 'video') {
    block.payload.video_file = file
    if (block.payload.video_preview) URL.revokeObjectURL(block.payload.video_preview)
    block.payload.video_preview = URL.createObjectURL(file)
  } else if (fileType === 'file') {
    block.payload.file = file
  }

  // Map sang content_type_str cho BE
  // fileType = 'file' => dùng block.type: 'pdf' | 'docx'
  const contentTypeStr =
    fileType === 'file'
      ? block.type // pdf / docx
      : fileType // image / video

  try {
    // đánh dấu đang upload để UI hiển thị
    block.payload.uploading = true
    block.payload.progress = 0

    const res = await uploadMedia(file, 'lesson_material', contentTypeStr, (percent: number) => {
      // callback progress từ axios.onUploadProgress
      block.payload.progress = percent
    })

    // Gán id/url vào payload tuỳ loại
    if (fileType === 'image') {
      block.payload.image_id = res.id
      block.payload.image_url = res.url
      delete block.payload.image_file
    } else if (fileType === 'video') {
      block.payload.video_id = res.id
      block.payload.video_url = res.url
      delete block.payload.video_file
    } else if (fileType === 'file') {
      block.payload.file_id = res.id
      block.payload.file_url = res.url
      if (!block.payload.filename) {
        block.payload.filename = file.name
      }
      delete block.payload.file
    }

    block.payload.uploading = false
    showNotification('success', 'Thành công', 'Upload file thành công')
  } catch (error) {
    console.error('❌ Lỗi upload file:', error)
    block.payload.uploading = false
    showNotification('error', 'Lỗi', 'Upload file thất bại, vui lòng thử lại')
  }
}

/* ---------- Module/Lesson/Block management ---------- */
const addModule = () => {
  f.modules.push({
    title: '',
    position: f.modules.length,
    lessons: [],
  })
}

const removeModule = (index: number) => {
  f.modules.splice(index, 1)
  f.modules.forEach((module, i) => {
    module.position = i
  })
}

const addLesson = (moduleIndex: number) => {
  f.modules[moduleIndex].lessons.push({
    title: '',
    position: f.modules[moduleIndex].lessons.length,
    content_type: 'lesson',
    content_blocks: [],
  })
}

const removeLesson = (moduleIndex: number, lessonIndex: number) => {
  f.modules[moduleIndex].lessons.splice(lessonIndex, 1)
  f.modules[moduleIndex].lessons.forEach((lesson, i) => {
    lesson.position = i
  })
}

const addContentBlock = (moduleIndex: number, lessonIndex: number) => {
  f.modules[moduleIndex].lessons[lessonIndex].content_blocks.push({
    type: 'text',
    position: f.modules[moduleIndex].lessons[lessonIndex].content_blocks.length,
    payload: { text: '' },
  })
}

const removeContentBlock = (moduleIndex: number, lessonIndex: number, blockIndex: number) => {
  const block = f.modules[moduleIndex].lessons[lessonIndex].content_blocks[blockIndex]
  if (block.payload.image_preview) URL.revokeObjectURL(block.payload.image_preview)
  if (block.payload.video_preview) URL.revokeObjectURL(block.payload.video_preview)

  f.modules[moduleIndex].lessons[lessonIndex].content_blocks.splice(blockIndex, 1)
  f.modules[moduleIndex].lessons[lessonIndex].content_blocks.forEach((b, i) => {
    b.position = i
  })
}

const resetBlockPayload = (block: any) => {
  const payloadTemplates: Record<string, any> = {
    text: { text: '' },
    image: { image_preview: '', caption: '', image_id: null },
    video: { video_preview: '', video_id: null, uploading: false, progress: 0 },
    pdf: { filename: '', file_id: null, uploading: false, progress: 0 },
    docx: { file_id: null, uploading: false, progress: 0 },
    quiz: {
      title: '',
      time_limit: '00:45:00',
      time_open: null,
      time_close: null,
      questions: [],
    },
  }
  block.payload = payloadTemplates[block.type] || {}
}

/* ---------- Question Management ---------- */
const getBaseAnswerPayload = (type: string) => {
  switch (type) {
    case 'multiple_choice_single':
    case 'multiple_choice_multi':
      return { choices: [] }
    case 'true_false':
      return { answer: true }
    case 'fill_in_the_blank':
      return { blanks: [{ id: 'BLANK_1', answer: '' }] }
    default:
      return {}
  }
}

const resetQuestionPayload = (question: any, block: any, questionIndex: number) => {
  question.answer_payload = getBaseAnswerPayload(question.type)

  if (question.type !== 'multiple_choice_single') {
    const key = getQuestionKey(block, questionIndex)
    delete selectedCorrectChoice.value[key]
  }
}

const addQuestion = (block: any) => {
  if (!block.payload.questions) {
    block.payload.questions = []
  }
  const newQuestion = {
    position: block.payload.questions.length,
    type: 'multiple_choice_single',
    prompt: { text: '' },
    answer_payload: getBaseAnswerPayload('multiple_choice_single'),
    hint: { text: '' },
  }
  block.payload.questions.push(newQuestion)
}

const removeQuestion = (block: any, questionIndex: number) => {
  block.payload.questions.splice(questionIndex, 1)
  block.payload.questions.forEach((q: any, i: number) => {
    q.position = i
  })
}

const addChoice = (question: any) => {
  if (!question.answer_payload.choices) {
    question.answer_payload.choices = []
  }
  const choiceId = String.fromCharCode(97 + question.answer_payload.choices.length) // a, b, c, ...
  question.answer_payload.choices.push({
    id: choiceId,
    text: '',
    is_correct: false,
  })
}

const removeChoice = (question: any, choiceIndex: number) => {
  question.answer_payload.choices.splice(choiceIndex, 1)
}

const setCorrectChoice = (question: any, choiceIndex: number) => {
  question.answer_payload.choices.forEach((choice: any, index: number) => {
    choice.is_correct = index === choiceIndex
  })
}

/* ---------- Notification ---------- */
const showNotification = (type: 'success' | 'error', title: string, message: string) => {
  notificationModal.type = type
  notificationModal.title = title
  notificationModal.message = message
  notificationModal.open = true
}

/* ---------- Cover image ---------- */
const titleRef = ref<HTMLInputElement | null>(null)
const titleErr = ref('')
const fileInput = ref<HTMLInputElement | null>(null)
const coverFile = ref<File | null>(null)
const coverPreview = ref<string>('')
const coverErr = ref('')
const coverImageId = ref<string | null>(null)
const MAX_AVATAR_SIZE = 2 * 1024 * 1024
const OVER_LIMIT_MSG = 'File ảnh vượt quá dung lượng cho phép (2MB)'
const submitting = ref(false)

const onPickCover = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > MAX_AVATAR_SIZE) {
    coverErr.value = OVER_LIMIT_MSG
    coverFile.value = null
    if (coverPreview.value) URL.revokeObjectURL(coverPreview.value)
    coverPreview.value = ''
    return
  }

  coverErr.value = ''
  coverFile.value = file
  if (coverPreview.value) URL.revokeObjectURL(coverPreview.value)
  coverPreview.value = URL.createObjectURL(file)

  try {
    const res = await uploadMedia(file, 'course_thumbnail', 'image')
    coverImageId.value = res.id
  } catch (err) {
    console.error('❌ Lỗi upload ảnh bìa:', err)
    showNotification('error', 'Lỗi', 'Upload ảnh bìa thất bại')
    coverImageId.value = null
  }
}

/* ---------- Submit: gọi API tạo khoá học ---------- */
async function submit() {
  titleErr.value = ''
  if (!f.title || !f.title.trim()) {
    titleErr.value = 'Vui lòng nhập tên khoá học.'
    titleRef.value?.focus()
    titleRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }

  // 🚫 Không cho submit nếu còn file đang upload
  const hasUploading = f.modules.some((module) =>
    module.lessons.some((lesson) =>
      lesson.content_blocks.some((block) => block.payload && block.payload.uploading === true),
    ),
  )

  if (hasUploading) {
    showNotification(
      'error',
      'Đang upload file',
      'Vui lòng chờ upload file hoàn tất rồi hãy lưu khoá học.',
    )
    return
  }

  submitting.value = true
  try {
    const actualPayload = await logActualPayload()

    console.log('🚀 GỬI PAYLOAD ĐẾN SERVER...')

    await axios.post('/api/content/instructor/courses/', actualPayload, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    })

    showNotification('success', 'Thành công', 'Đã tạo khoá học thành công!')

    setTimeout(() => {
      router.push({ path: '/teacher/courses' })
    }, 2000)
  } catch (e: any) {
    console.error('❌ Lỗi khi tạo khóa học:', e)
    showNotification('error', 'Lỗi', e?.message || 'Có lỗi xảy ra. Vui lòng thử lại.')
  } finally {
    submitting.value = false
  }
}

/* ---------- Clean up object URLs ---------- */
onBeforeUnmount(() => {
  if (coverPreview.value) URL.revokeObjectURL(coverPreview.value)

  f.modules.forEach((module) => {
    module.lessons.forEach((lesson) => {
      lesson.content_blocks.forEach((block) => {
        if (block.payload.image_preview) URL.revokeObjectURL(block.payload.image_preview)
        if (block.payload.video_preview) URL.revokeObjectURL(block.payload.video_preview)
      })
    })
  })
})
</script>

<style scoped>
.container-wrapper {
  @apply mx-auto max-w-6xl p-6 lg:p-8;
}
.page-title {
  @apply mb-6 text-3xl font-extrabold text-gray-800 text-center;
}
.course-form {
  @apply space-y-8 rounded-2xl bg-white p-8 shadow-xl border border-gray-100;
}
.form-grid {
  @apply grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-2;
}
.form-field {
  @apply block;
}
.label-text {
  @apply mb-2 block text-sm font-semibold text-gray-700;
}
.input-field {
  @apply w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-800 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition duration-200 ease-in-out;
}
textarea.input-field {
  @apply resize-y;
}
.file-upload-area {
  @apply flex flex-wrap items-center gap-4;
}
.btn-secondary {
  @apply rounded-lg border border-gray-300 px-5 py-2.5 font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200 ease-in-out;
}
.file-info {
  @apply text-sm text-gray-600;
}
.image-preview {
  @apply mt-4 w-full h-48 rounded-lg object-cover shadow-md;
}
.image-preview-small {
  @apply mt-2 w-full max-w-xs h-32 rounded-lg object-cover shadow-md;
}
.video-preview-small {
  @apply mt-2 w-full max-w-md rounded-lg object-cover shadow-md max-h-48;
}
.hint-text {
  @apply mt-2 text-xs text-gray-500;
}
.error-text {
  @apply mt-2 text-sm text-rose-600 font-medium;
}
.form-actions {
  @apply flex justify-end gap-4 pt-6 border-t border-gray-100 mt-8;
}
.btn-primary {
  @apply rounded-xl bg-blue-600 px-6 py-3 font-bold text-white shadow-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 ease-in-out;
}
.btn-cancel {
  @apply rounded-xl border border-gray-300 bg-white px-6 py-3 font-semibold text-gray-700 shadow-sm hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2 transition duration-200 ease-in-out;
}
.module-card {
  @apply mb-6 p-4 border border-gray-200 rounded-lg bg-gray-50;
}
.module-header {
  @apply flex items-center justify-between mb-4 pb-2 border-b border-gray-200;
}
.module-title {
  @apply text-lg font-semibold text-gray-800;
}
.lessons-section {
  @apply mt-4;
}
.lesson-card {
  @apply mb-4 p-4 border border-gray-200 rounded-lg bg-white;
}
.lesson-header {
  @apply flex items-center justify-between mb-3 pb-2 border-b border-gray-200;
}
.lesson-title {
  @apply font-medium text-gray-800;
}
.lesson-content {
  @apply space-y-4;
}
.content-blocks-section {
  @apply mt-4;
}
.content-block-card {
  @apply mb-3 p-3 border border-gray-200 rounded-lg bg-gray-50;
}
.content-block-header {
  @apply flex items-center justify-between mb-3 pb-2 border-b border-gray-200;
}
.content-block-body {
  @apply space-y-3;
}
.questions-section {
  @apply mt-4;
}
.question-card {
  @apply mb-3 p-3 border border-gray-200 rounded-lg bg-white;
}
.question-header {
  @apply flex items-center justify-between mb-3 pb-2 border-b border-gray-200;
}
.question-body {
  @apply space-y-3;
}
.choice-item {
  @apply space-y-2;
}
.hidden {
  display: none;
}
.action-buttons {
  @apply flex justify-center gap-4 mb-6;
}
.btn-preview {
  @apply rounded-xl bg-purple-600 px-6 py-3 font-bold text-white shadow-lg hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 transition duration-200 ease-in-out;
}
</style>
