<template>
  <div class="ranking-page-ui">
    <div class="container">
      <header class="header">
        <div class="header-info">
          <h1 class="header-title">🏆 Bảng Xếp Hạng</h1>
          <p class="header-subtitle">Vinh danh những học viên có thành tích xuất sắc nhất trong mỗi kỳ thi.</p>
        </div>

        <div class="select-wrapper">
          <button class="select-btn" @click="openSelect = !openSelect" :disabled="loadingExams">
            <span v-if="loadingExams">Đang tải đề...</span>
            <span v-else>{{ selectedExamTitle || 'Vui lòng chọn đề thi' }}</span>
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2.5" stroke="currentColor" class="select-icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5" />
            </svg>
          </button>
          <ul v-show="openSelect" class="select-menu" @mouseleave="openSelect = false">
            <li v-for="e in exams" :key="e.id" @click="selectExam(e.id)">{{ e.title }}</li>
          </ul>
        </div>
      </header>
      
      <div v-if="loading" class="skeleton-wrapper">
        <div class="skeleton-top3">
          <div class="sk-top-card"></div>
          <div class="sk-top-card main"></div>
          <div class="sk-top-card"></div>
        </div>
        <div class="sk-list">
          <div v-for="i in 7" :key="i" class="sk-list-item"></div>
        </div>
      </div>

      <div v-else-if="rows.length === 0" class="empty-state">
         <img src="https://res.cloudinary.com/dapvicdpm/image/upload/v1727116801/temp/leaderboard-empty_u5o8fg.svg" alt="No data" class="empty-icon" />
        <h3 class="empty-title">Chưa có dữ liệu xếp hạng</h3>
        <p class="empty-text">Hiện chưa có ai hoàn thành đề thi này. Hãy là người đầu tiên!</p>
      </div>

      <div v-else>
        <div class="top-3-grid">
          <div v-if="rows[1]" class="rank-card rank-2">
            <div class="podium-rank silver">🥈 Hạng 2</div>
            <img :src="avatarOf(rows[1].name)" alt="avatar" class="rank-avatar">
            <h3 class="rank-name">{{ rows[1].name }}</h3>
            <div class="rank-score">{{ rows[1].score }} điểm</div>
            <div class="rank-time">{{ rows[1].time }}</div>
          </div>
          <div v-if="rows[0]" class="rank-card rank-1">
            <div class="podium-rank gold">🥇 Hạng 1</div>
            <img :src="avatarOf(rows[0].name)" alt="avatar" class="rank-avatar">
            <h3 class="rank-name">{{ rows[0].name }}</h3>
            <div class="rank-score">{{ rows[0].score }} điểm</div>
            <div class="rank-time">{{ rows[0].time }}</div>
          </div>
          <div v-if="rows[2]" class="rank-card rank-3">
            <div class="podium-rank bronze">🥉 Hạng 3</div>
            <img :src="avatarOf(rows[2].name)" alt="avatar" class="rank-avatar">
            <h3 class="rank-name">{{ rows[2].name }}</h3>
            <div class="rank-score">{{ rows[2].score }} điểm</div>
            <div class="rank-time">{{ rows[2].time }}</div>
          </div>
        </div>

        <div class="ranking-list-wrapper">
          <div v-for="(row, index) in paginatedRestRows" :key="row.id || row.name + '-' + getRestRank(index)" class="rank-row">
            <div class="row-rank">#{{ getRestRank(index) }}</div>
            <div class="row-user">
              <img :src="avatarOf(row.name)" alt="avatar" class="row-avatar" loading="lazy" decoding="async" />
              <span class="row-name">{{ row.name }}</span>
            </div>
            <div class="row-stats">
              <div class="row-stat">
                <span class="stat-value">{{ row.correct }}/{{ row.total }}</span>
                <span class="stat-label">Câu đúng</span>
              </div>
              <div class="row-stat">
                <span class="stat-value">{{ row.time }}</span>
                <span class="stat-label">Thời gian</span>
              </div>
              <div class="row-stat score">
                <span class="stat-value">{{ row.score }}</span>
                <span class="stat-label">Điểm</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="totalPages > 1" class="pagination-wrapper">
        <button class="nav-btn" :disabled="currentPage <= 1" @click="handlePageChange(currentPage - 1)">‹</button>
        <button
          v-for="p in pagesToShow"
          :key="p.key"
          class="page-btn"
          :class="{ active: p.num === currentPage, separator: p.sep }"
          :disabled="p.sep"
          @click="!p.sep && handlePageChange(p.num!)"
        >{{ p.text }}</button>
        <button class="nav-btn" :disabled="currentPage >= totalPages" @click="handlePageChange(currentPage + 1)">›</button>
      </div>

      <div v-if="me" class="my-rank-sticky">
        <div class="my-rank-rank">#{{ me.rank }}</div>
        <div class="my-rank-user">
          <img :src="avatarOf('Bạn')" alt="avatar" class="row-avatar" />
          <span class="row-name">Vị trí của bạn</span>
        </div>
        <div class="row-stats">
          <div class="row-stat">
            <span class="stat-value">{{ me.correct }}/{{ me.total }}</span>
            <span class="stat-label">Câu đúng</span>
          </div>
          <div class="row-stat">
            <span class="stat-value">{{ me.time }}</span>
            <span class="stat-label">Thời gian</span>
          </div>
          <div class="row-stat score">
            <span class="stat-value">{{ me.score }}</span>
            <span class="stat-label">Điểm</span>
          </div>
        </div>
      </div>

      <div v-if="err" class="empty-state error">{{ err }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, watch, computed } from 'vue'

