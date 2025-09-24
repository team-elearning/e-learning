<template>
  <div class="certs">
    <div class="wrap">
      <header class="head">
        <div>
          <h1>Chứng chỉ của tôi</h1>
          <p class="muted">Các chứng chỉ bạn đã đạt được sau khi hoàn thành bài thi.</p>
        </div>
      </header>

      <div class="grid">
        <article v-for="c in items" :key="c.id" class="card">
          <img :src="c.thumbnail" :alt="c.title" class="thumb" />
          <div class="meta">
            <h3 class="title">{{ c.title }}</h3>
            <p class="sub muted">Điểm {{ c.score }}/{{ c.total }} · Ngày cấp {{ c.issuedAt }}</p>
          </div>
          <div class="foot">
            <el-button @click="view(c)">Xem</el-button>
            <el-button type="primary" @click="download(c)">Tải PDF</el-button>
          </div>
        </article>
      </div>

      <div v-if="!items.length" class="empty">Bạn chưa có chứng chỉ nào.</div>
      <div v-if="err" class="empty error">{{ err }}</div>
    </div>

    <el-dialog v-model="show" title="Xem chứng chỉ" width="720px">
      <img :src="viewing?.image" alt="" style="width:100%;border-radius:8px;border:1px solid #e5e7eb" />
      <template #footer>
        <el-button @click="show=false">Đóng</el-button>
        <el-button type="primary" @click="download(viewing!)">Tải PDF</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

let examService: any
try { examService = (await import('@/services/exam.service')).examService } catch {}

const items = ref<any[]>([])
const err = ref('')
const show = ref(false)
const viewing = ref<any>(null)

onMounted(async () => {
  try {
    items.value = examService?.certificates ? await examService.certificates() : mockCerts()
  } catch (e:any) {
    err.value = e?.message || String(e)
    items.value = mockCerts()
  }
})

function view(c:any){ viewing.value = c; show.value = true }
function download(c:any){
  // demo: tải ảnh; thực tế trả file pdf từ server
  const a = document.createElement('a')
  a.href = c.pdf || c.image || c.thumbnail
  a.download = (c.title || 'certificate') + '.pdf'
  a.click()
}

/* ------- MOCK ------- */
function mockCerts(){
  return Array.from({length:4}).map((_,i)=>({
    id: i+1,
    title: `Chứng chỉ Đề #${i+1}`,
    score: 90 - i*5,
    total: 100,
    issuedAt: '2025-03-1' + i,
    thumbnail: `https://picsum.photos/seed/cert-${i}/640/360`,
    image: `https://picsum.photos/seed/cert-${i}/960/540`,
    pdf: ''
  }))
}
</script>

<style scoped>
.certs{ background:#fff; min-height:100vh; color:#0f172a; }
.wrap{ max-width:1100px; margin:0 auto; padding:18px; }
.head{ margin-bottom:12px; }
h1{ margin:0; font-size:24px; font-weight:800; }
.muted{ color:#6b7280; }
.grid{ display:grid; grid-template-columns:repeat(3, 1fr); gap:12px; }
.card{ border:1px solid #e5e7eb; border-radius:14px; background:#fff; overflow:hidden; }
.thumb{ width:100%; aspect-ratio:16/9; object-fit:cover; border-bottom:1px solid #e5e7eb; }
.meta{ padding:10px; }
.title{ margin:0 0 2px; font-weight:800; }
.sub{ margin:0; }
.foot{ padding:10px; border-top:1px solid #e5e7eb; display:flex; justify-content:flex-end; gap:8px; }
.empty{ text-align:center; padding:20px; color:#6b7280; }
.error{ color:#b91c1c; }
@media (max-width: 980px){ .grid{ grid-template-columns:repeat(2, 1fr) } }
@media (max-width: 640px){ .grid{ grid-template-columns:1fr } }
</style>
