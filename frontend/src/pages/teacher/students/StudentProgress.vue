<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-4 py-6 sm:px-6 md:px-10">
      <!-- Header -->
      <div class="mb-4 sm:mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h1 class="text-xl font-semibold sm:text-2xl">Học sinh</h1>
      </div>

      <!-- Tools -->
      <div class="mb-5 grid grid-cols-1 gap-2 sm:gap-3 md:grid-cols-4">
        <!-- Search -->
        <div class="md:col-span-2">
          <label class="sr-only">Tìm kiếm</label>
          <div
            class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2.5"
          >
            <svg
              viewBox="0 0 24 24"
              class="h-5 w-5 shrink-0 text-slate-400"
              fill="none"
              stroke="currentColor"
              aria-hidden="true"
            >
              <circle cx="11" cy="11" r="8" stroke-width="2" />
              <path d="M21 21l-4.3-4.3" stroke-width="2" />
            </svg>
            <input
              v-model.trim="q"
              type="text"
              placeholder="Tìm tên, username, email…"
              class="w-full bg-transparent outline-none text-sm sm:text-base"
              @input="onChanged(true)"
            />
          </div>
        </div>

        <!-- Status -->
        <div class="select-wrap">
          <select v-model="status" class="select-base" @change="onChanged(true)">
            <option value="">Tất cả trạng thái</option>
            <option value="active">Đang hoạt động</option>
            <option value="locked">Khoá tạm</option>
            <option value="banned">Cấm</option>
          </select>
          <span class="select-chevron" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
              <path
                fill-rule="evenodd"
                d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 111.04 1.08l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.31a.75.75 0 01.02-1.1z"
                clip-rule="evenodd"
              />
            </svg>
          </span>
        </div>

        <!-- Sort -->
        <div class="select-wrap">
          <select v-model="sortBy" class="select-base" @change="onChanged(true)">
            <option value="name">Tên (A→Z)</option>
            <option value="createdAt">Ngày tạo</option>
            <option value="lastLoginAt">Đăng nhập gần</option>
          </select>
          <span class="select-chevron" aria-hidden="true">
            <svg viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
              <path
                fill-rule="evenodd"
                d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 111.04 1.08l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.31a.75.75 0 01.02-1.1z"
                clip-rule="evenodd"
              />
            </svg>
          </span>
        </div>
      </div>

      <!-- List -->
      <div v-if="loading" class="py-16 text-center text-slate-500">Đang tải…</div>

      <div v-else class="grid grid-cols-1 gap-3">
        <article
          v-for="u in list"
          :key="u.id"
          class="flex flex-wrap items-center gap-3 sm:gap-4 rounded-2xl border border-slate-200 bg-white p-3 sm:p-4 hover:shadow-sm"
        >
          <img
            :src="u.avatar || fallbackAvatar(u)"
            :alt="u.name"
            class="h-12 w-12 rounded-full object-cover"
          />

          <div class="min-w-0 flex-1">
            <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
              <h3 class="truncate font-semibold text-slate-900">{{ u.name }}</h3>
              <span class="truncate text-xs text-slate-500">@{{ u.username }}</span>
              <span class="rounded-full border px-2 py-0.5 text-xs" :class="badgeClass(u.status)">
                {{ statusText(u.status) }}
              </span>
            </div>

            <div class="mt-1 truncate text-xs sm:text-sm text-slate-600">
              {{ u.email }}
              <span class="mx-1 text-slate-300">•</span>
              Tạo: {{ fmt(u.createdAt) }}
              <span class="mx-1 text-slate-300">•</span>
              Lần đăng nhập cuối: {{ u.lastLoginAt ? fmt(u.lastLoginAt) : '—' }}
            </div>
          </div>

          <div class="flex w-full sm:w-auto shrink-0 gap-2">
            <button
              class="flex-1 sm:flex-none rounded-xl border px-3 py-2 text-sm hover:bg-slate-50"
              @click="openFeedback(u.id)"
            >
              Phản hồi
            </button>
          </div>
        </article>

        <p v-if="!list.length" class="mt-10 text-center text-slate-500">
          Không có học sinh phù hợp.
        </p>
      </div>

      <!-- Pagination -->
      <div class="mt-6">
        <!-- Compact on mobile -->
        <div
          v-if="isCompact"
          class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2"
        >
          <div class="text-sm text-slate-600">
            Tổng {{ total }} • Trang {{ page }} / {{ totalPages || 1 }}
          </div>
          <div class="flex items-center gap-2">
            <button
              class="rounded-xl border px-3 py-2 text-sm disabled:opacity-50"
              :disabled="page <= 1"
              @click="go(page - 1)"
            >
              Trước
            </button>
            <span class="text-sm text-slate-600">Trang {{ page }} / {{ totalPages || 1 }}</span>
            <button
              class="rounded-xl border px-3 py-2 text-sm disabled:opacity-50"
              :disabled="page >= totalPages"
              @click="go(page + 1)"
            >
              Sau
            </button>

            <div class="select-wrap ml-1">
              <select v-model.number="pageSize" class="select-base h-9" @change="onChanged(true)">
                <option :value="10">10 / trang</option>
                <option :value="20">20 / trang</option>
                <option :value="50">50 / trang</option>
              </select>
              <span class="select-chevron" aria-hidden="true">
                <svg viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                  <path
                    fill-rule="evenodd"
                    d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 111.04 1.08l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.31a.75.75 0 01.02-1.1z"
                    clip-rule="evenodd"
                  />
                </svg>
              </span>
            </div>
          </div>
        </div>

        <!-- Full on ≥ md -->
        <div v-else class="flex items-center justify-between">
          <div class="text-sm text-slate-600">
            Tổng {{ total }} • Trang {{ page }} / {{ totalPages || 1 }}
          </div>
          <div class="flex items-center gap-2">
            <button
              class="rounded-xl border px-3 py-2 text-sm disabled:opacity-50"
              :disabled="page <= 1"
              @click="go(page - 1)"
            >
              Trước
            </button>

            <div class="select-wrap">
              <select v-model.number="page" class="select-base h-10 w-[92px]" @change="go(page)">
                <option v-for="p in Math.max(totalPages, 1)" :key="p" :value="p">{{ p }}</option>
              </select>
              <span class="select-chevron" aria-hidden="true">
                <svg viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                  <path
                    fill-rule="evenodd"
                    d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 111.04 1.08l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.31a.75.75 0 01.02-1.1z"
                    clip-rule="evenodd"
                  />
                </svg>
              </span>
            </div>

            <button
              class="rounded-xl border px-3 py-2 text-sm disabled:opacity-50"
              :disabled="page >= totalPages"
              @click="go(page + 1)"
            >
              Sau
            </button>

            <div class="select-wrap ml-1">
              <select v-model.number="pageSize" class="select-base h-10" @change="onChanged(true)">
                <option :value="10">10 / trang</option>
                <option :value="20">20 / trang</option>
                <option :value="50">50 / trang</option>
              </select>
              <span class="select-chevron" aria-hidden="true">
                <svg viewBox="0 0 20 20" fill="currentColor" class="h-4 w-4">
                  <path
                    fill-rule="evenodd"
                    d="M5.23 7.21a.75.75 0 011.06.02L10 10.17l3.71-2.94a.75.75 0 111.04 1.08l-4.24 3.36a.75.75 0 01-.94 0L5.21 8.31a.75.75 0 01.02-1.1z"
                    clip-rule="evenodd"
                  />
                </svg>
              </span>
            </div>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { userService, type User, type UserStatus, type PageParams } from '@/services/user.service'

