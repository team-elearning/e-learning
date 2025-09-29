<template>
  <div class="container-wrapper">
    <h1 class="page-title">Tạo khoá học mới</h1>

    <form @submit.prevent="submit" class="course-form">
      <div class="form-grid">
        <label class="form-field md:col-span-2">
          <span class="label-text">Tên khoá học <b class="text-rose-600">*</b></span>
          <input v-model.trim="f.title" class="input-field" placeholder="Ví dụ: Luyện thi Toán lớp 3" required />
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

        <div class="form-field md:col-span-2">
          <span class="label-text">Ảnh khoá học <b class="text-rose-600">*</b></span>
          <div class="file-upload-area">
            <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onPickCover" />
            <button type="button" class="btn-secondary" @click="fileInput?.click()">
              Chọn ảnh bìa
            </button>
            <span v-if="coverFile" class="file-info">
              {{ coverFile.name }} — {{ Math.round(coverFile.size / 1024) }} KB
            </span>
            <span v-else class="file-info text-gray-500">Chưa có ảnh nào được chọn</span>
          </div>
          <img v-if="coverPreview" :src="coverPreview" alt="Xem trước ảnh" class="image-preview" />
          <p class="hint-text">Hỗ trợ: JPG/PNG. Tối đa 2MB. (Bắt buộc)</p>
          <p v-if="coverErr" class="error-text">{{ coverErr }}</p>
        </div>

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
            <button type="button" class="btn-secondary" @click="videosInput?.click()">
              Thêm video
            </button>
            <span v-if="videoFiles.length" class="file-info">
              Đã chọn {{ videoFiles.length }} video.
            </span>
            <span v-else class="file-info text-gray-500">Chưa có video nào được chọn</span>
          </div>

          <video v-if="videoPreview" :src="videoPreview" controls class="video-preview"></video>

          <ul v-if="videoFiles.length" class="video-list">
            <li v-for="(f, i) in videoFiles" :key="'v' + i" class="video-item">
              <span class="truncate">{{ f.name }}</span>
              <span class="video-size">{{ (f.size / 1024 / 1024).toFixed(1) }} MB</span>
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
        <button :disabled="submitting || !canSubmit" class="btn-primary">
          {{ submitting ? 'Đang lưu…' : 'Lưu khoá học' }}
        </button>
        <button type="button" class="btn-cancel" @click="router.back()">Huỷ</button>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { courseService, type CourseDetail, type Grade, type Level, type CourseStatus, type Subject } from '@/services/course.service'

const router = useRouter()

/** Form theo schema service */
const f = reactive<Partial<CourseDetail> & {
  lessonsCount?: number
}>({
  title: '',
  subject: 'math' as Subject,
  grade: 3 as Grade,
  level: 'basic' as Level,
  description: '',
  lessonsCount: 24,
  status: 'draft' as CourseStatus
})

/* ---------- ẢNH KHOÁ HỌC ---------- */
const fileInput = ref<HTMLInputElement | null>(null)
const coverFile = ref<File | null>(null)
const coverPreview = ref<string>('')
const coverErr = ref('')

function onPickCover(e: Event) {
  coverErr.value = ''
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return
  if (!file.type.startsWith('image/')) { coverErr.value = 'Vui lòng chọn file ảnh (JPG/PNG).'; input.value=''; return }
  if (file.size > 2 * 1024 * 1024) { coverErr.value = 'Ảnh tối đa 2MB.'; input.value=''; return }
  coverFile.value = file
  if (coverPreview.value) URL.revokeObjectURL(coverPreview.value)
  coverPreview.value = URL.createObjectURL(file)
}

/* ---------- VIDEO BÀI HỌC ---------- */
const videosInput = ref<HTMLInputElement | null>(null)
const videoFiles = ref<File[]>([])
const videoPreview = ref<string>('')
const videoErr = ref('')

const acceptVideos = computed(() =>
  ['video/mp4', 'video/webm', 'video/quicktime'].join(',')
)

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
const canSubmit = computed(() => Boolean(f.title && coverFile.value))

