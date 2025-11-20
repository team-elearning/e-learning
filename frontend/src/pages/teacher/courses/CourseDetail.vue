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
            <p class="text-xs uppercase tracking-wide text-slate-400">Chi tiết khoá học</p>
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
          <button
            v-if="course"
            type="button"
            class="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
            @click="editCourse"
          >
            Sửa khoá học
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
        <!-- Top info -->
        <section class="grid grid-cols-1 gap-4 lg:grid-cols-[280px,1fr]">
          <!-- Thumbnail -->
          <div
            class="h-48 w-full overflow-hidden rounded-2xl border border-slate-200 bg-slate-100 sm:h-56"
          >
            <img
              v-if="coverBlobUrl"
              :src="coverBlobUrl"
              :alt="course.title"
              class="h-full w-full object-cover"
            />
            <div
              v-else
              class="flex h-full w-full items-center justify-center text-5xl text-slate-300"
            >
              🎓
            </div>
          </div>

          <!-- Meta -->
          <div class="rounded-2xl border border-slate-200 bg-white p-4 sm:p-5">
            <h2 class="mb-2 text-lg font-semibold">Thông tin chung</h2>

            <p class="text-sm text-slate-600">
              {{ course.description || 'Chưa có mô tả cho khoá học này.' }}
            </p>

            <div class="mt-4 flex flex-wrap items-center gap-2 text-xs">
              <span
                v-if="course.grade"
                class="rounded-full bg-sky-50 px-2.5 py-1 font-medium text-sky-700"
              >
                Lớp {{ course.grade }}
              </span>

              <span
                v-for="cat in course.categories"
                :key="cat"
                class="rounded-full bg-emerald-50 px-2.5 py-1 font-medium text-emerald-700"
              >
                {{ cat }}
              </span>

              <span
                v-for="tag in course.tags"
                :key="tag"
                class="rounded-full bg-slate-100 px-2 py-1 text-slate-700"
              >
                #{{ tag }}
              </span>
            </div>

            <p class="mt-3 text-xs text-slate-500">{{ course.modules?.length || 0 }} chương học</p>
          </div>
        </section>

        <!-- Modules & lessons -->
        <section class="space-y-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-5 lg:p-6">
          <div class="flex items-center justify-between gap-3">
            <h2 class="text-lg font-semibold text-slate-800">Nội dung khoá học</h2>
          </div>

          <div v-if="!course.modules || course.modules.length === 0" class="text-sm text-slate-500">
            Chưa có chương học nào trong khoá học này.
          </div>

          <div v-else class="space-y-4">
            <!-- Module -->
            <div
              v-for="(m, mIndex) in course.modules"
              :key="m.id || mIndex"
              class="rounded-xl border border-slate-200 bg-slate-50 p-4"
            >
              <div class="mb-3 flex flex-wrap items-center justify-between gap-2">
                <div class="flex items-center gap-2">
                  <span
                    class="flex h-7 w-7 items-center justify-center rounded-full bg-sky-100 text-xs font-semibold text-sky-700"
                  >
                    {{ mIndex + 1 }}
                  </span>
                  <div>
                    <p class="text-sm font-semibold text-slate-800">
                      {{ m.title || `Chương ${mIndex + 1}` }}
                    </p>
                    <p class="text-xs text-slate-500">{{ m.lessons?.length || 0 }} bài học</p>
                  </div>
                </div>
              </div>

              <!-- Lessons -->
              <div class="space-y-3">
                <div
                  v-for="(lesson, lIndex) in m.lessons"
                  :key="lesson.id || lIndex"
                  class="rounded-lg border border-slate-200 bg-white p-3"
                >
                  <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
                    <div class="flex items-center gap-2">
                      <span
                        class="inline-flex h-6 min-w-[1.5rem] items-center justify-center rounded-full bg-slate-100 text-[11px] font-semibold text-slate-700"
                      >
                        B{{ lIndex + 1 }}
                      </span>
                      <p class="text-sm font-medium text-slate-800">
                        {{ lesson.title || `Bài ${lIndex + 1}` }}
                      </p>
                    </div>
                  </div>

                  <!-- Content blocks -->
                  <div
                    v-if="lesson.content_blocks && lesson.content_blocks.length"
                    class="space-y-3"
                  >
                    <div
                      v-for="(b, bIndex) in lesson.content_blocks"
                      :key="b.id || bIndex"
                      class="rounded-lg border border-slate-100 bg-slate-50 p-3 text-sm"
                    >
                      <div class="mb-2 flex items-center justify-between">
                        <div class="flex items-center gap-2 text-[11px] uppercase tracking-wide">
                          <span class="font-semibold text-slate-500"> Phần {{ bIndex + 1 }} </span>
                          <span class="text-slate-400">•</span>
                          <span class="font-medium text-slate-500">
                            {{ blockTypeLabel(b.type) }}
                          </span>
                        </div>
                      </div>

                      <!-- TEXT -->
                      <div v-if="b.type === 'text'">
                        <p class="whitespace-pre-wrap text-sm text-slate-700">
                          {{ b.payload?.text }}
                        </p>
                      </div>

                      <!-- IMAGE -->
                      <div v-else-if="b.type === 'image'" class="space-y-2">
                        <div
                          class="flex max-h-72 w-full items-center justify-center overflow-hidden rounded-lg bg-slate-100"
                        >
                          <img
                            v-if="b.payload?._image_blob_url"
                            :src="b.payload._image_blob_url"
                            :alt="b.payload?.caption || 'Hình ảnh bài học'"
                            class="h-full w-full object-contain"
                          />
                          <div
                            v-else
                            class="flex h-32 w-full items-center justify-center text-slate-400"
                          >
                            Không có ảnh
                          </div>
                        </div>
                        <p v-if="b.payload?.caption" class="text-xs text-slate-500">
                          {{ b.payload.caption }}
                        </p>
                      </div>

                      <!-- VIDEO -->
                      <div v-else-if="b.type === 'video'" class="space-y-2">
                        <video
                          v-if="b.payload?._video_blob_url"
                          :src="b.payload._video_blob_url"
                          controls
                          class="w-full max-h-72 rounded-lg bg-black"
                        ></video>
                        <p v-else class="text-xs text-slate-500">Không tìm thấy video.</p>
                      </div>

                      <!-- PDF / DOCX -->
                      <div v-else-if="b.type === 'pdf' || b.type === 'docx'" class="space-y-2">
                        <div
                          class="flex items-center justify-between gap-2 rounded-md bg-white px-3 py-2 text-xs"
                        >
                          <div class="flex items-center gap-2">
                            <span class="text-lg">
                              {{ b.type === 'pdf' ? '📄' : '📘' }}
                            </span>
                            <div>
                              <p class="font-medium text-slate-800">
                                {{ b.payload?.filename || 'Tài liệu' }}
                              </p>
                              <p class="text-[11px] text-slate-500">
                                {{ b.type.toUpperCase() }}
                              </p>
                            </div>
                          </div>

                          <div class="flex items-center gap-2">
                            <!-- Xem trực tiếp (PDF: iframe, DOCX: note + tải) -->
                            <button
                              v-if="b.payload?._file_blob_url || b.payload?.file_url"
                              type="button"
                              class="inline-flex items-center gap-1 rounded-md border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 hover:bg-slate-50"
                              @click="openDocViewer(b)"
                            >
                              Xem trực tiếp
                            </button>

                            <!-- Mở tab mới / tải về thô -->
                            <a
                              v-if="b.payload?.file_url"
                              :href="b.payload.file_url"
                              target="_blank"
                              rel="noopener noreferrer"
                              class="inline-flex items-center gap-1 text-xs font-medium text-sky-700 hover:underline"
                            >
                              Mở tài liệu
                              <span>↗</span>
                            </a>
                            <span v-else class="text-[11px] text-slate-400"> Không có file </span>
                          </div>
                        </div>
                      </div>

                      <!-- QUIZ -->
                      <div v-else-if="b.type === 'quiz'" class="space-y-3">
                        <p class="text-sm font-semibold text-slate-800">
                          {{ b.payload?.title || 'Bài kiểm tra' }}
                        </p>
                        <p v-if="b.payload?.time_limit" class="text-xs text-slate-500">
                          Thời gian làm bài: {{ b.payload.time_limit }}
                        </p>

                        <div
                          v-if="b.payload?.questions && b.payload.questions.length"
                          class="space-y-2"
                        >
                          <div
                            v-for="(q, qIndex) in b.payload.questions"
                            :key="qIndex"
                            class="rounded-md bg-white p-2 text-xs"
                          >
                            <p class="font-medium text-slate-800">
                              Câu {{ qIndex + 1 }}.
                              {{ q.prompt?.text }}
                            </p>
                            <p class="mt-1 text-[11px] text-slate-500">
                              Loại: {{ questionTypeLabel(q.type) }}
                            </p>
                          </div>
                        </div>

                        <p v-else class="text-xs text-slate-500">Chưa có câu hỏi.</p>
                      </div>

                      <!-- OTHER / UNKNOWN -->
                      <div v-else class="text-xs text-slate-500">
                        Kiểu nội dung: {{ b.type }} (chưa hỗ trợ hiển thị chi tiết).
                      </div>
                    </div>
                  </div>

                  <p v-else class="text-xs text-slate-500">Bài học này chưa có nội dung.</p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </div>

      <!-- Không có course mà cũng không loading & không lỗi -->
      <div v-else class="rounded-2xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
        Không tìm thấy dữ liệu khoá học.
      </div>

      <!-- ========= DOC VIEWER MODAL ========= -->
      <div
        v-if="docViewerOpen && docViewerUrl"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-3"
      >
        <div class="flex h-[90vh] w-full max-w-5xl flex-col overflow-hidden rounded-2xl bg-white">
          <div class="flex items-center justify-between border-b border-slate-200 px-4 py-2">
            <p class="text-sm font-semibold text-slate-800">
              Xem tài liệu {{ docViewerType?.toUpperCase() }}
            </p>
            <button
              type="button"
              class="rounded-full p-1 text-slate-500 hover:bg-slate-100"
              @click="closeDocViewer"
            >
              ✕
            </button>
          </div>

          <div class="flex-1 bg-slate-100">
            <!-- PDF: iframe hiển thị trực tiếp -->
            <iframe
              v-if="docViewerType === 'pdf'"
              :src="docViewerUrl"
              class="h-full w-full"
            ></iframe>

            <!-- DOCX: thông báo + nút tải -->
            <div
              v-else-if="docViewerType === 'docx'"
              class="flex h-full flex-col items-center justify-center gap-3 px-4 text-center text-sm text-slate-600"
            >
              <p>Trình duyệt không hỗ trợ xem DOCX trực tiếp.</p>
              <p>Bạn có thể tải file về để mở bằng Word/Office.</p>
              <a
                :href="docViewerUrl"
                target="_blank"
                rel="noopener noreferrer"
                class="inline-flex items-center gap-1 rounded-md bg-sky-600 px-3 py-1.5 text-xs font-medium text-white hover:bg-sky-700"
              >
                Tải tài liệu
              </a>
            </div>
          </div>
        </div>
      </div>
      <!-- ========= END DOC VIEWER MODAL ========= -->
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'
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
interface ContentBlock {
  id?: string
  type: string
  position: number
  payload: any
}

