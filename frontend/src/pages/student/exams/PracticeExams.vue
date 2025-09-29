<template>
  <div class="exams-page-ui">
    <div class="container">
      <header class="header">
        <div class="header-info">
          <h1 class="header-title">Kho đề luyện tập</h1>
          <p class="header-subtitle">Chọn một đề thi để bắt đầu thử thách và nâng cao kỹ năng của bạn.</p>
        </div>
        <div class="tools">
          <div class="search-wrapper">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="search-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
            </svg>
            <input v-model.trim="q" placeholder="Tìm kiếm theo tên đề..." @keydown.enter="applyFilters" />
          </div>
          <div class="select-wrapper">
            <button class="select-btn" @click="open = !open">
              <span>{{ levelLabel || 'Tất cả cấp độ' }}</span>
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor" class="select-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M8.25 15L12 18.75 15.75 15m-7.5-6L12 5.25 15.75 9" />
              </svg>
            </button>
            <ul v-show="open" class="select-menu" @mouseleave="open = false">
              <li @click="setLevel('')">Tất cả cấp độ</li>
              <li @click="setLevel('basic')">Cơ bản</li>
              <li @click="setLevel('advanced')">Nâng cao</li>
            </ul>
          </div>
        </div>
      </header>

      <div v-if="loading" class="exams-grid">
        <div v-for="i in pageSize" :key="i" class="card-skeleton"></div>
      </div>

      <div v-else-if="exams.length > 0" class="exams-grid">
        <article v-for="e in exams" :key="e.id" class="exam-card">
          <div class="card-body">
            <span class="subject-tag" :class="getSubjectClass(subj(e))">{{ subj(e) }}</span>
            <h2 class="card-title">{{ e.title }}</h2>
            <p class="card-meta">
              <span>{{ qCount(e) }} câu</span>
              <span>{{ toMin(e.durationSec) }} phút</span>
              <span>Đạt ≥ {{ e.passCount }} câu</span>
            </p>
          </div>
          <div class="card-footer">
            <span class="level-badge" :class="e.level">{{ labelLevel(e.level) }}</span>
            <router-link class="start-btn" :to="{ name: 'student-exam-detail', params: { id: e.id } }">
              Bắt đầu
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="arrow-icon">
                <path stroke-linecap="round" stroke-linejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
              </svg>
            </router-link>
          </div>
        </article>
      </div>
      
      <div v-else class="empty-state">
        <img src="https://res.cloudinary.com/dapvicdpm/image/upload/v1727116801/temp/no-results_s3fb6c.svg" alt="No results" class="empty-icon" />
        <h3 class="empty-title">Không tìm thấy đề thi phù hợp</h3>
        <p class="empty-text">Vui lòng thử lại với từ khóa hoặc bộ lọc khác.</p>
      </div>
    </div>

    <div v-if="totalPages > 1" class="pagination-wrapper">
      <button class="nav-btn" :disabled="page <= 1" @click="go(page - 1)">‹</button>
      <button
        v-for="p in pagesToShow"
        :key="p.key"
        class="page-btn"
        :class="{ active: p.num === page, separator: p.sep }"
        :disabled="p.sep"
        @click="!p.sep && go(p.num!)"
      >{{ p.text }}</button>
      <button class="nav-btn" :disabled="page >= totalPages" @click="go(page + 1)">›</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useExamStore } from '@/store/exam.store'
import { storeToRefs } from 'pinia'

const store = useExamStore()
const { exams, total, page, pageSize, loading } = storeToRefs(store)

const q = ref(store.q)
const level = ref<'' | 'basic' | 'advanced'>(store.level)
const open = ref(false)

const levelLabel = computed(() =>
  level.value === 'basic' ? 'Cơ bản' : level.value === 'advanced' ? 'Nâng cao' : ''
)

function setLevel(v: '' | 'basic' | 'advanced') {
  level.value = v
  open.value = false
  applyFilters()
}

function applyFilters() {
  store.q = q.value
  store.level = level.value
  store.fetchExamsPage(1, pageSize.value)
}

onMounted(() => {
  store.fetchExamsPage()
})

function go(p: number) {
  store.fetchExamsPage(p, pageSize.value)
}

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const pagesToShow = computed(() => {
  const max = totalPages.value
  const cur = page.value
  const windowSize = 5
  const arr: { key: string; num?: number; text: string; sep?: boolean }[] = []

  const push = (n: number) => arr.push({ key: 'p' + n, num: n, text: String(n) })
  const sep = (k: string) => arr.push({ key: k, text: '…', sep: true })

  if (max <= windowSize + 2) {
    for (let i = 1; i <= max; i++) push(i)
  } else {
    push(1)
    const start = Math.max(2, cur - 1)
    const end = Math.min(max - 1, cur + 1)
    if (start > 2) sep('s')
    for (let i = start; i <= end; i++) push(i)
    if (end < max - 1) sep('e')
    push(max)
  }
  return arr
})

// --- Helpers ---
function qCount(e: any) { return (e?.questionsCount ?? e?.questions ?? 0) as number }
function toMin(s: number) { return Math.round(s / 60) }
function labelLevel(l: 'basic' | 'advanced') { return l === 'advanced' ? 'Nâng cao' : 'Cơ bản' }

// Định nghĩa một đối tượng để map giá trị subject với nhãn hiển thị
const subjectLabels: Record<string, string> = {
  math: 'Toán học',
  vietnamese: 'Tiếng Việt',
  english: 'Tiếng Anh',
  science: 'Khoa học'
};

function subj(e: any) {
  if (e && 'subject' in e && e.subject) {
    return labelSubject(e.subject);
  }
  return e?.level === 'advanced' ? 'Nâng cao' : 'Cơ bản';
}

