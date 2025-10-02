<!-- src/pages/teacher/courses/CourseDetail.vue -->
<template>
  <div class="mx-auto max-w-5xl p-6">
    <!-- Loading -->
    <div v-if="loading" class="grid grid-cols-1 gap-6 md:grid-cols-3">
      <div class="md:col-span-1 h-56 rounded-2xl bg-slate-200 animate-pulse" />
      <div class="md:col-span-2 rounded-2xl border bg-white p-4">
        <div class="h-4 w-40 bg-slate-200 rounded mb-4 animate-pulse" />
        <div class="grid grid-cols-3 gap-3 text-center">
          <div class="rounded-xl bg-slate-100 p-6 animate-pulse" />
          <div class="rounded-xl bg-slate-100 p-6 animate-pulse" />
          <div class="rounded-xl bg-slate-100 p-6 animate-pulse" />
        </div>
      </div>
    </div>

    <!-- Error -->
    <div v-else-if="err" class="rounded-xl border border-rose-200 bg-rose-50 p-4 text-rose-700">
      {{ err }}
    </div>

    <!-- Content -->
    <template v-else-if="c">
      <div class="mb-4 flex items-center justify-between">
        <h1 class="text-2xl font-semibold">{{ c.title }}</h1>
        <div class="flex gap-2">
          <button
            class="rounded-xl bg-sky-600 px-4 py-2 font-semibold text-white"
            @click="goEdit(c.id)"
          >
            Sửa
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 gap-6 md:grid-cols-3">
        <!-- Ảnh cover tối ưu + spinner loading + fallback lỗi -->
        <div class="md:col-span-1">
          <div class="relative w-full overflow-hidden rounded-2xl" style="aspect-ratio: 16 / 9">
            <!-- Overlay: LOADING -->
            <div
              v-if="!imgLoaded && !imgError"
              class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-200/60"
              aria-live="polite"
              aria-busy="true"
            >
              <div class="h-8 w-8 rounded-full border-2 border-slate-400 border-t-transparent animate-spin" />
              <span class="text-xs font-medium text-slate-600 tracking-wide">Loading…</span>
            </div>

            <!-- Overlay: ERROR -->
            <div
              v-if="imgError"
              class="absolute inset-0 flex flex-col items-center justify-center gap-2 bg-slate-100"
              role="alert"
            >
              <div class="text-sm text-slate-600">Không tải được ảnh</div>
              <button
                class="rounded-lg border px-3 py-1.5 text-xs text-slate-700 hover:bg-white"
                @click="retryLoad"
              >
                Thử lại
              </button>
            </div>

            <!-- Ảnh chính -->
            <img
              v-if="c?.thumbnail"
              :key="imgKey"
              :src="c.thumbnail"
              :alt="c.title || 'cover'"
              class="absolute inset-0 h-full w-full object-cover"
              width="1280" height="720"
              decoding="async"
              loading="eager"
              fetchpriority="high"
              @load="onImgLoad"
              @error="onImgError"
            />
          </div>
        </div>

        <div class="md:col-span-2 rounded-2xl border bg-white p-4">
          <div class="mb-2 text-sm text-slate-500">
            Cập nhật: {{ fmtDate(c.updatedAt) }}
          </div>

          <div class="grid grid-cols-3 gap-3 text-center">
            <div class="rounded-xl bg-slate-100 p-4">
              <div class="text-2xl font-semibold">{{ c.enrollments }}</div>
              <div class="text-xs">Học sinh</div>
            </div>
            <div class="rounded-xl bg-slate-100 p-4">
              <div class="text-2xl font-semibold">{{ c.lessonsCount }}</div>
              <div class="text-xs">Bài học</div>
            </div>
            <div class="rounded-xl bg-slate-100 p-4">
              <div class="text-2xl font-semibold">{{ statusText(c.status) }}</div>
              <div class="text-xs">Trạng thái</div>
            </div>
          </div>

          <div class="mt-4 text-sm leading-relaxed text-slate-700" v-if="c.description">
            {{ c.description }}
          </div>
        </div>
      </div>

      <!-- Sections / Lessons (tuỳ chọn hiển thị) -->
      <div class="mt-6 space-y-3" v-if="c.sections?.length">
        <div
          v-for="sec in c.sections"
          :key="sec.id"
          class="rounded-2xl border bg-white"
        >
          <div class="flex items-center justify-between px-4 py-3 border-b">
            <div class="font-semibold">Chương {{ sec.order }} — {{ sec.title }}</div>
            <div class="text-xs text-slate-500">{{ sec.lessons.length }} bài</div>
          </div>
          <ul class="divide-y">
            <li
              v-for="(l, i) in sec.lessons"
              :key="l.id"
              class="flex items-center justify-between px-4 py-2 text-sm"
            >
              <div class="min-w-0">
                <span class="font-medium">Bài {{ sec.order }}.{{ i + 1 }}</span>
                <span class="mx-2 text-slate-400">•</span>
                <span class="text-slate-700">{{ l.title }}</span>
                <span v-if="l.isPreview" class="ml-2 rounded-full bg-emerald-50 px-2 py-0.5 text-xs text-emerald-700 border border-emerald-200">Preview</span>
              </div>
              <div class="text-slate-500">
                <span class="rounded-full bg-slate-100 px-2 py-0.5 text-xs mr-2">{{ typeLabel(l.type) }}</span>
                <span v-if="l.durationMinutes" class="text-xs">{{ l.durationMinutes }}'</span>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </template>

    <div v-else class="p-6">Không tìm thấy khoá học.</div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { courseService, type CourseDetail, type CourseStatus } from '@/services/course.service'

const route = useRoute()
const router = useRouter()

const id = route.params.id as string | number

const c = ref<CourseDetail | null>(null)
const loading = ref(true)
const err = ref('')

// trạng thái ảnh
const imgLoaded = ref(false)
const imgError = ref(false)
const imgKey = ref(0)

onMounted(async () => {
  try {
    const detail = await courseService.detail(id)
    c.value = detail

    // Preload ảnh cover để ưu tiên tải sớm (giảm trễ hiển thị)
    if (detail?.thumbnail) {
      const link = document.createElement('link')
      link.rel = 'preload'
      link.as = 'image'
      link.href = detail.thumbnail
      document.head.appendChild(link)
    }
  } catch (e: any) {
    err.value = e?.message || 'Không tải được dữ liệu khoá học.'
  } finally {
    loading.value = false
  }
})

function onImgLoad() {
  imgLoaded.value = true
  imgError.value = false
}

function onImgError() {
  imgLoaded.value = false
  imgError.value = true
}

function retryLoad() {
  // Reset trạng thái và buộc <img> render lại
  imgLoaded.value = false
  imgError.value = false
  imgKey.value++
}

function goEdit(cid: number | string) {
  router.push({ path: `/teacher/courses/${cid}/edit` })
}

function statusText(s: CourseStatus) {
  return s === 'published'
    ? 'Đã xuất bản'
    : s === 'pending_review'
    ? 'Chờ duyệt'
    : s === 'draft'
    ? 'Nháp'
    : s === 'rejected'
    ? 'Từ chối'
    : 'Lưu trữ'
}

function typeLabel(t: 'video' | 'pdf' | 'quiz') {
  return t === 'video' ? 'Video' : t === 'pdf' ? 'Tài liệu' : 'Quiz'
}

function fmtDate(iso?: string) {
  if (!iso) return ''
  try { return new Date(iso).toLocaleString() } catch { return iso }
}
</script>
