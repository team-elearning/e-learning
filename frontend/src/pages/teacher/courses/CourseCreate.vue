<!-- frontend/src/pages/teacher/courses/CourseCreate.vue -->
<template>
  <div class="min-h-screen w-full bg-slate-50">
    <main class="mx-auto w-full max-w-5xl px-4 py-6 sm:px-6 md:px-10">
      <div class="page-head">
        <div>
          <p class="page-kicker">Khoá học</p>
          <h1 class="page-title">Tạo khoá học</h1>
        </div>
        <div class="page-actions">
          <button class="btn btn-secondary" type="button" @click="router.push('/teacher/courses')">Về danh sách</button>
          <button class="btn btn-primary" :disabled="saving" @click="submit">
            {{ saving ? 'Đang lưu…' : 'Lưu khoá học' }}
          </button>
        </div>
      </div>

      <!-- Thông tin khoá học -->
      <section class="card">
        <div class="section-head">
          <h2 class="section-title">Thông tin khoá học</h2>
          <p class="section-desc">Nhập thông tin cơ bản và ảnh khoá học.</p>
        </div>
        <div class="space-y-4">
          <label class="field">
            <span class="label">Tên khoá học <span class="text-rose-600">*</span></span>
            <input v-model.trim="form.title" class="input" placeholder="Nhập tên khoá học" />
          </label>
          <div class="grid gap-3 md:grid-cols-3">
            <label class="field">
              <span class="label">Khối lớp</span>
              <select v-model.number="form.grade" class="input">
                <option v-for="g in [1,2,3,4,5]" :key="g" :value="g">Lớp {{ g }}</option>
              </select>
            </label>
            <label class="field">
              <span class="label">Môn học</span>
              <select v-model="form.subject" class="input">
                <option value="math">Toán</option>
                <option value="vietnamese">Tiếng Việt</option>
                <option value="english">Tiếng Anh</option>
                <option value="science">Khoa học</option>
                <option value="history">Lịch sử</option>
              </select>
            </label>
            <label class="field">
              <span class="label">Mức độ</span>
              <select v-model="form.level" class="input">
                <option value="basic">Cơ bản</option>
                <option value="advanced">Nâng cao</option>
              </select>
            </label>
          </div>
          <div class="grid gap-3 md:grid-cols-3">
            <label class="field">
              <span class="label">Trạng thái</span>
              <select v-model="form.status" class="input">
                <option value="draft">Nháp</option>
                <option value="published">Xuất bản</option>
              </select>
            </label>
            <label class="field md:col-span-2">
              <span class="label">Ảnh thumbnail (chọn file)</span>
              <label class="input-file">
                <input type="file" accept="image/*" class="hidden" @change="onPickThumb" />
                <span class="input-file__btn">Chọn ảnh</span>
                <span class="input-file__text">{{ form.thumbnailFile?.name || 'Chưa chọn ảnh' }}</span>
              </label>
              <div v-if="form.thumbnailPreview" class="thumb-preview">
                <img :src="form.thumbnailPreview" alt="preview" class="thumb-img" />
              </div>
            </label>
          </div>
          <label class="field">
            <span class="label">Mô tả</span>
            <textarea
              v-model.trim="form.description"
              rows="3"
              class="input"
              placeholder="Mô tả ngắn gọn nội dung, mục tiêu…"
            />
          </label>
        </div>
      </section>

      <!-- Chương trình học -->
        <section class="card">
          <div class="mb-3 flex items-center justify-between">
            <div>
              <h2 class="section-title">Chương trình học (Modules &amp; Lessons)</h2>
              <p class="section-desc">Thêm chương và bài, mỗi bài chọn file video.</p>
            </div>
            <div class="flex gap-2">
              <button type="button" class="btn btn-primary" @click="addModule">+ Thêm Chương</button>
            </div>
          </div>

        <div v-if="!form.modules.length" class="empty">Chưa có chương. Hãy thêm chương đầu tiên.</div>

        <div v-for="(mod, mIndex) in form.modules" :key="mod.id" class="module">
          <div class="module-header">
            <div class="flex-1 space-y-2">
              <label class="field">
                <span class="label">Tên chương</span>
                <input
                  v-model.trim="mod.title"
                  class="input"
                  :placeholder="`Chương ${mIndex + 1}`"
                />
              </label>
            </div>
            <button type="button" class="btn btn-ghost text-rose-600" @click="removeModule(mIndex)">Xoá</button>
          </div>

          <div class="lesson-actions">
            <span class="text-sm font-semibold text-slate-700">Bài học</span>
            <button type="button" class="btn btn-secondary" @click="addLesson(mod)">+ Thêm Bài</button>
          </div>

          <div v-if="!mod.lessons.length" class="empty small">Chưa có bài trong chương này.</div>

          <div v-for="(lesson, lIndex) in mod.lessons" :key="lesson.id" class="lesson">
            <div class="flex-1 grid gap-2 md:grid-cols-2">
              <label class="field">
                <span class="label">Tên bài học</span>
                <input
                  v-model.trim="lesson.title"
                  class="input"
                  :placeholder="`Bài ${mIndex + 1}.${lIndex + 1}`"
                />
              </label>
              <label class="field">
                <span class="label">File video</span>
                <input type="file" accept="video/*" class="input" @change="onPickVideo(lesson, $event)" />
                <p v-if="lesson.videoPreview" class="text-xs text-slate-500 truncate">Đã chọn: {{ lesson.videoFile?.name || 'Video mẫu' }}</p>
              </label>
            </div>
            <button type="button" class="btn btn-ghost text-rose-600" @click="removeLesson(mod, lIndex)">Xoá</button>
          </div>
        </div>
      </section>

      <!-- Errors -->
      <div v-if="errors.length" class="card border border-rose-200 bg-rose-50 text-rose-700">
        <div class="font-semibold">Cần kiểm tra:</div>
        <ul class="list-disc pl-5 space-y-1 text-sm">
          <li v-for="err in errors" :key="err">{{ err }}</li>
        </ul>
      </div>

      <!-- Actions -->
          <div class="mt-6 flex flex-wrap items-center gap-3">
            <button class="btn btn-primary" :disabled="saving" @click="submit">
              {{ saving ? 'Đang lưu…' : 'Lưu khoá học' }}
            </button>
            <button class="btn btn-secondary" type="button" @click="router.push('/teacher/courses')">Huỷ</button>
            <span v-if="successMsg" class="text-sm text-emerald-700">{{ successMsg }}</span>
          </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { courseService, type CourseDetail } from '@/services/course.service'