function labelSubject(s: keyof typeof subjectLabels) {
  return subjectLabels[s] || 'Khác';
}

// THÊM HÀM MỚI ĐỂ SỬA LỖI
function getSubjectClass(subjectLabel: string) {
  const subjectKey = Object.keys(subjectLabels).find(key => subjectLabels[key] === subjectLabel);
  return `subject-${subjectKey || 'default'}`;
}


watch(pageSize, () => store.fetchExamsPage(1, pageSize.value))
</script>

<style scoped>
.exams-page-ui {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  background-color: #f8fafc;
  min-height: 100vh;
}
.container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 32px 24px;
}

/* Header */
.header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  flex-wrap: wrap;
  gap: 24px;
  margin-bottom: 32px;
}
.header-title { font-size: 32px; font-weight: 800; color: #1e293b; margin: 0 0 4px; }
.header-subtitle { font-size: 16px; color: #64748b; margin: 0; }
.tools { display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }

.search-wrapper { display: flex; align-items: center; gap: 8px; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 0 12px; transition: all 0.2s ease; }
.search-wrapper:focus-within { border-color: #16a34a; box-shadow: 0 0 0 2px #dcfce7; }
.search-wrapper input { border: 0; outline: 0; width: 240px; height: 42px; font-size: 15px; }
.search-icon { width: 20px; height: 20px; color: #9ca3af; }

.select-wrapper { position: relative; }
.select-btn { display: flex; align-items: center; justify-content: space-between; gap: 8px; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; cursor: pointer; font-weight: 600; width: 180px; transition: all 0.2s ease; }
.select-btn:hover { border-color: #cbd5e1; }
.select-icon { width: 18px; height: 18px; color: #6b7280; transition: transform 0.2s ease; }
.select-btn[aria-expanded="true"] .select-icon { transform: rotate(180deg); }
.select-menu { position: absolute; top: calc(100% + 6px); left: 0; width: 100%; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 6px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1); z-index: 10; }
.select-menu li { padding: 10px; border-radius: 8px; cursor: pointer; font-weight: 500; }
.select-menu li:hover { background: #f1f5f9; color: #16a34a; }

/* Grid & Cards */
.exams-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(320px, 1fr)); gap: 24px; }
.exam-card { background: #fff; border: 1px solid #e2e8f0; border-radius: 16px; display: flex; flex-direction: column; transition: all 0.3s ease; box-shadow: 0 1px 2px 0 rgb(0 0 0 / 0.05); }
.exam-card:hover { transform: translateY(-4px); box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1); }
.card-body { padding: 20px; flex-grow: 1; }
.card-title { font-size: 18px; font-weight: 700; color: #1e293b; margin: 12px 0; line-height: 1.5; }
.card-meta { display: flex; flex-wrap: wrap; gap: 6px 12px; font-size: 14px; color: #64748b; margin: 0; padding-top: 12px; border-top: 1px solid #f1f5f9; }
.card-meta span::after { content: '•'; margin-left: 12px; color: #cbd5e1; }
.card-meta span:last-child::after { content: ''; }
.card-footer { display: flex; justify-content: space-between; align-items: center; padding: 12px 20px; background: #f8fafc; border-top: 1px solid #e2e8f0; }

.level-badge { font-size: 12px; font-weight: 700; padding: 4px 10px; border-radius: 999px; }
.level-badge.basic { color: #15803d; background-color: #dcfce7; }
.level-badge.advanced { color: #991b1b; background-color: #fee2e2; }

.subject-tag { display: inline-block; padding: 4px 10px; border-radius: 999px; font-size: 12px; font-weight: 700; color: #fff; }
.subject-math { background-color: #ef4444; }
.subject-english { background-color: #3b82f6; }
.subject-vietnamese { background-color: #f97316; }
.subject-science { background-color: #14b8a6; }
.subject-default { background-color: #64748b; }

.start-btn { display: inline-flex; align-items: center; gap: 6px; background-color: #16a34a; color: #fff; text-decoration: none; padding: 8px 16px; border-radius: 8px; font-weight: 600; font-size: 14px; transition: all 0.2s ease; }
.start-btn:hover { background-color: #15803d; }
.arrow-icon { width: 16px; height: 16px; transition: transform 0.2s ease; }
.start-btn:hover .arrow-icon { transform: translateX(3px); }

/* Skeleton */
.card-skeleton { height: 180px; background-color: #fff; border-radius: 16px; border: 1px solid #e2e8f0; }

/* Empty State */
.empty-state { text-align: center; padding: 64px 24px; }
.empty-icon { width: 120px; height: 120px; margin-bottom: 24px; }
.empty-title { font-size: 20px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.empty-text { font-size: 15px; color: #64748b; max-width: 350px; margin: 0 auto; }

/* Pagination */
.pagination-wrapper { display: flex; justify-content: center; align-items: center; gap: 8px; padding: 32px 0 16px; }
.nav-btn, .page-btn { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 10px; border: 1px solid #e2e8f0; background: #fff; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.nav-btn:disabled, .page-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.nav-btn:not(:disabled):hover, .page-btn:not(:disabled):hover { border-color: #cbd5e1; }
.page-btn.active { background: #16a34a; color: #fff; border-color: #16a34a; }
.page-btn.separator { cursor: default; background: #f8fafc; }

@media (max-width: 768px) {
  .header { flex-direction: column; align-items: stretch; }
  .tools { flex-direction: column; align-items: stretch; }
  .search-wrapper input, .select-btn { width: 100%; box-sizing: border-box; }
}
</style>