<template>
  <div class="container-wrapper">
    <h1 class="page-title">Tạo khoá học mới</h1>

    <!-- STEP HEADER / PROGRESS -->
    <div class="mb-6 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
      <div class="flex items-center gap-3">
        <template v-for="step in steps" :key="step.id">
          <div class="flex items-center gap-2">
            <div
              class="flex h-9 w-9 items-center justify-center rounded-full border text-sm font-semibold"
              :class="{
                'bg-blue-600 text-white border-blue-600': currentStep === step.id,
                'bg-blue-50 text-blue-600 border-blue-400': currentStep > step.id,
                'bg-gray-100 text-gray-500 border-gray-300': currentStep < step.id,
              }"
            >
              {{ step.id }}
            </div>
            <div class="hidden flex-col text-sm md:flex">
              <span
                class="font-semibold"
                :class="currentStep === step.id ? 'text-gray-900' : 'text-gray-500'"
              >
                {{ step.label }}
              </span>
              <span class="text-xs text-gray-400">{{ step.subLabel }}</span>
            </div>
          </div>

          <div
            v-if="step.id < steps.length"
            class="hidden h-px flex-1 bg-gradient-to-r from-gray-200 via-gray-300 to-gray-200 md:block"
          />
        </template>
      </div>

      <div class="text-xs text-gray-500 md:text-sm">
        Bước {{ currentStep }} / {{ steps.length }}
      </div>
    </div>

    <!-- FORM WRAPPER -->
    <div class="course-form space-y-8">
      <!-- STEP 1: BASIC INFO -->
      <section v-if="currentStep === 1" class="space-y-6">
        <h2 class="text-lg font-bold text-gray-800 mb-2">Bước 1: Thông tin cơ bản</h2>

        <div class="form-grid">
          <!-- Title -->
          <label class="form-field md:col-span-2">
            <span class="label-text"> Tên khoá học <b class="text-rose-600">*</b> </span>
            <input
              ref="titleRef"
              v-model.trim="form.title"
              class="input-field"
              :class="{ 'ring-2 ring-rose-500 border-rose-500': Boolean(titleErr) }"
              placeholder="Ví dụ: Toán 5 (Hỗ trợ học bộ Cánh diều)"
              @input="titleErr = ''"
            />
            <p v-if="titleErr" class="error-text">{{ titleErr }}</p>
          </label>

          <!-- Subject -->
          <label class="form-field">
            <span class="label-text">Môn học</span>
            <select v-model="form.subject" class="input-field">
              <option value="">-- Chọn môn --</option>
              <option value="Toán">Toán</option>
              <option value="Tiếng Việt">Tiếng Việt</option>
              <option value="Tiếng Anh">Tiếng Anh</option>
              <option value="Khoa học">Khoa học</option>
              <option value="Lịch sử">Lịch sử</option>
            </select>
          </label>
          <p v-if="subjectErr" class="error-text">{{ subjectErr }}</p>

          <!-- Grade -->
          <label class="form-field">
            <span class="label-text">Khối lớp</span>
            <select v-model="form.grade" class="input-field">
              <option value="">-- Chọn khối --</option>
              <option value="1">Lớp 1</option>
              <option value="2">Lớp 2</option>
              <option value="3">Lớp 3</option>
              <option value="4">Lớp 4</option>
              <option value="5">Lớp 5</option>
            </select>
          </label>
          <p v-if="gradeErr" class="error-text">{{ gradeErr }}</p>

          <!-- Description -->
          <label class="form-field md:col-span-2">
            <span class="label-text">Mô tả khoá học</span>
            <textarea
              v-model.trim="form.description"
              rows="4"
              class="input-field resize-y"
              placeholder="Mô tả ngắn gọn về khoá học, đối tượng, mục tiêu..."
            ></textarea>
          </label>

          <!-- Tags -->
          <label class="form-field md:col-span-2">
            <span class="label-text">
              Tags
              <i class="text-gray-500 font-normal">(phân cách bởi dấu phẩy)</i>
            </span>
            <input
              v-model="tagsInput"
              class="input-field"
              placeholder="Ví dụ: toan, lop 5, canh dieu"
              @input="updateTags"
            />
            <p class="hint-text">Tags giúp học sinh tìm kiếm khoá học dễ dàng hơn.</p>
          </label>

          <!-- Categories -->
          <label class="form-field md:col-span-2">
            <span class="label-text">
              Danh mục
              <i class="text-gray-500 font-normal">(phân cách bởi dấu phẩy)</i>
            </span>
            <input
              v-model="categoriesInput"
              class="input-field"
              placeholder="Ví dụ: toán tiểu học, luyện thi, cánh diều"
              @input="updateCategories"
            />
            <p class="hint-text">Có thể dùng để nhóm các khoá học cùng chủ đề.</p>
          </label>

          <!-- Price + Published -->
          <label class="form-field">
            <span class="label-text">Giá khoá học (VNĐ)</span>
            <input
              v-model.number="form.price"
              type="number"
              min="0"
              class="input-field"
              placeholder="Ví dụ: 199000"
            />
            <p class="hint-text">Để 0 nếu là khoá miễn phí.</p>
          </label>

          <div class="form-field">
            <span class="label-text">Trạng thái xuất bản</span>
            <label class="inline-flex items-center gap-2 text-sm text-gray-700">
              <input v-model="form.published" type="checkbox" class="rounded" />
              <span>Xuất bản ngay sau khi tạo</span>
            </label>
            <p class="hint-text">Nên để <b>tắt</b> để soạn nội dung trước khi công khai.</p>
          </div>
        </div>
      </section>

      <!-- STEP 2: THUMBNAIL UPLOAD -->
      <section v-else-if="currentStep === 2" class="space-y-6">
        <h2 class="text-lg font-bold text-gray-800 mb-2">Bước 2: Ảnh bìa khóa học</h2>

        <div class="space-y-4">
          <div class="form-field md:col-span-2">
            <span class="label-text">
              Ảnh khoá học
              <i class="text-gray-500 font-normal">(tùy chọn nhưng nên có)</i>
            </span>

            <div class="file-upload-area">
              <input
                ref="thumbnailInput"
                type="file"
                accept="image/*"
                class="hidden"
                @change="onPickThumbnail"
              />

              <button type="button" class="btn-secondary" @click="thumbnailInput?.click()">
                Chọn ảnh bìa
              </button>

              <span v-if="thumbnail.file" class="file-info">
                {{ thumbnail.file.name }} — {{ Math.round(thumbnail.file.size / 1024) }} KB
              </span>
              <span v-else class="file-info text-gray-500"> Chưa có ảnh nào được chọn </span>
            </div>

            <img
              v-if="thumbnail.previewUrl"
              :src="thumbnail.previewUrl"
              alt="Xem trước ảnh"
              class="image-preview"
            />

            <p class="hint-text">
              Hỗ trợ: JPG/PNG. Tối đa 2MB. Ảnh sẽ được upload trực tiếp lên S3.
            </p>
            <p v-if="thumbnail.error" class="error-text">{{ thumbnail.error }}</p>

            <div class="mt-3 flex items-center gap-3">
              <span v-if="thumbnail.uploading" class="text-sm text-gray-600">
                Đang upload: {{ thumbnail.progress }}%
              </span>

              <span
                v-else-if="thumbnail.uploaded && form.image_id"
                class="text-sm text-emerald-600 font-medium"
              >
                ✓ Ảnh đã upload thành công.
              </span>
            </div>
          </div>
        </div>
      </section>

      <!-- STEP 3: CURRICULUM (Phiên bản nhẹ, giữ style cũ) -->

      <!-- STEP 4: REVIEW & SUBMIT -->
      <!-- STEP 3: REVIEW & SUBMIT -->
      <section v-else-if="currentStep === 3" class="space-y-6">
        <h2 class="text-lg font-bold text-gray-800 mb-2">Bước 3: Xem lại & Tạo khoá học</h2>

        <div class="grid gap-4 md:grid-cols-2">
          <!-- Thông tin chung -->
          <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-2">
            <h3 class="font-semibold text-gray-800 mb-2">Thông tin cơ bản</h3>
            <p><span class="font-medium">Tên:</span> {{ form.title || '—' }}</p>
            <p><span class="font-medium">Môn:</span> {{ form.subject || '—' }}</p>
            <p><span class="font-medium">Khối:</span> {{ form.grade || '—' }}</p>
            <p>
              <span class="font-medium">Giá:</span>
              {{ form.price ? form.price.toLocaleString('vi-VN') + 'đ' : 'Miễn phí' }}
            </p>
            <p>
              <span class="font-medium">Xuất bản:</span>
              <span v-if="form.published">Có</span>
              <span v-else>Không</span>
            </p>
          </div>

          <!-- Ảnh + Tags -->
          <div class="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3">
            <h3 class="font-semibold text-gray-800 mb-2">Ảnh & Phân loại</h3>

            <div class="flex gap-3 items-start">
              <div class="w-28 h-20 rounded-lg bg-gray-100 overflow-hidden">
                <img
                  v-if="thumbnail.previewUrl"
                  :src="thumbnail.previewUrl"
                  class="w-full h-full object-cover"
                />
                <div
                  v-else
                  class="w-full h-full flex items-center justify-center text-2xl text-gray-300"
                >
                  🎓
                </div>
              </div>

              <div class="flex-1 text-sm space-y-1">
                <p>
                  <span class="font-medium">Ảnh:</span>
                  <span v-if="form.image_id" class="text-emerald-600 font-semibold">Đã upload</span>
                  <span v-else class="text-gray-500">Chưa có</span>
                </p>
                <p>
                  <span class="font-medium">Tags:</span>
                  <span v-if="form.tags.length">{{ form.tags.join(', ') }}</span>
                  <span v-else class="text-gray-500">—</span>
                </p>
                <p>
                  <span class="font-medium">Danh mục:</span>
                  <span v-if="form.categories.length">{{ form.categories.join(', ') }}</span>
                  <span v-else class="text-gray-500">—</span>
                </p>
              </div>
            </div>
          </div>
        </div>

        <!-- ❌ XOÁ TOÀN BỘ PHẦN TÓM TẮT ĐỀ CƯƠNG  -->
        <!-- (không còn modules, lessons, content_blocks khi tạo course) -->
      </section>

      <!-- ACTIONS (BOTTOM) -->
      <div class="form-actions">
        <button type="button" class="btn-cancel" @click="router.back()">Huỷ</button>

        <div class="flex gap-3">
          <button v-if="currentStep > 1" type="button" class="btn-secondary" @click="prevStep">
            Quay lại
          </button>

          <button
            v-if="currentStep < steps.length"
            type="button"
            class="btn-primary"
            :disabled="nextDisabled"
            @click="nextStep"
          >
            Tiếp tục
          </button>

          <button
            v-else
            type="button"
            class="btn-primary"
            :class="{ 'opacity-60 pointer-events-none': submitting }"
            @click="submit"
          >
            {{ submitting ? 'Đang tạo…' : 'Tạo khoá học' }}
          </button>
        </div>
      </div>
    </div>

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
        @click.self="handleNotificationOk"
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
            <button type="button" class="btn-primary" @click="handleNotificationOk">OK</button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, onBeforeUnmount } from 'vue'
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

