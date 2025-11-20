<template>
  <div class="min-h-screen w-full bg-slate-50">
    <main class="mx-auto w-full max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <!-- Header -->
      <div
        class="mb-5 flex flex-col items-stretch justify-between gap-3 sm:flex-row sm:items-center"
      >
        <div class="flex items-center gap-3">
          <button
            type="button"
            class="flex h-9 w-9 items-center justify-center rounded-full border border-slate-200 bg-white text-slate-600 hover:bg-slate-50"
            @click="goBack"
          >
            ‹
          </button>
          <div>
            <p class="text-xs uppercase tracking-wide text-slate-400">Sửa khoá học</p>
            <h1 class="text-xl font-semibold sm:text-2xl">
              {{ course?.title || 'Đang tải…' }}
            </h1>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <button
            type="button"
            class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700 hover:bg-slate-50"
            @click="goToList"
          >
            Quay lại danh sách
          </button>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="space-y-4">
        <div class="h-40 w-full rounded-2xl bg-slate-200 animate-pulse" />
        <div class="h-4 w-1/2 rounded bg-slate-200 animate-pulse" />
        <div class="h-4 w-1/3 rounded bg-slate-200 animate-pulse" />
        <div class="h-32 w-full rounded-2xl bg-slate-200 animate-pulse" />
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
      >
        {{ error }}
      </div>

      <!-- Content -->
      <div v-else-if="course" class="space-y-6">
        <!-- Form chỉnh sửa -->
        <form class="grid grid-cols-1 gap-6 lg:grid-cols-[280px,1fr]" @submit.prevent="submit">
          <!-- Thumbnail & info ngắn -->
          <section class="space-y-4">
            <!-- Thumbnail -->
            <div
              class="h-48 w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 sm:h-56"
            >
              <img
                v-if="coverBlobUrl"
                :src="coverBlobUrl"
                :alt="f.title || 'Ảnh khoá học'"
                class="h-full w-full object-cover"
              />
              <div
                v-else
                class="flex h-full w-full items-center justify-center text-5xl text-slate-300"
              >
                🎓
              </div>
            </div>

            <!-- Upload ảnh bìa -->
            <div class="rounded-2xl border border-slate-200 bg-white p-4">
              <h2 class="mb-2 text-sm font-semibold text-slate-800">Ảnh khoá học</h2>
              <p class="mb-3 text-xs text-slate-500">
                Ảnh bìa hiển thị trong danh sách và trang chi tiết khoá học (tùy chọn).
              </p>

              <input
                ref="coverInput"
                type="file"
                accept="image/*"
                class="hidden"
                @change="onPickCover"
              />

              <div class="flex items-center gap-3">
                <button
                  type="button"
                  class="rounded-xl border border-slate-300 bg-white px-3 py-2 text-xs font-medium text-slate-700 hover:bg-slate-50"
                  @click="coverInput?.click()"
                >
                  Chọn ảnh bìa
                </button>

                <span v-if="coverFileName" class="text-xs text-slate-600">
                  {{ coverFileName }}
                </span>
                <span v-else class="text-xs text-slate-400">
                  Chưa chọn ảnh mới (giữ nguyên ảnh hiện tại).
                </span>
              </div>

              <p class="mt-2 text-[11px] text-slate-400">Hỗ trợ JPG/PNG, tối đa 2MB.</p>
              <p v-if="coverErr" class="mt-2 text-xs font-medium text-rose-600">
                {{ coverErr }}
              </p>
            </div>

            <!-- Thông tin nhanh -->
            <div class="rounded-2xl border border-slate-200 bg-white p-4 text-xs">
              <p class="font-semibold text-slate-700">Tóm tắt</p>
              <p class="mt-1 text-slate-500">
                Lớp:
                <span class="font-medium text-slate-700">
                  {{ f.grade || 'Chưa rõ' }}
                </span>
              </p>
              <p class="mt-1 text-slate-500">
                Môn:
                <span class="font-medium text-slate-700">
                  {{ f.subject || course.categories[0] || 'Chưa rõ' }}
                </span>
              </p>
              <p class="mt-1 text-slate-500">
                Số chương:
                <span class="font-medium text-slate-700">
                  {{ f.modules.length }}
                </span>
              </p>
            </div>
          </section>

          <!-- Form chi tiết -->
          <section class="space-y-5 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
            <!-- Tên khoá học -->
            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-800">
                Tên khoá học <span class="text-rose-600">*</span>
              </label>
              <input
                v-model.trim="f.title"
                type="text"
                class="w-full rounded-lg border px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                :class="titleErr ? 'border-rose-500 ring-rose-500' : 'border-slate-300'"
                placeholder="Ví dụ: Toán 5 (Hỗ trợ học bộ Cánh diều)"
                @input="titleErr = ''"
              />
              <p v-if="titleErr" class="mt-1 text-xs font-medium text-rose-600">
                {{ titleErr }}
              </p>
            </div>

            <!-- Môn & khối -->
            <div class="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <label class="mb-1 block text-sm font-semibold text-slate-800"> Môn học </label>
                <select
                  v-model="f.subject"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                >
                  <option value="">Chọn môn</option>
                  <option value="Toán">Toán</option>
                  <option value="Tiếng Việt">Tiếng Việt</option>
                  <option value="Tiếng Anh">Tiếng Anh</option>
                  <option value="Khoa học">Khoa học</option>
                  <option value="Lịch sử">Lịch sử</option>
                </select>
              </div>

              <div>
                <label class="mb-1 block text-sm font-semibold text-slate-800"> Khối lớp </label>
                <select
                  v-model="f.grade"
                  class="w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                >
                  <option value="1">Lớp 1</option>
                  <option value="2">Lớp 2</option>
                  <option value="3">Lớp 3</option>
                  <option value="4">Lớp 4</option>
                  <option value="5">Lớp 5</option>
                </select>
              </div>
            </div>

            <!-- Mô tả -->
            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-800"> Mô tả </label>
              <textarea
                v-model.trim="f.description"
                rows="4"
                class="w-full resize-y rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                placeholder="Mô tả chi tiết về khoá học..."
              ></textarea>
            </div>

            <!-- Tags -->
            <div>
              <label class="mb-1 block text-sm font-semibold text-slate-800">
                Tags
                <span class="text-xs font-normal text-slate-500">(phân cách bằng dấu phẩy)</span>
              </label>
              <input
                v-model="tagsInput"
                type="text"
                class="w-full rounded-lg border border-slate-300 px-3 py-2.5 text-sm outline-none transition focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                placeholder="Ví dụ: toan, lop 5, canh dieu"
                @input="updateTags"
              />
              <p class="mt-1 text-[11px] text-slate-500">
                Tags giúp học sinh tìm kiếm khoá học dễ dàng hơn.
              </p>
            </div>

            <!-- CHỈNH SỬA CHƯƠNG / BÀI HỌC -->
            <div class="mt-4 space-y-3 rounded-xl bg-slate-50 p-3 text-xs text-slate-600">
              <div class="mb-2 flex items-center justify-between gap-2">
                <div>
                  <p class="text-sm font-semibold text-slate-800">Chương học (modules)</p>
                  <p class="mt-1 text-xs text-slate-500">
                    Em có thể đổi tên chương / bài học, thêm hoặc xoá chương / bài. Nội dung chi
                    tiết bên trong bài (text, file, quiz, ...) giữ nguyên.
                  </p>
                </div>
                <button
                  type="button"
                  class="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 hover:bg-slate-100"
                  @click="addModule"
                >
                  + Thêm chương
                </button>
              </div>

              <div v-if="!f.modules.length" class="text-xs text-slate-500">
                Chưa có chương nào. Nhấn <b>Thêm chương</b> để bắt đầu.
              </div>

              <div v-else class="space-y-3">
                <div
                  v-for="(m, mIndex) in f.modules"
                  :key="m.id || mIndex"
                  class="rounded-lg border border-slate-200 bg-white p-3"
                >
                  <div class="mb-2 flex items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <span
                        class="flex h-6 w-6 items-center justify-center rounded-full bg-sky-100 text-[11px] font-semibold text-sky-700"
                      >
                        {{ mIndex + 1 }}
                      </span>
                      <input
                        v-model.trim="m.title"
                        type="text"
                        class="w-full rounded border border-slate-300 px-2 py-1.5 text-xs outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                        :placeholder="`Chương ${mIndex + 1}`"
                      />
                    </div>
                    <button
                      type="button"
                      class="text-xs text-rose-600 hover:text-rose-700"
                      @click="removeModule(mIndex)"
                    >
                      Xoá
                    </button>
                  </div>

                  <!-- Lessons -->
                  <div class="mt-2 space-y-2">
                    <div class="flex items-center justify-between gap-2">
                      <p class="text-[11px] font-semibold text-slate-700">
                        Bài học ({{ m.lessons.length }})
                      </p>
                      <button
                        type="button"
                        class="rounded border border-slate-300 bg-white px-2 py-1 text-[11px] text-slate-700 hover:bg-slate-50"
                        @click="addLesson(mIndex)"
                      >
                        + Thêm bài
                      </button>
                    </div>

                    <div v-if="!m.lessons.length" class="text-[11px] text-slate-500">
                      Chưa có bài học nào trong chương này.
                    </div>

                    <div v-else class="space-y-2">
                      <div
                        v-for="(lesson, lIndex) in m.lessons"
                        :key="lesson.id || lIndex"
                        class="flex items-center justify-between gap-2 rounded border border-slate-200 bg-slate-50 px-2 py-1.5"
                      >
                        <div class="flex flex-1 items-center gap-2">
                          <span
                            class="inline-flex h-5 min-w-[1.4rem] items-center justify-center rounded-full bg-slate-200 text-[10px] font-semibold text-slate-700"
                          >
                            B{{ lIndex + 1 }}
                          </span>
                          <div class="flex-1">
                            <input
                              v-model.trim="lesson.title"
                              type="text"
                              class="w-full rounded border border-slate-300 px-2 py-1 text-[11px] outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500"
                              :placeholder="`Bài ${lIndex + 1}`"
                            />
                            <p class="mt-0.5 text-[10px] text-slate-500">
                              {{ lesson.content_blocks?.length || 0 }} nội dung (text / video / file
                              / quiz ...)
                            </p>
                          </div>
                        </div>

                        <button
                          type="button"
                          class="text-[11px] text-rose-600 hover:text-rose-700"
                          @click="removeLesson(mIndex, lIndex)"
                        >
                          Xoá
                        </button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div
              class="mt-4 flex flex-wrap items-center justify-end gap-3 border-t border-slate-100 pt-4"
            >
              <button
                type="button"
                class="rounded-xl border border-slate-300 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
                @click="goBack"
              >
                Huỷ
              </button>
              <button
                type="submit"
                class="rounded-xl bg-sky-600 px-5 py-2 text-sm font-semibold text-white shadow-sm hover:bg-sky-700 disabled:cursor-not-allowed disabled:opacity-60"
                :disabled="submitting"
              >
                {{ submitting ? 'Đang lưu…' : 'Lưu thay đổi' }}
              </button>
            </div>
          </section>
        </form>
      </div>

      <!-- Không có course mà cũng không loading & không lỗi -->
      <div v-else class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
        Không tìm thấy dữ liệu khoá học.
      </div>

      <!-- Notification modal -->
      <transition
        enter-active-class="transition-opacity duration-150 ease-out"
        leave-active-class="transition-opacity duration-150 ease-in"
        enter-from-class="opacity-0"
        leave-to-class="opacity-0"
      >
        <div
          v-if="notification.open"
          class="fixed inset-0 z-50 grid place-items-center bg-slate-900/50 p-4"
          role="dialog"
          aria-modal="true"
          @click.self="notification.open = false"
        >
          <div
            class="w-full max-w-md rounded-xl border border-slate-200 bg-white p-6 shadow-2xl outline-none"
          >
            <div class="mb-4 flex items-center gap-3">
              <div
                :class="[
                  'p-2 rounded-full',
                  notification.type === 'success'
                    ? 'bg-green-100 text-green-600'
                    : 'bg-amber-100 text-amber-600',
                ]"
              >
                <span v-if="notification.type === 'success'">✓</span>
                <span v-else>⚠</span>
              </div>
              <h3 class="text-lg font-bold text-slate-800">
                {{ notification.title }}
              </h3>
            </div>

            <div class="mb-6">
              <p class="text-slate-700">{{ notification.message }}</p>
            </div>

            <div class="flex justify-end">
              <button
                type="button"
                class="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
                @click="notification.open = false"
              >
                OK
              </button>
            </div>
          </div>
        </div>
      </transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
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