async function submit() {
  if (!canSubmit.value) {
    alert('Vui lòng điền đầy đủ Tên khoá học và chọn Ảnh khoá học.');
    return;
  }
  submitting.value = true
  try {
    // Nếu back-end của bạn nhận multipart, dùng FormData:
    const fd = new FormData()
    fd.append('title', f.title!)
    fd.append('grade', String(f.grade!))
    fd.append('subject', f.subject!)
    fd.append('level', f.level!)
    fd.append('status', f.status!)
    if (f.description) fd.append('description', f.description)
    if (f.lessonsCount) fd.append('lessonsCount', String(f.lessonsCount))
    if (coverFile.value) fd.append('thumbnail', coverFile.value)       // ảnh
    videoFiles.value.forEach(v => fd.append('videos[]', v)) // video optional
    // await api.post('/admin/courses', fd)                // hoặc endpoint của bạn

    // Với mock service hiện tại: truyền Partial<CourseDetail>
    await courseService.create({
      title: f.title,
      grade: f.grade,
      subject: f.subject,
      level: f.level,
      status: f.status,
      description: f.description,
      // mock không lưu file, nhưng bạn vẫn có thể lưu lessonsCount để hiển thị sau
      durationMinutes: 0, // Giá trị mặc định
      sections: [] // Giá trị mặc định
    } as Partial<CourseDetail>)

    alert('Đã tạo khoá học (mock).');
    router.push({ path: '/teacher/courses' });
  } catch (e: any) {
    alert(e?.message || 'Tạo khoá học thất bại.');
  } finally {
    submitting.value = false;
  }
}
</script>

<style scoped>
/* Base container */
.container-wrapper {
  @apply mx-auto max-w-4xl p-6 lg:p-8;
}

.page-title {
  @apply mb-6 text-3xl font-extrabold text-gray-800 text-center;
}

/* Form styling */
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
  @apply w-full rounded-lg border border-gray-300 px-4 py-2.5 
         text-gray-800 placeholder-gray-400 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none
         transition duration-200 ease-in-out;
}

textarea.input-field {
  @apply resize-y;
}

/* File Upload Specifics */
.file-upload-area {
  @apply flex flex-wrap items-center gap-4;
}

.btn-secondary {
  @apply rounded-lg border border-gray-300 px-5 py-2.5 font-medium text-gray-700 
         hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
         transition duration-200 ease-in-out;
}

.file-info {
  @apply text-sm text-gray-600;
}

.image-preview, .video-preview {
  @apply mt-4 w-full rounded-lg object-cover shadow-md;
}

.image-preview {
  @apply h-48; /* Increased height for better preview */
}

.video-preview {
  @apply max-h-[300px];
}

.hint-text {
  @apply mt-2 text-xs text-gray-500;
}

.error-text {
  @apply mt-2 text-sm text-rose-600 font-medium;
}

.video-list {
  @apply mt-3 space-y-2 text-sm bg-gray-50 p-3 rounded-lg border border-gray-200;
}

.video-item {
  @apply flex items-center justify-between text-gray-700;
}

.video-size {
  @apply ml-3 shrink-0 font-medium text-gray-600;
}

/* Form Actions */
.form-actions {
  @apply flex justify-end gap-4 pt-6 border-t border-gray-100 mt-8;
}

.btn-primary {
  @apply rounded-xl bg-gradient-to-r from-blue-600 to-blue-800 px-6 py-3 
         font-bold text-white shadow-lg hover:from-blue-700 hover:to-blue-900 
         focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
         disabled:opacity-50 disabled:cursor-not-allowed transition duration-200 ease-in-out;
}

.btn-cancel {
  @apply rounded-xl border border-gray-300 bg-white px-6 py-3 
         font-semibold text-gray-700 shadow-sm hover:bg-gray-100 
         focus:outline-none focus:ring-2 focus:ring-gray-400 focus:ring-offset-2
         transition duration-200 ease-in-out;
}

/* Responsive adjustments */
@media (min-width: 768px) {
  .form-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>