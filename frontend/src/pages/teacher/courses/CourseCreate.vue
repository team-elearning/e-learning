<template>
  <div class="container-wrapper">
    <h1 class="page-title">Tạo khoá học mới</h1>

    <form @submit.prevent="submit" class="course-form">
      <div class="form-grid">
        <!-- Tên khóa học -->
        <label class="form-field md:col-span-2">
          <span class="label-text">Tên khoá học <b class="text-rose-600">*</b></span>
          <input
            ref="titleRef"
            v-model.trim="f.title"
            class="input-field"
            :class="{ 'ring-2 ring-rose-500 border-rose-500': Boolean(titleErr) }"
            placeholder="Ví dụ: Luyện thi Toán lớp 3"
            aria-invalid="true"
            @input="titleErr = ''"
          />
          <p v-if="titleErr" class="error-text">{{ titleErr }}</p>
        </label>

        <label class="form-field">
          <span class="label-text">Môn học</span>
          <select v-model="f.subject" class="input-field">
            <option value="math">Toán</option>
            <option value="vietnamese">Tiếng Việt</option>
            <option value="english">Tiếng Anh</option>
            <option value="science">Khoa học</option>
            <option value="history">Lịch sử</option>
          </select>
        </label>

        <label class="form-field">
          <span class="label-text">Khối lớp</span>
          <select v-model.number="f.grade" class="input-field">
            <option :value="1">Lớp 1</option>
            <option :value="2">Lớp 2</option>
            <option :value="3">Lớp 3</option>
            <option :value="4">Lớp 4</option>
            <option :value="5">Lớp 5</option>
          </select>
        </label>

        <label class="form-field">
          <span class="label-text">Mức độ</span>
          <select v-model="f.level" class="input-field">
            <option value="basic">Cơ bản</option>
            <option value="advanced">Mở rộng</option>
          </select>
        </label>
        
        <label class="form-field">
          <span class="label-text">Số bài học</span>
          <input v-model.number="f.lessonsCount" type="number" min="1" class="input-field" placeholder="Số lượng bài học" />
        </label>

        <!-- Ảnh khoá học -->
        <div class="form-field md:col-span-2">
          <span class="label-text">Ảnh khoá học <i class="text-gray-500 font-normal">(tuỳ chọn)</i></span>
          <div class="file-upload-area">
            <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onPickCover" />
            <button type="button" class="btn-secondary" @click="fileInput?.click()">Chọn ảnh bìa</button>
            <span v-if="coverFile" class="file-info">
              {{ coverFile.name }} — {{ Math.round(coverFile.size / 1024) }} KB
            </span>
            <span v-else class="file-info text-gray-500">Chưa có ảnh nào được chọn</span>
          </div>
          <img v-if="coverPreview" :src="coverPreview" alt="Xem trước ảnh" class="image-preview" />
          <p class="hint-text">Hỗ trợ: JPG/PNG. Tối đa 2MB. (Không bắt buộc)</p>
          <p v-if="coverErr" class="error-text">{{ coverErr }}</p>
        </div>

        <!-- Video -->
        <div class="form-field md:col-span-2">
          <span class="label-text">Video bài học (tuỳ chọn)</span>
          <div class="file-upload-area">
            <input
              ref="videosInput"
              type="file"
              multiple
              :accept="acceptVideos"
              class="hidden"
              @change="onPickVideos"
            />
            <button type="button" class="btn-secondary" @click="videosInput?.click()">Thêm video</button>
            <span v-if="videoFiles.length" class="file-info">Đã chọn {{ videoFiles.length }} video.</span>
            <span v-else class="file-info text-gray-500">Chưa có video nào được chọn</span>
          </div>

          <video v-if="videoPreview" :src="videoPreview" controls class="video-preview"></video>

          <ul v-if="videoFiles.length" class="video-list">
            <li v-for="(vf, i) in videoFiles" :key="'v' + i" class="video-item">
              <span class="truncate">{{ vf.name }}</span>
              <span class="video-size">{{ (vf.size / 1024 / 1024).toFixed(1) }} MB</span>
            </li>
          </ul>
          <p class="hint-text">Tối đa 200MB/video; tổng ≤500MB.</p>
          <p v-if="videoErr" class="error-text">{{ videoErr }}</p>
        </div>
        
        <label class="form-field md:col-span-2">
          <span class="label-text">Trạng thái</span>
          <select v-model="f.status" class="input-field">
            <option value="draft">Nháp</option>
            <option value="published">Đã xuất bản</option>
          </select>
        </label>

        <label class="form-field md:col-span-2">
          <span class="label-text">Mô tả</span>
          <textarea v-model.trim="f.description" rows="4" class="input-field resize-y" placeholder="Mô tả chi tiết về khóa học"></textarea>
        </label>
      </div>

      <div class="form-actions">
        <button class="btn-primary" :class="{ 'opacity-60 pointer-events-none': submitting }">
          {{ submitting ? 'Đang lưu…' : 'Lưu khoá học' }}
        </button>
        <button type="button" class="btn-cancel" @click="router.back()">Huỷ</button>
      </div>
    </form>

    <!-- ===== Modal ảnh >2MB — màu & style giống hồ sơ giảng viên ===== -->
    <transition
      enter-active-class="transition-opacity duration-150 ease-out"
      leave-active-class="transition-opacity duration-150 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="limitModal.open"
        class="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="limit-title"
        @click.self="closeLimitModal"
      >
        <div
          ref="limitCard"
          tabindex="-1"
          class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-4 shadow-2xl outline-none"
        >
          <div class="mb-2 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5 text-amber-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
            <h3 id="limit-title" class="text-base font-bold text-slate-800">Không thể tải ảnh</h3>
          </div>
          <div class="mb-3 text-sm text-slate-800">
            <p>{{ limitModal.message }}</p>
            <small class="mt-1 block text-slate-500">Vui lòng chọn tệp PNG/JPG ≤ 2MB.</small>
          </div>
          <div class="flex justify-end">
            <button type="button" class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700" @click="closeLimitModal">
              ĐÃ HIỂU
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- ===== Modal kết quả lưu — cùng palette với popup trên ===== -->
    <transition
      enter-active-class="transition-opacity duration-150 ease-out"
      leave-active-class="transition-opacity duration-150 ease-in"
      enter-from-class="opacity-0"
      leave-to-class="opacity-0"
    >
      <div
        v-if="resultModal.open"
        class="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="result-title"
        @click.self="closeResultModal"
      >
        <div
          ref="resultCard"
          tabindex="-1"
          class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-4 shadow-2xl outline-none"
        >
          <div class="mb-2 flex items-center gap-2">
            <svg xmlns="http://www.w3.org/2000/svg" class="h-5 w-5" :class="resultModal.type==='success' ? 'text-emerald-600' : 'text-amber-500'" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2">
              <path v-if="resultModal.type==='success'" stroke-linecap="round" stroke-linejoin="round" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              <path v-else stroke-linecap="round" stroke-linejoin="round" d="M12 9v3m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
            </svg>
            <h3 id="result-title" class="text-base font-bold text-slate-800">
              {{ resultModal.title }}
            </h3>
          </div>
          <div class="mb-3 text-sm text-slate-800">
            <p>{{ resultModal.message }}</p>
          </div>
          <div class="flex justify-end">
            <button type="button" class="rounded-lg bg-blue-600 px-3 py-2 text-sm font-semibold text-white hover:bg-blue-700" @click="handleResultConfirm">
              {{ resultModal.type === 'success' ? 'OK' : 'Thử lại' }}
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onBeforeUnmount, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { courseService, type CourseDetail, type Grade, type Level, type CourseStatus, type Subject } from '@/services/course.service'