// ================== STEP STATE ==================
const steps = [
  { id: 1, label: 'Thông tin', subLabel: 'Tên, môn, mô tả' },
  { id: 2, label: 'Ảnh bìa', subLabel: 'Upload lên S3' },
  // { id: 3, label: 'Đề cương', subLabel: 'Chương & bài học' },
  { id: 3, label: 'Xem lại', subLabel: 'Tạo khoá học' },
]

const currentStep = ref(1)
const submitting = ref(false)

function prevStep() {
  if (currentStep.value > 1) currentStep.value--
}

// ================== FORM STATE ==================
interface Module {
  title: string
  position: number
  lessons: Lesson[]
}
interface Lesson {
  title: string
  position: number
  content_blocks: ContentBlock[]

  pdf_id?: string | null
  docx_id?: string | null
  video_id?: string | null
  quiz_file_id?: string | null
}

interface ContentBlock {
  type: 'text'
  position: number
  payload: { text: string }
}

const form = reactive({
  title: '',
  subject: '',
  grade: '',
  description: '',
  price: 0,
  tags: [] as string[],
  categories: [] as string[],
  published: false,
  image_id: null as string | null,
  modules: [] as Module[],
})

const titleRef = ref<HTMLInputElement | null>(null)
const titleErr = ref('')

