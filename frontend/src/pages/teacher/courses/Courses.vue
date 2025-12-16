<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10 md:py-8">
      <!-- Header -->
      <div class="mb-5 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
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
          <div
            class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2"
          >
            <svg
              viewBox="0 0 24 24"
              class="h-5 w-5 text-slate-400"
              fill="none"
              stroke="currentColor"
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

        <!-- Grade filter -->
        <div>
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
          <div class="flex-1 space-y-2">
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

      <!-- LIST -->
      <div v-else class="grid grid-cols-1 gap-4">
        <article
          v-for="c in filteredCourses"
          :key="c.id"
          class="flex flex-col gap-4 rounded-2xl border border-slate-200 bg-white p-4 hover:shadow-sm transition-shadow sm:flex-row sm:items-center"
        >
          <!-- Thumbnail -->
          <div class="h-40 w-full sm:h-20 sm:w-32 rounded-xl overflow-hidden bg-slate-100">
            <img
              v-if="c.thumbnail_url"
              :src="c.thumbnail_url"
              :alt="c.title"
              class="h-full w-full object-cover rounded-xl"
            />

            <div v-else class="flex h-full items-center justify-center text-3xl text-slate-300">
              🎓
            </div>
          </div>

          <!-- Content -->
          <div class="min-w-0 flex-1">
            <div class="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-3">
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

            <p class="mt-1 text-sm text-slate-500 line-clamp-2">
              {{ c.short_description || 'Chưa có mô tả cho khoá học này.' }}
            </p>

            <div class="mt-2 flex flex-wrap items-center gap-1.5">
              <span
                v-if="c.subject"
                class="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700"
              >
                {{ c.subject.title }}
              </span>

              <span
                v-else-if="c.categories && c.categories.length"
                class="rounded-full bg-emerald-50 px-2 py-0.5 text-[11px] font-medium text-emerald-700"
              >
                {{ c.categories[0].name }}
              </span>

              <span
                v-for="tag in c.tags"
                :key="tag.id"
                class="rounded-full bg-slate-100 px-2 py-0.5 text-[11px] text-slate-700"
              >
                #{{ tag.name }}
              </span>
            </div>

            <div class="mt-2 text-xs text-slate-500">{{ c.stats.total_modules }} chương học</div>
          </div>

          <!-- Actions -->
          <div class="grid grid-cols-3 gap-2 sm:flex sm:shrink-0">
            <button
              class="rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              @click="viewDetail(c)"
            >
              Chi tiết
            </button>

            <button
              class="rounded-xl bg-sky-600 px-3 py-2 text-sm font-semibold text-white hover:bg-sky-700"
              @click="editCourse(c)"
            >
              Sửa
            </button>

            <button
              class="rounded-xl border border-rose-200 bg-rose-50 px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-100"
              @click="openDeleteModal(c)"
            >
              Xoá
            </button>
          </div>
        </article>
      </div>
    </main>

    <!-- 🔥 POPUP XÓA (CÓ ANIMATION) -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="deleteModal.open"
        class="fixed inset-0 z-40 bg-black/40 flex items-center justify-center"
      >
        <div class="bg-white p-5 rounded-xl shadow-xl w-full max-w-md">
          <h2 class="font-semibold text-lg">Xoá khoá học?</h2>
          <p class="text-sm text-slate-600 mt-1">
            Bạn có chắc muốn xoá khóa học
            <span class="font-semibold">"{{ deleteModal.course?.title }}"</span>?
          </p>

          <div class="flex justify-end gap-2 mt-4">
            <button
              class="px-4 py-2 rounded-xl border"
              @click="closeDeleteModal"
              :disabled="deletingId === deleteModal.course?.id"
            >
              Huỷ
            </button>

            <button
              class="px-4 py-2 rounded-xl bg-rose-600 text-white"
              @click="confirmDelete"
              :disabled="deletingId === deleteModal.course?.id"
            >
              {{ deletingId === deleteModal.course?.id ? 'Đang xoá…' : 'Xoá' }}
            </button>
          </div>
        </div>
      </div>
    </transition>

    <!-- 🔥 POPUP THÔNG BÁO (CÓ ANIMATION) -->
    <!-- POPUP THÔNG BÁO -->
    <transition
      enter-active-class="transition duration-200 ease-out"
      enter-from-class="opacity-0 scale-90"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition duration-150 ease-in"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-90"
    >
      <div
        v-if="notificationModal.open"
        class="fixed inset-0 z-50 bg-black/40 flex items-center justify-center"
      >
        <div class="bg-white p-6 rounded-xl shadow-xl w-full max-w-md">
          <div class="flex items-center gap-3 mb-3">
            <div
              :class="[
                'p-2 rounded-full',
                notificationModal.type === 'success'
                  ? 'bg-green-100 text-green-600'
                  : 'bg-amber-100 text-amber-600',
              ]"
            >
              {{ notificationModal.type === 'success' ? '✓' : '⚠' }}
            </div>

            <h3 class="text-lg font-bold text-slate-800">
              {{ notificationModal.title }}
            </h3>
          </div>

          <p class="text-slate-700 mb-4">
            {{ notificationModal.message }}
          </p>

          <div class="flex justify-end">
            <button
              class="rounded-xl bg-sky-600 px-4 py-2 text-sm font-semibold text-white hover:bg-sky-700"
              @click="handleNotificationOk"
            >
              OK
            </button>
          </div>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import { useRouter } from 'vue-router'