// --- MOCK SERVICE (thay thế bằng service thật của bạn) ---
const examService = createMockService();

// --- TYPES ---
type Exam = { id: number | string; title: string };
type RankRow = { id?: string | number; name: string; score: number; correct: number; total: number; time: string };
type RankMe = { rank: number; score: number; correct: number; total: number; time: string };

// --- STATE ---
const exams = ref<Exam[]>([]);
const examId = ref<Exam['id'] | undefined>();
const openSelect = ref(false);

const rows = ref<RankRow[]>([]);
const me = ref<RankMe | null>(null);

const loading = ref(true);
const loadingExams = ref(true);
const err = ref('');

const selectedExamTitle = computed(() => exams.value.find(e => e.id === examId.value)?.title);

function selectExam(id: Exam['id']) {
  examId.value = id;
  openSelect.value = false;
}

// --- PAGINATION (cho danh sách từ hạng 4) ---
const currentPage = ref(1);
const pageSize = 10;
const restRows = computed(() => rows.value.slice(3)); // Bỏ qua top 3

const paginatedRestRows = computed(() => {
  const start = (currentPage.value - 1) * pageSize;
  return restRows.value.slice(start, start + pageSize);
});

const totalPages = computed(() => Math.max(1, Math.ceil(restRows.value.length / pageSize)));

function handlePageChange(page: number) {
  if (page < 1 || page > totalPages.value) return;
  currentPage.value = page;
}

function getRestRank(indexOnPage: number) {
  return (currentPage.value - 1) * pageSize + indexOnPage + 4; // Bắt đầu từ hạng 4
}

