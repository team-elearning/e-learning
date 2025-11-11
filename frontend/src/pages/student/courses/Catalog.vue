<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-6xl px-4 py-6">
      <!-- header -->
      <div class="flex items-start justify-between gap-3">
        <div>
          <h1 class="text-2xl font-extrabold tracking-tight text-slate-900">Tài liệu học tập</h1>
          <p class="mt-1 text-slate-600">
            Khám phá tài liệu, bài giảng và tư liệu học tập theo môn học.
          </p>
        </div>
        <router-link
          class="inline-flex items-center rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
          :to="{ name: 'student-learning-path' }"
        >
          Lộ trình học ›
        </router-link>
      </div>

      <!-- filters -->
      <div class="mt-5 flex flex-col gap-3 sm:flex-row sm:items-center">
        <div class="relative flex-1">
          <input
            v-model.trim="q"
            @keyup.enter="load"
            placeholder="Tìm tài liệu…"
            class="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 pr-10 text-slate-800 outline-none ring-sky-100 focus:ring-4"
          />
          <svg
            class="pointer-events-none absolute right-3 top-2.5 h-5 w-5 stroke-slate-400"
            viewBox="0 0 24 24"
            fill="none"
            stroke-width="2"
          >
            <path d="M21 21l-4.3-4.3" />
            <circle cx="11" cy="11" r="7" />
          </svg>
        </div>

        <select
          v-model="grade"
          @change="load"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"
        >
          <option :value="undefined">Tất cả khối</option>
          <option v-for="g in [1, 2, 3, 4, 5]" :key="g" :value="g">Khối {{ g }}</option>
        </select>

        <select
          v-model="subject"
          @change="load"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"
        >
          <option :value="undefined">Tất cả môn</option>
          <option v-for="s in subjects" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>

        <select
          v-model="docType"
          @change="load"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm"
        >
          <option :value="undefined">Loại tài liệu</option>
          <option v-for="t in documentTypes" :key="t.value" :value="t.value">{{ t.label }}</option>
        </select>

        <button
          @click="load"
          class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white hover:bg-slate-800"
        >
          Làm mới
        </button>
      </div>

      <!-- grid -->
      <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <!-- skeleton -->
        <template v-if="loading">
          <div
            v-for="i in 9"
            :key="i"
            class="animate-pulse rounded-2xl border border-slate-200 bg-white p-5"
          >
            <div class="flex items-start gap-3">
              <div class="h-12 w-12 shrink-0 rounded-lg bg-slate-100"></div>
              <div class="flex-1">
                <div class="h-4 w-3/4 rounded bg-slate-100"></div>
                <div class="mt-2 h-3 w-1/2 rounded bg-slate-100"></div>
              </div>
            </div>
            <div class="mt-4 flex gap-2">
              <div class="h-5 w-16 rounded-full bg-slate-100"></div>
              <div class="h-5 w-16 rounded-full bg-slate-100"></div>
            </div>
          </div>
        </template>

        <article
          v-else
          v-for="doc in items"
          :key="String(doc.id)"
          class="group relative cursor-pointer overflow-hidden rounded-2xl border border-slate-200 bg-white p-5 shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          @click="open(doc.id)"
        >
          <!-- icon & title -->
          <div class="flex items-start gap-3">
            <div
              class="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg border"
              :class="typeColorClass(doc.type)"
            >
              <svg
                class="h-6 w-6"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path
                  v-if="doc.type === 'pdf'"
                  d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6"
                />
                <path v-else-if="doc.type === 'video'" d="M23 7l-7 5 7 5V7z M2 5h13v14H2V5z" />
                <path
                  v-else-if="doc.type === 'slide'"
                  d="M10 3H3v7h7V3z M21 3h-7v7h7V3z M21 14h-7v7h7v-7z M10 14H3v7h7v-7z"
                />
                <path
                  v-else-if="doc.type === 'exercise'"
                  d="M9 11l3 3L22 4 M21 12v7a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2h11"
                />
                <path
                  v-else-if="doc.type === 'exam'"
                  d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4"
                />
                <path
                  v-else
                  d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z M14 2v6h6 M12 18v-6 M9 15h6"
                />
              </svg>
            </div>

            <div class="flex-1 min-w-0">
              <h3 class="line-clamp-2 text-sm font-extrabold leading-snug text-slate-900">
                {{ doc.title }}
              </h3>
              <p class="mt-1 line-clamp-1 text-xs text-slate-500">{{ doc.description }}</p>
            </div>
          </div>

          <!-- meta -->
          <div class="mt-4 flex flex-wrap items-center gap-2 text-xs">
            <span
              class="inline-flex items-center rounded-full border border-slate-200 px-2 py-0.5 text-slate-600"
            >
              Khối {{ doc.grade }}
            </span>
            <span
              class="inline-flex items-center rounded-full border border-slate-200 px-2 py-0.5 text-slate-600"
            >
              {{ subjectLabel(doc.subject) }}
            </span>
            <span
              class="inline-flex items-center rounded-full border px-2 py-0.5 font-semibold"
              :class="typeColorClass(doc.type)"
            >
              {{ typeLabel(doc.type) }}
            </span>
          </div>

          <!-- footer -->
          <div
            class="mt-4 flex items-center justify-between border-t border-slate-100 pt-3 text-xs text-slate-500"
          >
            <div class="flex items-center gap-1">
              <svg
                class="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M9 17H7A5 5 0 017 7h2m6 0h2a5 5 0 110 10h-2" />
                <path d="M9 12h6" />
              </svg>
              <span>{{ doc.fileSize || 'N/A' }}</span>
            </div>
            <div class="flex items-center gap-1">
              <svg
                class="h-4 w-4"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
              >
                <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4M7 10l5 5 5-5M12 15V3" />
              </svg>
              <span>{{ doc.downloads || 0 }}</span>
            </div>
          </div>

          <!-- hover overlay -->
          <div
            class="absolute inset-0 flex items-center justify-center bg-slate-900/0 transition group-hover:bg-slate-900/5"
          >
            <svg
              class="h-8 w-8 translate-y-2 stroke-slate-900 opacity-0 transition group-hover:translate-y-0 group-hover:opacity-100"
              viewBox="0 0 24 24"
              fill="none"
              stroke-width="2"
            >
              <circle cx="12" cy="12" r="10" />
              <path d="M12 8v8M8 12h8" />
            </svg>
          </div>
        </article>
      </div>

      <!-- pager & empty -->
      <div class="mt-6 flex items-center justify-center gap-3">
        <button
          :disabled="page <= 1"
          @click="prevPage"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition disabled:cursor-not-allowed disabled:opacity-40"
        >
          ‹ Trước
        </button>
        <span class="text-sm text-slate-600"
          >Trang <b>{{ page }}</b> / <b>{{ totalPages }}</b></span
        >
        <button
          :disabled="page >= totalPages"
          @click="nextPage"
          class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 transition disabled:cursor-not-allowed disabled:opacity-40"
        >
          Sau ›
        </button>
      </div>

      <div
        v-if="!loading && !items.length"
        class="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-600"
      >
        <svg
          class="mx-auto h-12 w-12 stroke-slate-300"
          viewBox="0 0 24 24"
          fill="none"
          stroke-width="2"
        >
          <path
            d="M9 12h6M9 16h6M9 8h6M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <p class="mt-3 font-semibold">Không có tài liệu phù hợp</p>
        <p class="mt-1 text-sm">Thử thay đổi bộ lọc hoặc từ khóa tìm kiếm</p>
      </div>

      <div
        v-if="err"
        class="mt-4 rounded-xl border border-rose-200 bg-rose-50 p-4 text-center text-sm font-semibold text-rose-600"
      >
        {{ err }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  documentService,
  type Grade,
  type Subject,
  type DocumentType,
} from '@/services/document.service'