// ================== TYPES ==================
interface Lesson {
  id?: string
  title: string
  position: number
  content_type: string
  published?: boolean
  content_blocks: any[]
}

interface Module {
  id?: string
  title: string
  position: number
  lessons: Lesson[]
}

interface CourseDetail {
  id: string
  title: string
  description: string
  grade: string | null
  image_url: string | null
  subject: string | null
  slug: string
  categories: string[]
  tags: string[]
  modules: Module[]
}

// ================== STATE ==================
const course = ref<CourseDetail | null>(null)
const loading = ref(false)
const error = ref('')

const submitting = ref(false)

// form state
const f = reactive<{
  title: string
  description: string
  grade: string
  subject: string
  tags: string[]
  modules: Module[]
}>({
  title: '',
  description: '',
  grade: '5',
  subject: '',
  tags: [],
  modules: [],
})

const titleErr = ref('')

// cover
const coverInput = ref<HTMLInputElement | null>(null)
const coverFileName = ref('')
const coverErr = ref('')
const coverBlobUrl = ref<string | null>(null)
const coverImageId = ref<string | null>(null)

// tags input
const tagsInput = ref('')

// notification
const notification = reactive({
  open: false,
  type: 'success' as 'success' | 'error',
  title: '',
  message: '',
})

// lưu blob url để revoke
const blobUrls = new Set<string>()