const router = useRouter()

/** Form theo schema service */
const f = reactive<Partial<CourseDetail> & { lessonsCount?: number }>({
  title: '',
  subject: 'math' as Subject,
  grade: 3 as Grade,
  level: 'basic' as Level,
  description: '',
  lessonsCount: 24,
  status: 'draft' as CourseStatus
})

/* ---------- UI state cho lỗi tên ---------- */
const titleRef = ref<HTMLInputElement | null>(null)
const titleErr = ref('')

/* ---------- ẢNH KHOÁ HỌC ---------- */
const fileInput = ref<HTMLInputElement | null>(null)
const coverFile = ref<File | null>(null)
const coverPreview = ref<string>('')
const coverErr = ref('')

/** ===== Modal 2MB ===== */
const MAX_AVATAR_SIZE = 2 * 1024 * 1024 // 2MB
const OVER_LIMIT_MSG = 'File ảnh vượt quá dung lượng cho phép (2MB)'
const limitModal = reactive<{ open: boolean; message: string }>({ open: false, message: '' })
const limitCard = ref<HTMLElement | null>(null)
function showLimitModal(msg = OVER_LIMIT_MSG) { limitModal.message = msg; limitModal.open = true; queueMicrotask(() => limitCard.value?.focus()) }
function closeLimitModal() { limitModal.open = false }