// TAGS / CATEGORIES INPUT
const tagsInput = ref('')
const categoriesInput = ref('')

const updateTags = () => {
  form.tags = tagsInput.value
    .split(',')
    .map((t) => t.trim())
    .filter((t) => t.length > 0)
}

const updateCategories = () => {
  form.categories = categoriesInput.value
    .split(',')
    .map((t) => t.trim())
    .filter((t) => t.length > 0)
}
const subjectErr = ref('')
const gradeErr = ref('')

// NEXT DISABLED
const nextDisabled = computed(() => {
  if (currentStep.value === 1) {
    return !form.title.trim() || !form.subject.trim() || !form.grade.trim()
  }
  return false
})
function nextStep() {
  if (currentStep.value === 1) {
    titleErr.value = ''
    subjectErr.value = ''
    gradeErr.value = ''

    if (!form.title.trim()) {
      titleErr.value = 'Vui lòng nhập tên khóa học.'
      titleRef.value?.focus()
      return
    }

    if (!form.subject.trim()) {
      subjectErr.value = 'Vui lòng chọn môn học.'
      return
    }

    if (!form.grade.trim()) {
      gradeErr.value = 'Vui lòng chọn khối lớp.'
      return
    }
  }

  if (currentStep.value < steps.length) {
    currentStep.value++
  }
}
// ================== THUMBNAIL UPLOAD (Presigned) ==================
const thumbnailInput = ref<HTMLInputElement | null>(null)