// ================== HELPERS ==================
const showNotification = (type: 'success' | 'error', title: string, message: string) => {
  notification.type = type
  notification.title = title
  notification.message = message
  notification.open = true
}

const updateTags = () => {
  f.tags = tagsInput.value
    .split(',')
    .map((t) => t.trim())
    .filter((t) => t.length > 0)
}

async function fetchBlobUrl(path: string): Promise<string | null> {
  try {
    const res = await axios.get(path, {
      responseType: 'blob',
      headers: {
        ...getAuthHeaders(),
      },
    })
    const url = URL.createObjectURL(res.data)
    blobUrls.add(url)
    return url
  } catch (e) {
    console.error('❌ Lỗi tải file blob:', path, e)
    return null
  }
}

// upload ảnh bìa
type MediaComponent = 'lesson_material' | 'course_thumbnail'

interface UploadMediaResponse {
  id: string
  original_filename: string
  uploaded_at: string
  status: string
  component: string
  url: string
}

async function uploadMedia(
  file: File,
  component: MediaComponent,
  contentTypeStr: string,
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
  })

  return data
}

// ================== FETCH COURSE ==================
async function fetchCourse() {
  const id = route.params.id
  if (!id) {
    error.value = 'Không tìm thấy ID khoá học trên URL.'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const { data } = await axios.get<CourseDetail>(`/api/content/instructor/courses/${id}/`, {
      headers: {
        ...getAuthHeaders(),
      },
    })

    course.value = data

    // map data -> form
    f.title = data.title || ''
    f.description = data.description || ''
    f.grade = data.grade || '5'
    f.subject = data.subject || data.categories[0] || ''
    f.tags = data.tags || []

    tagsInput.value = f.tags.join(', ')

    // clone modules để chỉnh sửa
    f.modules = (data.modules || []).map((m, mIndex) => ({
      id: m.id,
      title: m.title,
      position: m.position ?? mIndex,
      lessons: (m.lessons || []).map((l, lIndex) => ({
        id: l.id,
        title: l.title,
        position: l.position ?? lIndex,
        content_type: l.content_type,
        published: l.published,
        content_blocks: l.content_blocks || [],
      })),
    }))

    // cover blob
    if (data.image_url) {
      const url = await fetchBlobUrl(data.image_url)
      if (url) {
        coverBlobUrl.value = url
      }
    }
  } catch (e: any) {
    console.error('❌ Lỗi tải chi tiết khoá học:', e)
    error.value =
      e?.response?.data?.detail ||
      e?.message ||
      'Không thể tải chi tiết khoá học. Vui lòng thử lại.'
  } finally {
    loading.value = false
  }
}