/** ===== Modal kết quả ===== */
const resultModal = reactive<{ open: boolean; type: 'success' | 'error'; title: string; message: string }>({ open: false, type: 'success', title: '', message: '' })
const resultCard = ref<HTMLElement | null>(null)
function showResultModal(type: 'success' | 'error', title: string, message: string) {
  resultModal.type = type; resultModal.title = title; resultModal.message = message;
  resultModal.open = true; queueMicrotask(() => resultCard.value?.focus())
}
function closeResultModal() { resultModal.open = false }
function handleResultConfirm() {
  if (resultModal.type === 'success') { closeResultModal(); router.push({ path: '/teacher/courses' }) }
  else { closeResultModal() }
}

/** ESC để đóng modal (nếu muốn) */
function handleEsc(e: KeyboardEvent) {
  if (e.key !== 'Escape') return
  if (limitModal.open) { e.stopPropagation(); closeLimitModal() }
  else if (resultModal.open) { e.stopPropagation(); closeResultModal() }
}
onMounted(() => window.addEventListener('keydown', handleEsc))
onBeforeUnmount(() => window.removeEventListener('keydown', handleEsc))

/* ---------- Ảnh bìa ---------- */
function onPickCover(e: Event) {
  coverErr.value = ''
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) {
    coverErr.value = 'Vui lòng chọn file ảnh (JPG/PNG).'
    input.value = ''
    return
  }
  if (file.size > MAX_AVATAR_SIZE) {
    showLimitModal()
    input.value = ''
    coverFile.value = null
    if (coverPreview.value) { URL.revokeObjectURL(coverPreview.value); coverPreview.value = '' }
    return
  }

  coverFile.value = file
  if (coverPreview.value) URL.revokeObjectURL(coverPreview.value)
  coverPreview.value = URL.createObjectURL(file)
}

/* ---------- VIDEO BÀI HỌC ---------- */
const videosInput = ref<HTMLInputElement | null>(null)
const videoFiles = ref<File[]>([])
const videoPreview = ref<string>('')
const videoErr = ref('')
const acceptVideos = computed(() => ['video/mp4', 'video/webm', 'video/quicktime'].join(','))

function onPickVideos(e: Event) {
  videoErr.value = ''
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files ?? [])
  const allowed = ['video/mp4', 'video/webm', 'video/quicktime']
  const valid: File[] = []

  for (const file of files) {
    if (!allowed.includes(file.type)) continue
    if (file.size > 200 * 1024 * 1024) { videoErr.value = `File ${file.name} vượt 200MB, đã bỏ qua.`; continue }
    valid.push(file)
  }
  const total = valid.reduce((s, f) => s + f.size, 0)
  if (total > 500 * 1024 * 1024) { videoErr.value = 'Tổng dung lượng video vượt 500MB.'; input.value=''; return }

  videoFiles.value = valid
  if (videoPreview.value) URL.revokeObjectURL(videoPreview.value)
  videoPreview.value = videoFiles.value.length ? URL.createObjectURL(videoFiles.value[0]) : ''
}