const MAX_THUMBNAIL_SIZE = 2 * 1024 * 1024 // 2MB

const thumbnail = reactive<{
  file: File | null
  previewUrl: string
  error: string
  uploading: boolean
  progress: number
  uploaded: boolean
  fileId: string | null
}>({
  file: null,
  previewUrl: '',
  error: '',
  uploading: false,
  progress: 0,
  uploaded: false,
  fileId: null,
})

const onPickThumbnail = (evt: Event) => {
  const input = evt.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > MAX_THUMBNAIL_SIZE) {
    thumbnail.error = 'File ảnh vượt quá dung lượng cho phép (tối đa 2MB).'
    thumbnail.file = null
    if (thumbnail.previewUrl) URL.revokeObjectURL(thumbnail.previewUrl)
    thumbnail.previewUrl = ''
    return
  }

  thumbnail.error = ''
  thumbnail.file = file
  if (thumbnail.previewUrl) URL.revokeObjectURL(thumbnail.previewUrl)
  thumbnail.previewUrl = URL.createObjectURL(file)
  thumbnail.uploaded = false
  thumbnail.fileId = null
  form.image_id = null

  // 🔥 TỰ ĐỘNG UPLOAD
  uploadThumbnail()
}

/**
 * Init upload -> PUT file to S3 -> Confirm
 */
async function uploadThumbnail() {
  if (!thumbnail.file) {
    thumbnail.error = 'Vui lòng chọn ảnh trước khi upload.'
    return
  }

  const file = thumbnail.file
  thumbnail.error = ''
  thumbnail.uploading = true
  thumbnail.progress = 0

  try {
    // 1) INIT
    const initRes = await axios.post(
      '/api/media/upload/init/',
      {
        filename: file.name,
        file_type: file.type,
        file_size: file.size,
        component: 'course_thumbnail',
      },
      { headers: { ...getAuthHeaders() } },
    )

    const { file_id, upload_url, upload_fields } = {
      file_id: initRes.data.file_id || initRes.data.id,
      upload_url: initRes.data.upload_url,
      upload_fields: initRes.data.upload_fields,
    }

    if (!file_id || !upload_url || !upload_fields) {
      throw new Error('Presigned URL không hợp lệ.')
    }

    // 2) UPLOAD TO S3 (POST multipart/form-data)
    const formData = new FormData()
    Object.entries(upload_fields).forEach(([key, value]) => {
      formData.append(key, value as string)
    })
    formData.append('file', file)

    await axios.post(upload_url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => {
        if (e.total) thumbnail.progress = Math.round((e.loaded * 100) / e.total)
      },
    })

    // 3) CONFIRM
    const confirmRes = await axios.post(
      `/api/media/upload/confirm/${file_id}/`,
      {},
      { headers: getAuthHeaders() },
    )

    form.image_id = confirmRes.data.id
    thumbnail.fileId = confirmRes.data.id
    thumbnail.uploaded = true
  } catch (error) {
    console.error('❌ Upload thumbnail lỗi:', error)
    thumbnail.error = 'Upload ảnh thất bại. Vui lòng thử lại.'
  } finally {
    thumbnail.uploading = false
  }
}

