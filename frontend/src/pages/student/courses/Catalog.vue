<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-6xl px-4 py-6">
      <!-- header -->
      <div class="flex items-start justify-between gap-3">
        <div>
          <h1 class="text-2xl font-extrabold tracking-tight text-slate-900">Catalog</h1>
          <p class="mt-1 text-slate-600">Khám phá các khoá học đã phát hành theo khối & môn học.</p>
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
            placeholder="Tìm khóa học…"
            class="w-full rounded-xl border border-slate-200 bg-white px-4 py-2.5 pr-10 text-slate-800 outline-none ring-sky-100 focus:ring-4"
          />
          <svg class="pointer-events-none absolute right-3 top-2.5 h-5 w-5 stroke-slate-400" viewBox="0 0 24 24" fill="none" stroke-width="2"><path d="M21 21l-4.3-4.3"/><circle cx="11" cy="11" r="7"/></svg>
        </div>

        <select v-model="grade" class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm">
          <option :value="undefined">Tất cả khối</option>
          <option v-for="g in [1,2,3,4,5]" :key="g" :value="g">Khối {{ g }}</option>
        </select>

        <select v-model="subject" class="rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm">
          <option :value="undefined">Tất cả môn</option>
          <option v-for="s in subjects" :key="s.value" :value="s.value">{{ s.label }}</option>
        </select>

        <button @click="load" class="rounded-xl bg-slate-900 px-4 py-2.5 text-sm font-bold text-white hover:bg-slate-800">
          Làm mới
        </button>
      </div>

      <!-- grid -->
      <div class="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        <!-- skeleton -->
        <template v-if="loading">
          <div v-for="i in 8" :key="i" class="animate-pulse rounded-2xl border border-slate-200 bg-white">
            <div class="h-36 w-full rounded-t-2xl bg-slate-100"></div>
            <div class="p-4">
              <div class="h-4 w-3/4 rounded bg-slate-100"></div>
              <div class="mt-2 h-3 w-1/2 rounded bg-slate-100"></div>
            </div>
          </div>
        </template>

        <article
          v-else
          v-for="c in items"
          :key="String(c.id)"
          class="group relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
          @click="open(c.id)"
        >
          <img :src="c.thumbnail" :alt="c.title" class="h-36 w-full object-cover" />
          <div class="p-4">
            <div class="line-clamp-2 text-sm font-extrabold leading-snug text-slate-900">{{ c.title }}</div>
            <div class="mt-2 flex items-center gap-2 text-xs text-slate-600">
              <span class="inline-flex items-center rounded-full border border-slate-200 px-2 py-0.5">Khối {{ c.grade }}</span>
              <span class="inline-flex items-center rounded-full border border-slate-200 px-2 py-0.5">{{ subjectLabel(c.subject) }}</span>
            </div>
          </div>
          <div class="absolute right-3 top-3 rounded-full bg-white/90 px-2 py-1 text-[10px] font-bold text-slate-600 ring-1 ring-slate-200">PUBLISHED</div>
        </article>
      </div>

      <!-- pager & empty -->
      <div class="mt-6 flex items-center justify-center gap-3">
        <button :disabled="page<=1" @click="page--; load()"
                class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 disabled:opacity-40">
          ‹ Trước
        </button>
        <span class="text-sm text-slate-600">Trang <b>{{ page }}</b></span>
        <button @click="page++; load()"
                class="rounded-xl border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700">
          Sau ›
        </button>
      </div>

      <div v-if="!loading && !items.length" class="mt-8 rounded-2xl border border-dashed border-slate-300 bg-white p-10 text-center text-slate-600">
        Không có khoá học phù hợp.
      </div>

      <div v-if="err" class="mt-4 text-center font-semibold text-rose-600">{{ err }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { courseService, type Subject } from '@/services/course.service'

const router = useRouter()
const route = useRoute()

const items = ref<any[]>([])
const err = ref('')
const loading = ref(false)

const q = ref('')
const grade = ref<number | undefined>()
const subject = ref<Subject | undefined>()
const page = ref(1)
const pageSize = 20
const subjects = courseService.subjects()

function subjectLabel(s: Subject){ return subjects.find(x=>x.value===s)?.label || s }

async function load(){
  try{
    loading.value = true
    const res = await courseService.list({
      q: q.value || undefined,
      grade: grade.value as any,
      subject: subject.value as any,
      status: 'published',
      page: page.value,
      pageSize
    })
    items.value = res.items
    err.value = ''
  }catch(e:any){ err.value = e?.message || String(e)}
  finally{ loading.value = false }
}
function open(id: number | string){
  router.push({ name: 'student-course-detail', params: { id } })
}

onMounted(() => {
  // nhận filter từ LearningPath (query.grade)
  const g = Number(route.query.grade || '')
  if (!Number.isNaN(g) && g >= 1 && g <= 5) grade.value = g
  load()
})
</script>