type LessonDraft = { id: string; title: string; videoFile: File | null; videoPreview: string }
type ModuleDraft = { id: string; title: string; lessons: LessonDraft[] }

const router = useRouter()

const form = reactive<{
  title: string
  description: string
  grade: number
  subject: 'math' | 'vietnamese' | 'english' | 'science' | 'history'
  level: 'basic' | 'advanced'
  status: 'draft' | 'published'
  thumbnailFile: File | null
  thumbnailPreview: string
  modules: ModuleDraft[]
}>({
  title: '',
  description: '',
  grade: 3,
  subject: 'math',
  level: 'basic',
  status: 'draft',
  thumbnailFile: null,
  thumbnailPreview: '',
  modules: [
    {
      id: uid('m'),
      title: 'Chương 1',
      lessons: [{ id: uid('l'), title: 'Bài 1', videoFile: null, videoPreview: '' }],
    },
  ],
})

const errors = ref<string[]>([])
const saving = ref(false)
const successMsg = ref('')

function uid(prefix: string) {
  return `${prefix}_${Math.random().toString(36).slice(2, 8)}`
}

function addModule() {
  const idx = form.modules.length + 1
  form.modules.push({
    id: uid('m'),
    title: `Chương ${idx}`,
    lessons: [{ id: uid('l'), title: `Bài ${idx}.1`, videoFile: null, videoPreview: '' }],
  })
}

function removeModule(index: number) {
  form.modules.splice(index, 1)
}

function addLesson(mod: ModuleDraft) {
  const lessonNo = mod.lessons.length + 1
  mod.lessons.push({ id: uid('l'), title: `Bài ${lessonNo}`, videoFile: null, videoPreview: '' })
}

function removeLesson(mod: ModuleDraft, index: number) {
  mod.lessons.splice(index, 1)
}

function fillSample() {
  form.title = 'Luyện thi Toán lớp 3 - Học kỳ 1'
  form.description = 'Ôn tập lý thuyết và bài tập trọng tâm, bám sát chương trình.'
  form.grade = 3
  form.subject = 'math'
  form.level = 'basic'
  form.status = 'published'
  form.thumbnailFile = null
  form.thumbnailPreview = 'https://picsum.photos/seed/course-sample/800/360'
  form.modules = [
    {
      id: uid('m'),
      title: 'Ôn số và phép tính',
      lessons: [
        { id: uid('l'), title: 'Cộng trừ trong phạm vi 1000', videoFile: null, videoPreview: '' },
        { id: uid('l'), title: 'Ôn bảng nhân chia', videoFile: null, videoPreview: '' },
      ],
    },
    {
      id: uid('m'),
      title: 'Hình học cơ bản',
      lessons: [
        { id: uid('l'), title: 'Đo độ dài đoạn thẳng', videoFile: null, videoPreview: '' },
        { id: uid('l'), title: 'Chu vi hình chữ nhật', videoFile: null, videoPreview: '' },
      ],
    },
    {
      id: uid('m'),
      title: 'Ứng dụng',
      lessons: [
        { id: uid('l'), title: 'Giải bài toán có lời văn', videoFile: null, videoPreview: '' },
      ],
    },
  ]
}