async function uploadGenericFile(file: File, component: string) {
  try {
    // 1) INIT
    const initRes = await axios.post(
      '/api/media/upload/init/',
      {
        filename: file.name,
        file_type: file.type,
        file_size: file.size,
        component,
      },
      { headers: getAuthHeaders() },
    )

    const { file_id, upload_url, upload_fields } = {
      file_id: initRes.data.file_id || initRes.data.id,
      upload_url: initRes.data.upload_url,
      upload_fields: initRes.data.upload_fields,
    }

    if (!file_id || !upload_url) throw new Error('Presigned URL không hợp lệ')

    // 2) UPLOAD (multipart/form-data)
    const formData = new FormData()
    Object.entries(upload_fields).forEach(([k, v]) => formData.append(k, v as string))
    formData.append('file', file)

    await axios.post(upload_url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    // 3) CONFIRM
    const confirmRes = await axios.post(
      `/api/media/upload/confirm/${file_id}/`,
      {},
      { headers: getAuthHeaders() },
    )

    return confirmRes.data
  } catch (err) {
    console.error('❌ Upload failed:', err)
    throw err
  }
}

// ================== NOTIFICATION MODAL ==================
const notificationModal = reactive({
  open: false,
  type: 'success' as 'success' | 'error',
  title: '',
  message: '',
  redirectAfterClose: false,
  redirectTo: '' as string,
})

function showNotification(
  type: 'success' | 'error',
  title: string,
  message: string,
  redirect = false,
  redirectTo = '',
) {
  notificationModal.type = type
  notificationModal.title = title
  notificationModal.message = message
  notificationModal.open = true
  notificationModal.redirectAfterClose = redirect
  notificationModal.redirectTo = redirectTo
}

function handleNotificationOk() {
  notificationModal.open = false
  if (notificationModal.redirectAfterClose && notificationModal.redirectTo) {
    router.push(notificationModal.redirectTo)
  }
}

// ================== SUBMIT (CREATE COURSE) ==================
async function submit() {
  titleErr.value = ''
  if (!form.title.trim()) {
    titleErr.value = 'Vui lòng nhập tên khoá học.'
    currentStep.value = 1
    titleRef.value?.focus()
    return
  }

  submitting.value = true

  try {
    const payload: any = {
      title: form.title,
      description: form.description,
      grade: form.grade || null,
      subject: form.subject || null,
      price: form.price || 0,
      categories: form.categories,
      tags: form.tags,
      image_id: form.image_id, // có thể là null nếu không upload ảnh
      published: form.published ?? false,
      // Nếu backend mới chỉ nhận metadata, KHÔNG gửi modules.
      // Nếu sau này backend hỗ trợ, có thể uncomment:
      // modules: form.modules,
    }

    console.log('🚀 Gửi payload tạo khoá học:', payload)

    const { data } = await axios.post('/api/content/instructor/courses/', payload, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    })

    const courseId = data?.id
    const redirectTo = courseId ? `/teacher/courses/${courseId}/edit` : '/teacher/courses'

    showNotification(
      'success',
      'Thành công',
      'Đã tạo khoá học thành công! Chuyển sang màn hình soạn đề cương.',
      true,
      redirectTo,
    )
  } catch (e: any) {
    console.error('❌ Lỗi khi tạo khoá học:', e)
    const detail = e?.response?.data?.detail

    if (detail && typeof detail === 'string' && detail.toLowerCase().includes('slug')) {
      showNotification(
        'error',
        'Tên khoá học đã tồn tại',
        'Đã có một khoá học khác dùng tên này. Vui lòng chọn tên khác.',
      )
    } else {
      showNotification(
        'error',
        'Lỗi',
        detail || e?.message || 'Không thể tạo khoá học. Vui lòng thử lại.',
      )
    }
  } finally {
    submitting.value = false
  }
}

// ================== CLEANUP ==================
onBeforeUnmount(() => {
  if (thumbnail.previewUrl) URL.revokeObjectURL(thumbnail.previewUrl)
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
.hint-text {
  @apply mt-2 text-xs text-gray-500;
}
.error-text {
  @apply mt-2 text-sm text-rose-600 font-medium;
}
.form-actions {
  @apply flex justify-between items-center gap-4 pt-6 border-t border-gray-100 mt-4;
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
</style>