const pagesToShow = computed(() => {
  const max = totalPages.value
  const cur = currentPage.value
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


// --- HELPERS ---
function avatarOf(name: string) {
  const safe = encodeURIComponent(name || 'User');
  return `https://api.dicebear.com/7.x/initials/svg?seed=${safe}&backgroundColor=e2e8f0&textColor=64748b`;
}

// --- DATA LOADERS ---
async function loadExams() {
  loadingExams.value = true;
  err.value = '';
  try {
    const list = await examService.list();
    exams.value = list;
    if (list.length > 0) {
      examId.value = list[0].id;
    }
  } catch (e: any) {
    err.value = e?.message || String(e);
  } finally {
    loadingExams.value = false;
  }
}

async function loadRanking(id: Exam['id']) {
  if (!id && id !== 0) {
    rows.value = [];
    me.value = null;
    return;
  };
  loading.value = true;
  rows.value = [];
  me.value = null;
  err.value = '';
  currentPage.value = 1;

  try {
    const r = await examService.ranking(id);
    rows.value = r.top;
    me.value = r.me;
  } catch (e: any) {
    err.value = e?.message || String(e);
  } finally {
    loading.value = false;
  }
}

// --- LIFECYCLE ---
onMounted(loadExams);
watch(examId, (id) => { if (id !== undefined) loadRanking(id) });

// --- MOCK SERVICE ---
function createMockService() {
  const delay = (ms: number) => new Promise(r => setTimeout(r, ms));
  return {
    async list(): Promise<Exam[]> {
      await delay(500);
      return Array.from({ length: 8 }).map((_, i) => ({
        id: i + 1,
        title: `Đề thi Thử Năng Lực #${i + 1}`
      }));
    },
    async ranking(_examId: Exam['id']): Promise<{ top: RankRow[]; me: RankMe }> {
      await delay(800);
      const N = 73;
      const top: RankRow[] = Array.from({ length: N }).map((_, i) => {
        const correct = 50 - Math.floor(i / 2);
        const score = Math.max(0, correct * 20);
        const mm = (15 + (i % 20)).toString().padStart(2, '0');
        const ss = ((i * 7) % 60).toString().padStart(2, '0');
        return { id: i + 1, name: `Học viên ${String.fromCharCode(65 + i)}`, score, correct, total: 50, time: `${mm}:${ss}` };
      });
      return { top, me: { rank: 88, score: 720, correct: 36, total: 50, time: '22:31' } };
    }
  };
}
</script>

<style scoped>
/* --- General --- */
.ranking-page-ui { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; background: #f8fafc; min-height: 100vh; color: #1e293b; padding-bottom: 96px; }
.container { max-width: 900px; margin: 0 auto; padding: 24px; }
.header { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.header-title { margin: 0; font-size: 32px; font-weight: 800; color: #0f172a; }
.header-subtitle { color: #64748b; margin: 4px 0 0 0; }

/* --- Custom Select --- */
.select-wrapper { position: relative; width: 320px; }
.select-btn { display: flex; align-items: center; justify-content: space-between; gap: 8px; background: #fff; width: 100%; height: 44px; border: 1px solid #e2e8f0; border-radius: 10px; padding: 10px 12px; cursor: pointer; font-weight: 600; transition: all 0.2s ease; }
.select-btn:disabled { cursor: not-allowed; background-color: #f8fafc; }
.select-btn:not(:disabled):hover { border-color: #cbd5e1; }
.select-icon { width: 18px; height: 18px; color: #6b7280; }
.select-menu { position: absolute; top: calc(100% + 6px); left: 0; width: 100%; background: #fff; border: 1px solid #e2e8f0; border-radius: 10px; padding: 6px; box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1); z-index: 10; max-height: 250px; overflow-y: auto; }
.select-menu li { padding: 10px; border-radius: 8px; cursor: pointer; font-weight: 500; }
.select-menu li:hover { background: #f1f5f9; color: #16a34a; }

/* --- Top 3 Cards --- */
.top-3-grid { display: grid; grid-template-columns: 1fr 1.2fr 1fr; gap: 16px; align-items: flex-end; margin-bottom: 24px; }
.rank-card { background: #fff; border-radius: 16px; padding: 24px; text-align: center; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); }
.rank-1 { order: 2; transform: scale(1.05); z-index: 5; }
.rank-2 { order: 1; }
.rank-3 { order: 3; }

.podium-rank { font-weight: 700; font-size: 14px; margin-bottom: 12px; }
.gold { color: #ca8a04; }
.silver { color: #64748b; }
.bronze { color: #c2410c; }
.rank-avatar { width: 80px; height: 80px; border-radius: 50%; margin: 0 auto 12px; border: 4px solid #fff; box-shadow: 0 0 0 1px #e2e8f0; }
.rank-1 .rank-avatar { width: 96px; height: 96px; }
.rank-name { font-size: 18px; font-weight: 700; margin: 0 0 4px; }
.rank-score { font-size: 24px; font-weight: 800; color: #16a34a; margin-bottom: 8px; }
.rank-time { font-size: 14px; color: #64748b; font-variant-numeric: tabular-nums; }

/* --- Ranking List (4+) --- */
.ranking-list-wrapper { background: #fff; border-radius: 16px; overflow: hidden; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.05); }
.rank-row { display: grid; grid-template-columns: 60px 1fr auto; align-items: center; padding: 16px 20px; border-bottom: 1px solid #f1f5f9; transition: background-color 0.2s ease; }
.rank-row:last-child { border-bottom: none; }
.rank-row:hover { background-color: #f8fafc; }

.row-rank { font-weight: 700; color: #64748b; font-size: 16px; text-align: center; }
.row-user { display: flex; align-items: center; gap: 16px; font-weight: 600; }
.row-avatar { width: 40px; height: 40px; border-radius: 50%; }
.row-stats { display: flex; gap: 24px; font-variant-numeric: tabular-nums; }
.row-stat { display: flex; flex-direction: column; align-items: flex-end; width: 90px; }
.stat-value { font-weight: 700; font-size: 16px; }
.stat-label { font-size: 12px; color: #64748b; }
.row-stat.score .stat-value { color: #16a34a; }

/* --- My Rank --- */
.my-rank-sticky { position: fixed; bottom: 0; left: 0; right: 0; background: #fff; z-index: 20; box-shadow: 0 -5px 15px -3px rgb(0 0 0 / 0.07); border-top: 1px solid #e2e8f0; display: flex; justify-content: center; }
.my-rank-sticky .row-stats { background-color: transparent; }
.my-rank-sticky { display: grid; grid-template-columns: 60px 1fr auto; align-items: center; padding: 12px 20px; max-width: 1800px; margin: 0 auto; background: linear-gradient(to right, #f0fdf4, #fff); border-top: 2px solid #16a34a; }
.my-rank-rank { font-weight: 800; color: #166534; font-size: 18px; text-align: center; }
.my-rank-user { display: flex; align-items: center; gap: 16px; font-weight: 700; }

/* --- States & Pagination --- */
.pagination-wrapper { display: flex; justify-content: center; align-items: center; gap: 8px; padding: 32px 0 16px; }
.nav-btn, .page-btn { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 10px; border: 1px solid #e2e8f0; background: #fff; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.nav-btn:disabled, .page-btn:disabled { opacity: 0.6; cursor: not-allowed; }
.nav-btn:not(:disabled):hover, .page-btn:not(:disabled):hover { border-color: #cbd5e1; }
.page-btn.active { background: #16a34a; color: #fff; border-color: #16a34a; }
.page-btn.separator { cursor: default; background: #f8fafc; }

.empty-state { text-align: center; padding: 64px 24px; }
.empty-icon { width: 140px; height: 140px; margin-bottom: 24px; }
.empty-title { font-size: 22px; font-weight: 700; color: #1e293b; margin: 0 0 8px; }
.empty-text { font-size: 16px; color: #64748b; max-width: 400px; margin: 0 auto; }
.error { color: #b91c1c; }

/* --- Skeleton --- */
.skeleton-wrapper { animation: pulse 1.5s infinite; }
.skeleton-top3 { display: grid; grid-template-columns: 1fr 1.2fr 1fr; gap: 16px; align-items: flex-end; margin-bottom: 24px; }
.sk-top-card { height: 200px; background-color: #e2e8f0; border-radius: 16px; }
.sk-top-card.main { height: 220px; }
.sk-list { background-color: #fff; border-radius: 16px; padding: 16px; border: 1px solid #e2e8f0; }
.sk-list-item { height: 40px; background-color: #e2e8f0; border-radius: 8px; margin: 12px; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.6} }

/* --- Responsive --- */
@media (max-width: 768px) {
  .header, .select-wrapper { width: 100%; }
  .top-3-grid { grid-template-columns: 1fr; }
  .rank-1, .rank-2, .rank-3 { order: 0 !important; transform: none !important; }
  .row-stats { display: none; } /* Ẩn bớt thông tin trên mobile */
  .rank-row, .my-rank-sticky { grid-template-columns: 60px 1fr; }
}
</style>