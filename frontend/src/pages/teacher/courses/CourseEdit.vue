<template>
  <div class="container-wrapper">
    <div v-if="loading" class="feedback-card">
      <svg class="animate-spin h-6 w-6 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
      </svg>
      <span>Đang tải khoá học…</span>
    </div>
    <div v-else-if="err" class="feedback-card text-red-600 bg-red-50 border-red-200">
      <svg xmlns="http://www.w3.org/2000/svg" class="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
      <span>{{ err }}</span>
    </div>

    <div v-else-if="course">
      <div class="text-center mb-8">
        <h1 class="page-title">Chỉnh sửa khoá học</h1>
        <p class="page-subtitle">Cập nhật thông tin chi tiết cho khoá học của bạn.</p>
      </div>
      
      <form @submit.prevent="save" class="course-form">
        <div class="form-grid">

          <label class="form-field md:col-span-2">
            <span class="label-text">Tên khoá học <b class="text-rose-600">*</b></span>
            <input v-model.trim="course.title" class="input-field" required />
          </label>
          
          <div class="form-field">
            <span class="label-text">Khối lớp</span>
            <div class="static-info">{{ `Lớp ${course.grade}` }}</div>
          </div>
          <div class="form-field">
            <span class="label-text">Môn học</span>
            <div class="static-info">{{ subjectLabel(course.subject) }}</div>
          </div>

          <div class="form-field md:col-span-2">
            <span class="label-text">Ảnh khoá học</span>
            <div class="flex items-center gap-4">
              <img :src="coverPreview || '/placeholder-image.svg'" alt="Ảnh bìa" class="h-20 w-32 rounded-lg object-cover border"/>
              <div>
                <input ref="coverInput" type="file" accept="image/*" class="hidden" @change="onPickCover"/>
                <button type="button" class="btn-secondary" @click="coverInput?.click()">Đổi ảnh</button>
                <p class="hint-text mt-2">JPG/PNG, tối đa 2MB. Giữ ảnh cũ nếu không đổi.</p>
              </div>
            </div>
             <p v-if="coverFile" class="file-info-selected">
              Đã chọn ảnh mới: <b>{{ coverFile.name }}</b>
            </p>
          </div>

          <div class="form-field md:col-span-2">
            <span class="label-text">Video bài học</span>
            <div class="file-upload-area">
              <input ref="videosInput" type="file" multiple :accept="acceptVideos" class="hidden" @change="onPickVideos"/>
              <button type="button" class="btn-secondary" @click="videosInput?.click()">Thêm video</button>
              <span v-if="videoFiles.length" class="file-info">{{ videoFiles.length }} video đã được chọn.</span>
              <span v-else class="file-info text-gray-500">Chưa có video nào</span>
            </div>
            <ul v-if="videoFiles.length" class="video-list">
              <li v-for="(f, i) in videoFiles" :key="'v' + i" class="video-item">
                <span class="truncate">{{ f.name }}</span>
                <span class="video-size">{{ (f.size / 1024 / 1024).toFixed(1) }} MB</span>
              </li>
            </ul>
             <video v-if="videoPreview" :src="videoPreview" controls class="video-preview"></video>
            <p class="hint-text">MP4/WebM/MOV, tối đa 200MB/video, tổng ≤500MB.</p>
          </div>
          
          <label class="form-field">
            <span class="label-text">Số bài học</span>
            <input v-model.number="lessonsProxy" type="number" min="1" class="input-field" />
          </label>
          <label class="form-field">
            <span class="label-text">Trạng thái</span>
            <select v-model="course.status" class="input-field">
              <option value="draft">Nháp</option>
              <option value="pending_review">Chờ duyệt</option>
              <option value="published">Đã xuất bản</option>
              <option value="rejected">Từ chối</option>
              <option value="archived">Lưu trữ</option>
            </select>
          </label>
        </div>

        <div class="form-actions">
           <p v-if="addedContentHint" class="text-sm text-slate-500 mr-auto">
             Thêm nội dung #{{ addedContentHint }} (demo).
           </p>
          <button type="button" class="btn-cancel" @click="router.back()">Huỷ</button>
          <button class="btn-primary" :disabled="saving">
            {{ saving ? 'Đang lưu…' : 'Lưu thay đổi' }}
          </button>
        </div>
      </form>
    </div>

    <div v-else class="feedback-card">Không tìm thấy khoá học.</div>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { courseService, type CourseDetail, type Subject } from '@/services/course.service'

/* ===== Router & state ===== */
const route = useRoute()
const router = useRouter()
const idParam = route.params.id
const id = Number(idParam)

const loading = ref(true)
const saving = ref(false)
const err = ref('')

const course = ref<CourseDetail | null>(null)

/* Nếu mở từ ContentLibrary: ?add=<contentId> */
const addedContentHint = ref<string | null>(null)

/* ===== File inputs & previews ===== */
const coverInput = ref<HTMLInputElement | null>(null)
const videosInput = ref<HTMLInputElement | null>(null)

const coverFile = ref<File | null>(null)
const coverPreview = ref<string>('')   // URL để hiển thị
const previewFromFile = ref(false)     // true nếu preview từ file mới -> revoke khi unmount

const videoFiles = ref<File[]>([])
const videoPreview = ref<string>('')

/* ===== Helpers ===== */
const subjectLabel = (s: Subject) =>
  s === 'math' ? 'Toán' :
  s === 'vietnamese' ? 'Tiếng Việt' :
  s === 'english' ? 'Tiếng Anh' :
  s === 'science' ? 'Khoa học' : 'Lịch sử'

/* Proxy lessons (CourseDetail không có field "lessons" cố định; ta dùng lessonsCount) */
const lessonsProxy = computed({
  get: () => course.value?.lessonsCount ?? 0,
  set: (v: number) => { if (course.value) course.value.lessonsCount = v }
})