const router = useRouter()
const route = useRoute()

interface Document {
  id: number | string
  title: string
  description: string
  grade: number
  subject: Subject
  type: DocumentType
  fileSize: string
  downloads: number
  url?: string
  createdAt?: string
}

const items = ref<Document[]>([])
const err = ref('')
const loading = ref(false)

const q = ref('')
const grade = ref<Grade | undefined>()
const subject = ref<Subject | undefined>()
const docType = ref<DocumentType | undefined>()
const page = ref(1)
const pageSize = 18
const totalPages = ref(1)

const subjects = documentService.subjects()
const documentTypes = [
  { value: 'pdf' as DocumentType, label: 'PDF' },
  { value: 'video' as DocumentType, label: 'Video' },
  { value: 'slide' as DocumentType, label: 'Slide' },
  { value: 'doc' as DocumentType, label: 'Tài liệu' },
  { value: 'exercise' as DocumentType, label: 'Bài tập' },
  { value: 'exam' as DocumentType, label: 'Đề thi' },
]

function subjectLabel(s: Subject): string {
  return subjects.find((x) => x.value === s)?.label || s
}

function typeLabel(t: DocumentType): string {
  return documentTypes.find((x) => x.value === t)?.label || t
}

function typeColorClass(t: DocumentType): string {
  const map: Record<string, string> = {
    pdf: 'bg-rose-50 text-rose-600 border-rose-200',
    video: 'bg-purple-50 text-purple-600 border-purple-200',
    slide: 'bg-amber-50 text-amber-600 border-amber-200',
    doc: 'bg-blue-50 text-blue-600 border-blue-200',
    exercise: 'bg-green-50 text-green-600 border-green-200',
    exam: 'bg-indigo-50 text-indigo-600 border-indigo-200',
  }
  return map[t] || 'bg-slate-50 text-slate-600 border-slate-200'
}

async function load() {
  try {
    loading.value = true
    err.value = ''
    const res = await documentService.list({
      q: q.value || undefined,
      grade: grade.value,
      subject: subject.value,
      type: docType.value,
      page: page.value,
      pageSize,
    })
    items.value = res.items
    totalPages.value = res.totalPages || 1
  } catch (e: any) {
    err.value = e?.response?.data?.message || e?.message || 'Đã xảy ra lỗi khi tải tài liệu'
    items.value = []
  } finally {
    loading.value = false
  }
}

function open(id: number | string) {
  router.push({ name: 'student-document-detail', params: { id } })
}

function prevPage() {
  if (page.value > 1) {
    page.value--
    load()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

function nextPage() {
  if (page.value < totalPages.value) {
    page.value++
    load()
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

onMounted(() => {
  const g = Number(route.query.grade || '')
  if (!Number.isNaN(g) && g >= 1 && g <= 5) grade.value = g as Grade

  const s = route.query.subject as Subject
  if (s && subjects.find((x) => x.value === s)) subject.value = s

  load()
})
</script>