// ================== COVER HANDLER ==================
const MAX_AVATAR_SIZE = 2 * 1024 * 1024
const OVER_LIMIT_MSG = 'File ảnh vượt quá dung lượng cho phép (2MB)'

const onPickCover = async (event: Event) => {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > MAX_AVATAR_SIZE) {
    coverErr.value = OVER_LIMIT_MSG
    coverFileName.value = ''
    return
  }

  coverErr.value = ''
  coverFileName.value = file.name

  // preview local
  if (coverBlobUrl.value) {
    URL.revokeObjectURL(coverBlobUrl.value)
  }
  const localUrl = URL.createObjectURL(file)
  coverBlobUrl.value = localUrl
  blobUrls.add(localUrl)

  try {
    const res = await uploadMedia(file, 'course_thumbnail', 'image')
    coverImageId.value = res.id
  } catch (err) {
    console.error('❌ Lỗi upload ảnh bìa:', err)
    coverImageId.value = null
    showNotification('error', 'Lỗi', 'Upload ảnh bìa thất bại. Vui lòng thử lại.')
  }
}

// ================== EDIT MODULES / LESSONS ==================
function addModule() {
  f.modules.push({
    title: '',
    position: f.modules.length,
    lessons: [],
  })
}

function removeModule(mIndex: number) {
  f.modules.splice(mIndex, 1)
  f.modules.forEach((m, idx) => {
    m.position = idx
  })
}