/* Accept video types */
const acceptVideos = computed(() => ['video/mp4', 'video/webm', 'video/quicktime'].join(','))

/* ===== File pick handlers ===== */
function onPickCover(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (!file.type.startsWith('image/')) { alert('Vui lòng chọn đúng file ảnh.'); input.value = ''; return }
  if (file.size > 2 * 1024 * 1024)     { alert('Ảnh tối đa 2MB.'); input.value = ''; return }

  coverFile.value = file
  if (previewFromFile.value && coverPreview.value) URL.revokeObjectURL(coverPreview.value)
  coverPreview.value = URL.createObjectURL(file)
  previewFromFile.value = true
}

function onPickVideos(e: Event) {
  const input = e.target as HTMLInputElement
  const files = Array.from(input.files ?? [])

  const allowed = ['video/mp4', 'video/webm', 'video/quicktime']
  const valid: File[] = []
  for (const f of files) {
    if (!allowed.includes(f.type)) continue
    if (f.size > 200 * 1024 * 1024) { alert(`File ${f.name} vượt 200MB, bỏ qua.`); continue }
    valid.push(f)
  }
  const total = valid.reduce((s, f) => s + f.size, 0)
  if (total > 500 * 1024 * 1024) { alert('Tổng dung lượng video vượt 500MB.'); input.value = ''; return }

  videoFiles.value = valid

  if (videoPreview.value) URL.revokeObjectURL(videoPreview.value)
  videoPreview.value = videoFiles.value.length ? URL.createObjectURL(videoFiles.value[0]) : ''
}

/* ===== Load detail ===== */
onMounted(async () => {
  try {
    loading.value = true
    const detail = await courseService.detail(id)
    course.value = reactive(detail)

    // preview ảnh ban đầu = thumbnail (nếu có)
    if (course.value.thumbnail) {
      coverPreview.value = course.value.thumbnail
      previewFromFile.value = false
    }

    // nếu có query add (từ ContentLibrary)
    const add = route.query.add ? String(route.query.add) : ''
    if (add) addedContentHint.value = add
  } catch (e: any) {
    err.value = e?.message || 'Không tải được khoá học.'
  } finally {
    loading.value = false
  }
})

/* ===== Save ===== */
async function save() {
  if (!course.value) return
  saving.value = true
  try {
    const fd = new FormData()
    fd.append('title', course.value.title)
    fd.append('status', course.value.status)
    fd.append('lessonsCount', String(course.value.lessonsCount ?? 0))
    fd.append('grade', String(course.value.grade))
    fd.append('subject', course.value.subject)
    if (course.value.level) fd.append('level', course.value.level)
    if (course.value.description) fd.append('description', course.value.description)

    // Ảnh mới (nếu có). Nếu không gửi, backend giữ thumbnail cũ
    if (coverFile.value) fd.append('thumbnail', coverFile.value)

    // Video (tuỳ chọn nhiều) – demo append, backend tuỳ ý xử lý
    videoFiles.value.forEach((f) => fd.append('videos[]', f))

    // Gọi API thật của bạn – service mock sẽ trả { ok: true }
    await courseService.update(id, fd as unknown as Partial<CourseDetail>)

    alert('Đã lưu (demo)')
    router.push({ path: `/teacher/courses/${id}` })
  } catch (e: any) {
    alert(e?.message || 'Lưu thất bại, thử lại.')
  } finally {
    saving.value = false
  }
}

/* ===== Cleanup ===== */
onBeforeUnmount(() => {
  if (previewFromFile.value && coverPreview.value) URL.revokeObjectURL(coverPreview.value)
  if (videoPreview.value) URL.revokeObjectURL(videoPreview.value)
})
</script>

<style scoped>
.container-wrapper {
  @apply mx-auto max-w-4xl p-6 lg:p-8;
}

.page-title {
  @apply text-3xl font-extrabold text-gray-800;
}
.page-subtitle {
  @apply mt-2 text-base text-gray-500;
}

.feedback-card {
  @apply flex items-center justify-center gap-3 rounded-2xl bg-white p-8 text-lg font-medium text-gray-600 shadow-lg border border-gray-100;
}

/* Form styling */
.course-form {
  @apply space-y-8 rounded-2xl bg-white p-8 shadow-xl border border-gray-100;
}
.form-grid {
  @apply grid grid-cols-1 gap-x-8 gap-y-6 md:grid-cols-2;
}
.form-field {
  @apply block;
}
.label-text {
  @apply mb-2 block text-sm font-semibold text-gray-700;
}
.input-field {
  @apply w-full rounded-lg border border-gray-300 px-4 py-2.5 text-gray-800 placeholder-gray-400
         focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none
         transition duration-200 ease-in-out;
}
.static-info {
    @apply w-full rounded-lg border border-gray-200 bg-gray-50 px-4 py-2.5 text-gray-600 font-medium;
}

/* File Upload Specifics */
.file-upload-area {
  @apply flex flex-wrap items-center gap-4;
}
.btn-secondary {
  @apply rounded-lg border border-gray-300 bg-white px-5 py-2.5 font-medium text-gray-700 
         hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
         transition duration-200 ease-in-out;
}
.file-info {
  @apply text-sm text-gray-600;
}
.file-info-selected {
    @apply mt-3 text-sm text-blue-700 bg-blue-50 p-2 rounded-md;
}
.video-preview {
  @apply mt-4 w-full rounded-lg object-cover shadow-md max-h-[300px];
}
.hint-text {
  @apply text-xs text-gray-500;
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
  @apply flex items-center gap-4 pt-6 border-t border-gray-200 mt-8;
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
</style>