const router = useRouter()

// state
const loading = ref(false)
const raw = ref<User[]>([])
const total = ref(0)

// filters
const q = ref('')
const status = ref<UserStatus | ''>('') // '' => tất cả
const sortBy = ref<'name' | 'createdAt' | 'lastLoginAt'>('name')
const sortDir = ref<'ascending' | 'descending'>('ascending')

// paging
const page = ref(1)
const pageSize = ref(20)
const totalPages = computed(() => Math.ceil(total.value / pageSize.value))

// responsive flag (compact pager on small screens)
const isCompact = ref(false)
function updateCompact() {
  isCompact.value = window.innerWidth < 640
}

// fetch list từ service
async function fetchList() {
  loading.value = true
  try {
    const params: PageParams = {
      q: q.value || undefined,
      role: 'student',
      status: (status.value as UserStatus) || undefined,
      page: page.value,
      pageSize: pageSize.value,
      sortBy: sortBy.value,
      sortDir: sortDir.value,
    }
    const { items, total: t } = await userService.list(params)
    raw.value = items
    total.value = t
  } finally {
    loading.value = false
  }
}

// list hiển thị
const list = computed(() => {
  let arr = raw.value.slice()

  const key = q.value.toLowerCase().trim()
  if (key) {
    arr = arr.filter(
      (u) =>
        (u.name ?? '').toLowerCase().includes(key) ||
        u.username.toLowerCase().includes(key) ||
        u.email.toLowerCase().includes(key),
    )
  }
  if (status.value) arr = arr.filter((u) => u.status === status.value)

  switch (sortBy.value) {
    case 'createdAt':
      arr.sort((a, b) => new Date(a.createdAt).getTime() - new Date(b.createdAt).getTime())
      break
    case 'lastLoginAt':
      arr.sort(
        (a, b) => new Date(a.lastLoginAt || 0).getTime() - new Date(b.lastLoginAt || 0).getTime(),
      )
      break
    default:
      arr.sort((a, b) => (a.name ?? '').localeCompare(b.name ?? ''))
  }
  if (sortDir.value === 'descending') arr.reverse()

  return arr
})