interface Lesson {
  id?: string
  title: string
  position: number
  content_type: string
  published?: boolean
  content_blocks: ContentBlock[]
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

const coverBlobUrl = ref<string | null>(null)

// lưu tất cả blob urls để revoke khi unmount
const blobUrls = new Set<string>()

// Viewer tài liệu (PDF / DOCX)
const docViewerOpen = ref(false)
const docViewerUrl = ref<string | null>(null)
const docViewerType = ref<'pdf' | 'docx' | null>(null)

// ================== HELPERS ==================
function blockTypeLabel(type: string) {
  switch (type) {
    case 'text':
      return 'Văn bản'
    case 'image':
      return 'Hình ảnh'
    case 'video':
      return 'Video'
    case 'pdf':
      return 'PDF'
    case 'docx':
      return 'DOCX'
    case 'quiz':
      return 'Bài kiểm tra'
    default:
      return type
  }
}

function questionTypeLabel(type: string) {
  switch (type) {
    case 'multiple_choice_single':
      return 'Chọn một đáp án'
    case 'multiple_choice_multi':
      return 'Chọn nhiều đáp án'
    case 'true_false':
      return 'Đúng / Sai'
    case 'fill_in_the_blank':
      return 'Điền vào chỗ trống'
    default:
      return type
  }
}

// giống list khoá học: call API lấy blob + Authorization
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

// mở viewer tài liệu
function openDocViewer(block: ContentBlock) {
  const blobUrl = block.payload?._file_blob_url
  const rawUrl = block.payload?.file_url

  if (blobUrl) {
    docViewerUrl.value = blobUrl
  } else if (rawUrl) {
    docViewerUrl.value = rawUrl
  } else {
    docViewerUrl.value = null
  }

  docViewerType.value = (block.type === 'pdf' || block.type === 'docx' ? block.type : null) as
    | 'pdf'
    | 'docx'
    | null

  if (docViewerUrl.value && docViewerType.value) {
    docViewerOpen.value = true
  }
}

function closeDocViewer() {
  docViewerOpen.value = false
  docViewerUrl.value = null
  docViewerType.value = null
}

// ================== FETCH ==================
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

    // cover
    if (course.value.image_url) {
      fetchBlobUrl(course.value.image_url).then((url) => {
        if (url) coverBlobUrl.value = url
      })
    }

    // images, videos, pdf, docx trong content blocks
    course.value.modules.forEach((m) => {
      m.lessons.forEach((lesson) => {
        lesson.content_blocks.forEach((b) => {
          if (b.type === 'image' && b.payload?.image_url) {
            fetchBlobUrl(b.payload.image_url).then((url) => {
              if (url) b.payload._image_blob_url = url
            })
          }
          if (b.type === 'video' && b.payload?.video_url) {
            fetchBlobUrl(b.payload.video_url).then((url) => {
              if (url) b.payload._video_blob_url = url
            })
          }
          if ((b.type === 'pdf' || b.type === 'docx') && b.payload?.file_url) {
            fetchBlobUrl(b.payload.file_url).then((url) => {
              if (url) b.payload._file_blob_url = url
            })
          }
        })
      })
    })
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

// ================== NAV ==================
function goBack() {
  router.back()
}

function goToList() {
  router.push({ path: '/teacher/courses' })
}

function editCourse() {
  if (!course.value) return
  router.push({ path: `/teacher/courses/${course.value.id}/edit` })
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