const router = useRouter()

/* ================= AUTH ================= */
const getAuthHeaders = () => {
  const token = localStorage.getItem('access')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/* ============== INTERFACE ============== */
interface Subject {
  id: string
  title: string
  slug: string
}
interface Tag {
  id: string
  name: string
  slug: string
}

interface CourseItem {
  id: string
  title: string
  slug: string
  short_description: string | null
  thumbnail_url: string | null
  grade: string | null
  subject: Subject | null
  tags: Tag[]
  categories?: { id: string; name: string }[]
  stats: { total_modules: number }
}

/* ============== STATE ============== */
const courses = ref<CourseItem[]>([])
const search = ref('')
const gradeFilter = ref('')
const loading = ref(false)
const error = ref('')

/* POPUP DELETE */
const deleteModal = reactive({
  open: false,
  course: null as CourseItem | null,
})
const deletingId = ref<string | null>(null)

/* POPUP NOTIFICATION */
const notificationModal = reactive({
  open: false,
  type: 'success' as 'success' | 'error',
  title: '',
  message: '',
})

function showNotification(type: 'success' | 'error', title: string, message: string) {
  notificationModal.type = type
  notificationModal.title = title
  notificationModal.message = message
  notificationModal.open = true
}

/* ============== FETCH ============== */
async function fetchCourses() {
  loading.value = true
  try {
    const { data } = await axios.get('/api/content/instructor/courses/', {
      headers: getAuthHeaders(),
    })
    courses.value = data || []
  } catch (e: any) {
    error.value = e?.response?.data?.detail || 'Không thể tải danh sách khoá học.'
  } finally {
    loading.value = false
  }
}
onMounted(fetchCourses)

/* ============== FILTERING ============== */
const normalize = (s: string) =>
  s
    .toLowerCase()
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')

const filteredCourses = computed(() => {
  let list = [...courses.value]
  if (gradeFilter.value) list = list.filter((c) => c.grade === gradeFilter.value)

  const kw = normalize(search.value)
  if (kw) {
    const parts = kw.split(/\s+/).filter(Boolean)

    list = list.filter((c) => {
      const tokens = [
        normalize(c.title),
        normalize(c.short_description || ''),
        ...c.tags.map((t) => normalize(t.name)),
      ]
      return parts.every((p) => tokens.some((t) => t.includes(p)))
    })
  }
  return list.sort((a, b) => a.title.localeCompare(b.title, 'vi'))
})

/* ============== NAVIGATION ============== */
function createCourse() {
  router.push('/teacher/courses/new')
}
function viewDetail(c: CourseItem) {
  router.push(`/teacher/courses/${c.id}`)
}
function editCourse(c: CourseItem) {
  router.push(`/teacher/courses/${c.id}/edit`)
}

/* ============== DELETE ============== */
function openDeleteModal(course: CourseItem) {
  deleteModal.course = course
  deleteModal.open = true
}

function closeDeleteModal() {
  if (deletingId.value) return
  deleteModal.open = false
  deleteModal.course = null
}

async function confirmDelete() {
  if (!deleteModal.course) return

  const course = deleteModal.course
  deletingId.value = course.id

  try {
    await axios.delete(`/api/content/instructor/courses/${course.id}/`, {
      headers: getAuthHeaders(),
    })

    courses.value = courses.value.filter((c) => c.id !== course.id)

    closeDeleteModal()
    showNotification('success', 'Thành công', 'Đã xoá khoá học thành công.')
  } catch (e) {
    showNotification('error', 'Lỗi', 'Không thể xoá khoá học.')
  } finally {
    deletingId.value = null
  }
}
function handleNotificationOk() {
  // tắt popup thông báo
  notificationModal.open = false

  // đảm bảo tắt luôn popup xoá (nếu vì lý do gì đó vẫn còn open)
  deleteModal.open = false
  deleteModal.course = null
  deletingId.value = null
}
</script>