function onChanged(resetPage = false) {
  if (resetPage) page.value = 1
  debouncedFetch()
}

function go(p: number) {
  page.value = p
  fetchList()
}

function openFeedback(id: string | number) {
  router.push({ path: '/teacher/students/feedback', query: { id: String(id) } })
}

// helpers
function fmt(iso?: string) {
  if (!iso) return '—'
  const d = new Date(iso)
  return d.toLocaleString('vi-VN')
}
function fallbackAvatar(u: User) {
  return `https://i.pravatar.cc/100?u=${encodeURIComponent(String(u.id))}`
}
function badgeClass(s: UserStatus | 'inactive') {
  switch (s) {
    case 'active':
      return 'border-emerald-200 bg-emerald-50 text-emerald-700'
    case 'locked':
      return 'border-amber-200 bg-amber-50 text-amber-700'
    case 'banned':
      return 'border-rose-200 bg-rose-50 text-rose-700'
    case 'inactive':
      return 'border-sky-200 bg-sky-50 text-sky-700'
  }
}
function statusText(s: UserStatus) {
  return s === 'active'
    ? 'Đang hoạt động'
    : s === 'locked'
      ? 'Khoá tạm'
      : s === 'banned'
        ? 'Cấm'
        : 'Chờ duyệt'
}

// debounce fetch
let t: number | undefined
function debouncedFetch(delay = 300) {
  if (t) window.clearTimeout(t)
  t = window.setTimeout(() => fetchList(), delay)
}

// auto fetch
watch([q, status, sortBy, sortDir, pageSize], () => onChanged(true))
onMounted(() => {
  updateCompact()
  window.addEventListener('resize', updateCompact, { passive: true })
  fetchList()
})
</script>

<style scoped>
:host,
.min-h-screen {
  overflow-x: hidden;
}

/* ===== Custom select (cross-browser, stable size) ===== */
.select-wrap {
  position: relative;
}
.select-chevron {
  pointer-events: none;
  position: absolute;
  right: 10px;
  top: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  color: #94a3b8; /* slate-400 */
}
.select-base {
  width: 100%;
  border-radius: 1rem; /* rounded-2xl */
  border: 1px solid #e5e7eb; /* slate-200 */
  background: #fff;
  padding: 0 2.5rem 0 0.75rem; /* pr-10 + pl-3 */
  height: 40px; /* h-10 */
  font-size: 0.875rem; /* text-sm */
  line-height: 1.25rem;
  background-clip: padding-box; /* fix Safari radius */
  appearance: none;
  -webkit-appearance: none;
  -moz-appearance: none;
}
.select-base::-ms-expand {
  display: none;
} /* old Edge/IE */
.select-base:focus {
  outline: none;
  border-color: #7dd3fc; /* sky-300 */
  box-shadow: 0 0 0 2px rgba(2, 132, 199, 0.28);
}
.select-base:hover {
  border-color: #cbd5e1;
} /* slate-300 */
</style>