function validate() {
  const errs: string[] = []
  if (!form.title.trim()) errs.push('Nhập tên khoá học')
  if (!form.modules.length) errs.push('Thêm ít nhất 1 chương')

  form.modules.forEach((m, mi) => {
    if (!m.title.trim()) errs.push(`Chương ${mi + 1}: cần tên chương`)
    if (!m.lessons.length) errs.push(`Chương ${mi + 1}: cần ít nhất 1 bài học`)
    m.lessons.forEach((l, li) => {
      if (!l.title.trim()) errs.push(`Bài ${mi + 1}.${li + 1}: cần tên`)
      if (!l.videoFile && !l.videoPreview) errs.push(`Bài ${mi + 1}.${li + 1}: chọn file video`)
    })
  })

  errors.value = errs
  return !errs.length
}

function mapPayload(): Partial<CourseDetail> {
  return {
    title: form.title.trim(),
    description: form.description.trim() || undefined,
    grade: form.grade as any,
    subject: form.subject as any,
    level: form.level as any,
    status: form.status as any,
    thumbnail: form.thumbnailPreview || undefined,
    sections: form.modules.map((m, idx) => ({
      id: m.id,
      title: m.title.trim() || `Chương ${idx + 1}`,
      order: idx + 1,
      lessons: m.lessons.map((l, li) => ({
        id: l.id,
        title: l.title.trim() || `Bài ${idx + 1}.${li + 1}`,
        type: 'video',
        videoUrl: l.videoPreview || l.videoFile?.name || undefined,
        isPreview: li === 0,
      })),
    })),
  }
}

function onPickThumb(e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) {
    form.thumbnailFile = f
    form.thumbnailPreview = URL.createObjectURL(f)
  }
}

function onPickVideo(lesson: LessonDraft, e: Event) {
  const f = (e.target as HTMLInputElement).files?.[0]
  if (f) {
    lesson.videoFile = f
    lesson.videoPreview = URL.createObjectURL(f)
  }
}

async function submit() {
  successMsg.value = ''
  if (!validate() || saving.value) return
  saving.value = true
  try {
    await courseService.create(mapPayload())
    successMsg.value = 'Đã lưu khoá học (mock).'
    router.push('/teacher/courses')
  } catch (e: any) {
    errors.value = [e?.message || 'Không thể lưu khoá học']
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.card {
  @apply mb-5 rounded-2xl border border-slate-200 bg-white p-5 shadow-sm;
}
.section-title {
  @apply mb-3 text-lg font-semibold text-slate-800;
}
.section-head { @apply mb-2 flex items-center justify-between gap-3; }
.section-desc { @apply text-sm text-slate-500; }
.field {
  @apply flex flex-col gap-1;
}
.label {
  @apply text-sm font-medium text-slate-700;
}
.input {
  @apply w-full rounded-lg border border-slate-200 px-3 py-2 text-sm outline-none transition focus:border-sky-400 focus:ring-2 focus:ring-sky-100;
}
.input-file {
  @apply flex items-center gap-2 rounded-lg border border-slate-200 bg-slate-50 px-3 py-2 text-sm;
}
.input-file__btn {
  @apply inline-flex items-center rounded-md bg-sky-600 px-3 py-1 text-white text-xs font-semibold;
}
.input-file__text {
  @apply text-slate-600;
}
.thumb-preview { @apply mt-2; }
.thumb-img { @apply h-28 w-full max-w-sm rounded-lg object-cover border; }
.module {
  @apply mb-4 rounded-xl border border-slate-200 bg-slate-50 p-3;
}
.module-header {
  @apply mb-3 flex flex-wrap items-start gap-3;
}
.lesson-actions {
  @apply mb-2 flex items-center justify-between;
}
.lesson {
  @apply mb-3 flex flex-wrap items-center gap-3 rounded-lg border border-slate-200 bg-white p-3;
}
.empty {
  @apply rounded-lg border border-dashed border-slate-200 bg-slate-100 px-3 py-3 text-sm text-slate-500;
}
.empty.small {
  @apply py-2;
}
.page-head { @apply mb-5 flex flex-wrap items-center justify-between gap-3; }
.page-kicker { @apply text-sm text-slate-500; }
.page-title { @apply text-2xl font-semibold; }
.page-actions { @apply flex gap-2; }
.btn {
  @apply inline-flex items-center justify-center rounded-lg px-3 py-2 text-sm font-semibold transition;
}
.btn-primary { @apply bg-sky-600 text-white hover:bg-sky-700; }
.btn-secondary { @apply border border-sky-200 bg-white text-sky-700 hover:bg-sky-50; }
.btn-ghost {
  @apply rounded-lg px-2 py-1 text-sm font-semibold hover:bg-slate-100;
}
</style>
