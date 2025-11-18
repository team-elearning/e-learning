<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <!-- Header -->
      <div
        class="mb-5 flex flex-col items-stretch justify-between gap-3 sm:flex-row sm:items-center"
      >
        <h1 class="text-xl font-semibold sm:text-2xl">Khoá học</h1>
        <button
          class="inline-flex items-center justify-center rounded-xl bg-sky-600 px-4 py-2 font-semibold text-white hover:bg-sky-700"
          @click="createCourse"
        >
          + Tạo khoá học
        </button>
      </div>

      <!-- Tools -->
      <div class="mb-5 grid grid-cols-1 gap-3 md:grid-cols-3">
        <!-- Search -->
        <div class="md:col-span-2">
          <label class="sr-only">Tìm kiếm</label>
          <div
            class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2"
          >
            <svg
              viewBox="0 0 24 24"
              class="h-5 w-5 text-slate-400"
              fill="none"
              stroke="currentColor"
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="8" stroke-width="2" />
              <path d="M21 21l-4.3-4.3" stroke-width="2" />
            </svg>
            <input
              v-model.trim="search"
              type="text"
              placeholder="Tìm khoá học…"
              class="w-full bg-transparent outline-none placeholder:text-slate-400"
            />
          </div>
        </div>

        <!-- Filter khối -->
        <div class="grid grid-cols-1 gap-2 sm:grid-cols-2">
          <select
            v-model="gradeFilter"
            class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm"
          >
            <option value="">Tất cả khối</option>
            <option value="1">Lớp 1</option>
            <option value="2">Lớp 2</option>
            <option value="3">Lớp 3</option>
            <option value="4">Lớp 4</option>
            <option value="5">Lớp 5</option>
          </select>
        </div>
      </div>

      <!-- Loading -->
      <div v-if="loading" class="grid grid-cols-1 gap-4">
        <div
          v-for="i in 4"
          :key="i"
          class="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 sm:flex-row sm:items-center"
        >
          <div class="h-40 w-full rounded-xl bg-slate-200 animate-pulse sm:h-20 sm:w-32" />
          <div class="min-w-0 flex-1 space-y-2">
            <div class="h-4 w-2/3 rounded bg-slate-200 animate-pulse" />
            <div class="h-3 w-1/2 rounded bg-slate-200 animate-pulse" />
          </div>
          <div class="h-10 w-full rounded bg-slate-200 animate-pulse sm:h-8 sm:w-24" />
        </div>
      </div>

      <!-- Error -->
      <div
        v-else-if="error"
        class="mt-6 rounded-2xl border border-rose-200 bg-rose-50 p-4 text-sm text-rose-700"
      >
        {{ error }}
      </div>

      <!-- Empty -->
      <div v-else-if="filteredCourses.length === 0" class="mt-10 text-center text-slate-500">
        Không có khoá học phù hợp.
      </div>

      <!-- List -->
      <div v-else class="grid grid-cols-1 gap-4">
        <article
          v-for="c in filteredCourses"
          :key="String(c.id)"
          class="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 transition-shadow hover:shadow-sm sm:flex-row sm:items-center"
        >
          <!-- Thumbnail -->
          <div
            class="h-40 w-full rounded-xl bg-slate-100 sm:h-20 sm:w-32 sm:shrink-0 overflow-hidden"
          >
            <img
              v-if="thumbnailUrlMap[c.id]"
              :src="thumbnailUrlMap[c.id]"
              :alt="c.title"
              class="h-40 w-full rounded-xl object-cover sm:h-20 sm:w-32 sm:shrink-0"
            />
            <div
              v-else
              class="flex h-full w-full items-center justify-center text-3xl text-slate-300"
            >
              🎓
            </div>
          </div>

          <!-- Content -->
          <div class="min-w-0 flex-1">
            <div class="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-3">
              <h3
                class="truncate font-semibold cursor-pointer hover:underline"
                :title="c.title"
                @click="viewDetail(c)"
              >
                {{ c.title }}
              </h3>

              <span
                v-if="c.grade"
                class="w-max rounded-full bg-sky-50 px-2 py-0.5 text-xs font-medium text-sky-700"
              >
                Lớp {{ c.grade }}
              </span>
            </div>

            <p class="mt-1 line-clamp-2 text-sm text-slate-500">
              {{ c.description || 'Chưa có mô tả cho khoá học này.' }}
            </p>

            <div class="mt-2 flex flex-wrap items-center gap-1.5">
              <span
                v-if="c.subject"
                class="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700"
              >
                {{ c.subject }}
              </span>

              <span
                v-for="tag in c.tags"
                :key="tag"
                class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-700"
              >
                #{{ tag }}
              </span>
            </div>

            <div class="mt-2 text-xs text-slate-500">{{ c.modules?.length || 0 }} chương học</div>
          </div>

          <!-- Actions -->
          <div class="grid grid-cols-2 gap-2 sm:flex sm:shrink-0">
            <button
              class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50 w-full sm:w-auto"
              @click="viewDetail(c)"
            >
              Chi tiết
            </button>
            <button
              class="inline-flex items-center justify-center rounded-xl bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-700 w-full sm:w-auto"
              @click="editCourse(c)"
            >
              Sửa
            </button>
          </div>
        </article>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
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