/* ---------- SUBMIT ---------- */
onBeforeUnmount(() => {
  if (coverPreview.value) URL.revokeObjectURL(coverPreview.value)
  if (videoPreview.value) URL.revokeObjectURL(videoPreview.value)
})

const submitting = ref(false)

async function submit() {
  titleErr.value = ''
  if (!f.title || !f.title.trim()) {
    titleErr.value = 'Vui lòng nhập tên khoá học.'
    titleRef.value?.focus()
    titleRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
    return
  }

  submitting.value = true
  try {
    // Nếu dùng upload file thật: tạo FormData ở đây (demo giữ nguyên)
    // const fd = new FormData() ... append ...

    await courseService.create({
      title: f.title,
      grade: f.grade,
      subject: f.subject,
      level: f.level,
      status: f.status,
      description: f.description,
      durationMinutes: 0,
      sections: []
    } as Partial<CourseDetail>)

    showResultModal('success', 'Đã tạo khoá học thành công!', 'Khoá học của bạn đã được lưu.')
  } catch (e: any) {
    showResultModal('error', 'Tạo khoá học thất bại', e?.message || 'Có lỗi xảy ra. Vui lòng thử lại.')
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
/* Base container */
.container-wrapper { @apply mx-auto max-w-4xl p-6 lg:p-8; }
.page-title { @apply mb-6 text-3xl font-extrabold text-gray-800 text-center; }

/* Form styling */
.course-form { @apply space-y-8 rounded-2xl bg-white p-8 shadow-xl border border-gray-100; }
.form-grid { @apply grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-2; }
.form-field { @apply block; }
.label-text { @apply mb-2 block text-sm font-semibold text-gray-700; }
.input-field { @apply w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-800 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition duration-200 ease-in-out; }
textarea.input-field { @apply resize-y; }

/* File Upload Specifics */
.file-upload-area { @apply flex flex-wrap items-center gap-4; }
.btn-secondary { @apply rounded-lg border border-gray-300 px-5 py-2.5 font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 transition duration-200 ease-in-out; }
.file-info { @apply text-sm text-gray-600; }
.image-preview { @apply mt-4 w-full h-48 rounded-lg object-cover shadow-md; }
.video-preview { @apply mt-4 w-full rounded-lg object-cover shadow-md max-h-[300px]; }
.hint-text { @apply mt-2 text-xs text-gray-500; }
.error-text { @apply mt-2 text-sm text-rose-600 font-medium; }
.video-list { @apply mt-3 space-y-2 text-sm bg-gray-50 p-3 rounded-lg border border-gray-200; }
.video-item { @apply flex items-center justify-between text-gray-700; }
.video-size { @apply ml-3 shrink-0 font-medium text-gray-600; }

/* Form Actions */
.form-actions { @apply flex justify-end gap-4 pt-6 border-t border-gray-100 mt-8; }

/* ĐỒNG BỘ MÀU VỚI POPUP: dùng bg-blue-600 / hover:bg-blue-700 */
.btn-primary {
  @apply rounded-xl bg-blue-600 px-6 py-3
         font-bold text-white shadow-lg
         hover:bg-blue-700
         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
         disabled:opacity-50 disabled:cursor-not-allowed
         transition duration-200 ease-in-out;
}
.btn-cancel {
  @apply rounded-xl border border-gray-300 bg-white px-6 py-3
         font-semibold text-gray-700 shadow-sm hover:bg-gray-100
         focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2
         transition duration-200 ease-in-out;
}
</style>