function addLesson(mIndex: number) {
  const mod = f.modules[mIndex]
  mod.lessons.push({
    title: '',
    position: mod.lessons.length,
    content_type: 'lesson',
    published: false,
    content_blocks: [],
  })
}

function removeLesson(mIndex: number, lIndex: number) {
  const mod = f.modules[mIndex]
  mod.lessons.splice(lIndex, 1)
  mod.lessons.forEach((l, idx) => {
    l.position = idx
  })
}

// ================== SUBMIT (PATCH) ==================
async function submit() {
  titleErr.value = ''
  if (!f.title || !f.title.trim()) {
    titleErr.value = 'Vui lòng nhập tên khoá học.'
    return
  }

  if (!course.value) return

  submitting.value = true
  try {
    const payload: any = {
      title: f.title,
      description: f.description,
      grade: f.grade,
      subject: f.subject || null,
      tags: f.tags,
      categories: f.subject ? [f.subject] : [],
      modules: f.modules,
    }

    // chỉ gửi image_id nếu user đã upload ảnh mới
    if (coverImageId.value) {
      payload.image_id = coverImageId.value
    }

    await axios.patch(`/api/content/instructor/courses/${course.value.id}/`, payload, {
      headers: {
        'Content-Type': 'application/json',
        ...getAuthHeaders(),
      },
    })

    showNotification('success', 'Thành công', 'Đã lưu thay đổi khoá học.')

    // cập nhật lại course local cho đồng bộ
    course.value = {
      ...course.value,
      title: f.title,
      description: f.description,
      grade: f.grade,
      subject: f.subject || null,
      categories: payload.categories,
      tags: [...f.tags],
      modules: JSON.parse(JSON.stringify(f.modules)),
    }
  } catch (e: any) {
    console.error('❌ Lỗi khi cập nhật khoá học:', e)
    showNotification(
      'error',
      'Lỗi',
      e?.response?.data?.detail ||
        e?.message ||
        'Có lỗi xảy ra khi lưu khoá học. Vui lòng thử lại.',
    )
  } finally {
    submitting.value = false
  }
}

// ================== NAV ==================
function goBack() {
  router.back()
}

function goToList() {
  router.push({ path: '/teacher/courses' })
}

// ================== INIT & CLEANUP ==================
onMounted(() => {
  fetchCourse()
})

onBeforeUnmount(() => {
  blobUrls.forEach((u) => URL.revokeObjectURL(u))
  blobUrls.clear()
})
</script>

<style scoped>
h1 {
  word-break: break-word;
}
</style>