interface CourseItem {
  id: string
  title: string
  description: string
  grade: string | null
  image_url: string | null
  subject: string | null
  slug: string
  categories: string[]
  tags: string[]
  modules: any[]
}

const courses = ref<CourseItem[]>([])
const loading = ref(false)
const error = ref('')

const search = ref('')
const gradeFilter = ref('')

// map courseId -> blob URL (thumbnail)
const thumbnailUrlMap = ref<Record<string, string>>({})

// ========== LOAD THUMBNAIL GIỐNG CALL KHÓA HỌC ==========
async function loadThumbnail(course: CourseItem) {
  if (!course.image_url) return
  if (thumbnailUrlMap.value[course.id]) return

  try {
    const res = await axios.get(course.image_url, {
      responseType: 'blob',
      headers: {
        ...getAuthHeaders(),
      },
    })

    const blobUrl = URL.createObjectURL(res.data)
    thumbnailUrlMap.value[course.id] = blobUrl
  } catch (e) {
    console.error('❌ Lỗi tải thumbnail cho khoá học', course.id, e)
  }
}

// ========== FETCH DATA ==========
const fetchCourses = async () => {
  loading.value = true
  error.value = ''

  try {
    const { data } = await axios.get<CourseItem[]>('/api/content/instructor/courses/', {
      headers: {
        ...getAuthHeaders(),
      },
    })

    courses.value = data || []

    // clear blob cũ để tránh leak
    Object.values(thumbnailUrlMap.value).forEach((u) => URL.revokeObjectURL(u))
    thumbnailUrlMap.value = {}

    // tải thumbnail cho các khoá có image_url (song song)
    const withImage = courses.value.filter((c) => c.image_url)
    await Promise.all(withImage.map((c) => loadThumbnail(c)))
  } catch (err: any) {
    console.error('❌ Lỗi tải danh sách khoá học:', err)
    error.value =
      err?.response?.data?.detail ||
      err?.message ||
      'Không thể tải danh sách khoá học. Vui lòng thử lại.'
    courses.value = []
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCourses()
})

// ========== FILTERED COURSES ==========
const filteredCourses = computed(() => {
  let list = [...courses.value]

  if (gradeFilter.value) {
    list = list.filter((c) => c.grade === gradeFilter.value)
  }

  const kw = search.value.trim().toLowerCase()
  if (kw) {
    list = list.filter((c) => {
      const inTitle = c.title?.toLowerCase().includes(kw)
      const inDesc = c.description?.toLowerCase().includes(kw)
      const inSubject = c.subject?.toLowerCase().includes(kw)
      const inTags = (c.tags || []).some((t) => t.toLowerCase().includes(kw))
      return inTitle || inDesc || inSubject || inTags
    })
  }

  // sort theo tên
  list.sort((a, b) => a.title.localeCompare(b.title, 'vi'))
  return list
})

// ========== NAVIGATION ==========
function createCourse() {
  router.push({ path: '/teacher/courses/new' })
}

const viewDetail = (course: CourseItem) => {
  router.push({ path: `/teacher/courses/${course.id}` })
}

const editCourse = (course: CourseItem) => {
  router.push({ path: `/teacher/courses/${course.id}/edit` })
}

// cleanup blob URL
onBeforeUnmount(() => {
  Object.values(thumbnailUrlMap.value).forEach((u) => URL.revokeObjectURL(u))
})
</script>

<style scoped>
:host,
.min-h-screen {
  overflow-x: hidden;
}
h3 {
  word-break: break-word;
}
@media (hover: none) {
  .hover\:shadow-sm:hover {
    box-shadow: none;
  }
  .hover\:bg-slate-50:hover {
    background: inherit;
  }
}
</style>
