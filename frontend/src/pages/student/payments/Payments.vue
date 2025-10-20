<template>
  <div class="page">
    <div class="container">
      <h1 class="title">Thanh toán</h1>

      <!-- Payment Methods -->
      <div class="grid">
        <div class="card method">
          <h2>Chuyển khoản qua VietQR</h2>
          <p>Quét mã QR bằng App ngân hàng (NAPAS 247) để thanh toán nhanh chóng.</p>
          <div class="actions">
            <button class="btn-primary" :disabled="loading" @click="goCheckout">
              <span v-if="loading" class="spinner" />
              <span>Tiếp tục</span>
            </button>
          </div>
        </div>

        <div class="card method muted-card">
          <h2>Thẻ/Tài khoản (Đang phát triển)</h2>
          <p>Tính năng này sẽ sớm có mặt.</p>
        </div>
      </div>

      <!-- Transaction History Section -->
      <div class="history-section">
        <div class="section-header">
          <h2 class="section-title">Lịch sử thanh toán</h2>
          <div class="filters">
            <select v-model="statusFilter" class="filter-select">
              <option value="">Tất cả</option>
              <option value="success">Thành công</option>
              <option value="pending">Đang xử lý</option>
              <option value="failed">Thất bại</option>
            </select>
          </div>
        </div>

        <!-- Stats -->
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon success">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 18.75a60.07 60.07 0 0115.797 2.101c.727.198 1.453-.342 1.453-1.096V18.75M3.75 4.5v.75A.75.75 0 013 6h-.75m0 0v-.375c0-.621.504-1.125 1.125-1.125H20.25M2.25 6v9m18-10.5v.75c0 .414.336.75.75.75h.75m-1.5-1.5h.375c.621 0 1.125.504 1.125 1.125v9.75c0 .621-.504 1.125-1.125 1.125h-.375m1.5-1.5H21a.75.75 0 00-.75.75v.75m0 0H3.75m0 0h-.375a1.125 1.125 0 01-1.125-1.125V15m1.5 1.5v-.75A.75.75 0 003 15h-.75M15 10.5a3 3 0 11-6 0 3 3 0 016 0zm3 0h.008v.008H18V10.5zm-12 0h.008v.008H6V10.5z" />
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ vnd(totalSuccess) }}</div>
              <div class="stat-label">Tổng thanh toán</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon pending">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ pendingCount }}</div>
              <div class="stat-label">Đang xử lý</div>
            </div>
          </div>

          <div class="stat-card">
            <div class="stat-icon total">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ successCount }}</div>
              <div class="stat-label">Giao dịch thành công</div>
            </div>
          </div>
        </div>

        <!-- Transactions: Desktop/Tablet Table -->
        <div class="card only-desktop">
          <div class="table-wrapper">
            <table class="table">
              <thead>
                <tr>
                  <th>Mã đơn</th>
                  <th>Gói học</th>
                  <th>Số tiền</th>
                  <th>Phương thức</th>
                  <th>Ngày</th>
                  <th>Trạng thái</th>
                  <th>Thao tác</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in filteredTransactions" :key="item.id">
                  <td><div class="order-id">{{ item.orderId }}</div></td>
                  <td><div class="plan-name">{{ item.plan }}</div></td>
                  <td><div class="amount">{{ vnd(item.amount) }}</div></td>
                  <td>
                    <div class="method-badge">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 013.75 9.375v-4.5zM3.75 14.625c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5a1.125 1.125 0 01-1.125-1.125v-4.5zM13.5 4.875c0-.621.504-1.125 1.125-1.125h4.5c.621 0 1.125.504 1.125 1.125v4.5c0 .621-.504 1.125-1.125 1.125h-4.5A1.125 1.125 0 0113.5 9.375v-4.5z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M6.75 6.75h.75v.75h-.75v-.75zM6.75 16.5h.75v.75h-.75v-.75zM16.5 6.75h.75v.75h-.75v-.75zM13.5 13.5h.75v.75h-.75v-.75zM13.5 19.5h.75v.75h-.75v-.75zM19.5 13.5h.75v.75h-.75v-.75zM19.5 19.5h.75v.75h-.75v-.75zM16.5 16.5h.75v.75h-.75v-.75z" />
                      </svg>
                      {{ item.method }}
                    </div>
                  </td>
                  <td><div class="date">{{ formatDate(item.date) }}</div></td>
                  <td>
                    <span :class="['badge', `badge-${item.status}`]">
                      {{ statusText(item.status) }}
                    </span>
                  </td>
                  <td>
                    <button class="btn-view" @click="viewDetail(item)">
                      <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                        <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      </svg>
                    </button>
                  </td>
                </tr>
              </tbody>
            </table>

            <div v-if="filteredTransactions.length === 0" class="empty-state">
              <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z" />
              </svg>
              <p>Chưa có giao dịch nào</p>
            </div>
          </div>
        </div>

        <!-- Transactions: Mobile Cards -->
        <div class="tx-list only-mobile">
          <div
            class="tx-card"
            v-for="item in filteredTransactions"
            :key="'m-' + item.id"
          >
            <div class="tx-row">
              <span class="tx-label">Mã đơn</span>
              <span class="tx-value tx-strong">{{ item.orderId }}</span>
            </div>
            <div class="tx-row">
              <span class="tx-label">Gói học</span>
              <span class="tx-value">{{ item.plan }}</span>
            </div>
            <div class="tx-row">
              <span class="tx-label">Số tiền</span>
              <span class="tx-value tx-strong">{{ vnd(item.amount) }}</span>
            </div>
            <div class="tx-row">
              <span class="tx-label">Phương thức</span>
              <span class="tx-value">{{ item.method }}</span>
            </div>
            <div class="tx-row">
              <span class="tx-label">Ngày</span>
              <span class="tx-value">{{ formatDate(item.date) }}</span>
            </div>
            <div class="tx-row">
              <span class="tx-label">Trạng thái</span>
              <span class="tx-value">
                <span :class="['badge', `badge-${item.status}`]">
                  {{ statusText(item.status) }}
                </span>
              </span>
            </div>
            <div class="tx-actions">
              <button class="btn-view" @click="viewDetail(item)">Xem</button>
            </div>
          </div>

          <div v-if="filteredTransactions.length === 0" class="empty-state">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" d="M2.25 13.5h3.86a2.25 2.25 0 012.012 1.244l.256.512a2.25 2.25 0 002.013 1.244h3.218a2.25 2.25 0 002.013-1.244l.256-.512a2.25 2.25 0 012.013-1.244h3.859m-19.5.338V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18v-4.162c0-.224-.034-.447-.1-.661L19.24 5.338a2.25 2.25 0 00-2.15-1.588H6.911a2.25 2.25 0 00-2.15 1.588L2.35 13.177a2.25 2.25 0 00-.1.661z" />
            </svg>
            <p>Chưa có giao dịch nào</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)

onMounted(() => {
  import('@/pages/student/payments/Checkout.vue')
})

async function goCheckout() {
  if (loading.value) return
  loading.value = true
  try {
    await router.push({ name: 'student-payments-checkout' })
  } finally {
    loading.value = false
  }
}

interface Transaction {
  id: number
  orderId: string
  plan: string
  amount: number
  method: string
  date: string
  status: 'success' | 'pending' | 'failed'
}

const transactions = ref<Transaction[]>([
  { id: 1, orderId: 'HOCVIEN-251016-A4F2E', plan: 'Gói Premium', amount: 499000, method: 'VietQR', date: '2025-10-16T10:30:00', status: 'success' },
  { id: 2, orderId: 'HOCVIEN-251015-B8G3H', plan: 'Gói Standard', amount: 199000, method: 'VietQR', date: '2025-10-15T14:20:00', status: 'success' },
  { id: 3, orderId: 'HOCVIEN-251014-C2J9K', plan: 'Gói Basic', amount: 99000, method: 'VietQR', date: '2025-10-14T09:15:00', status: 'pending' },
  { id: 4, orderId: 'HOCVIEN-251013-D5L1M', plan: 'Gói Premium', amount: 499000, method: 'VietQR', date: '2025-10-13T16:45:00', status: 'failed' },
])

const statusFilter = ref('')

const filteredTransactions = computed(() => {
  if (!statusFilter.value) return transactions.value
  return transactions.value.filter(t => t.status === statusFilter.value)
})

const totalSuccess = computed(() =>
  transactions.value.filter(t => t.status === 'success').reduce((s, t) => s + t.amount, 0)
)
const pendingCount = computed(() => transactions.value.filter(t => t.status === 'pending').length)
const successCount = computed(() => transactions.value.filter(t => t.status === 'success').length)

function vnd(n: number) { return n.toLocaleString('vi-VN') + 'đ' }
function formatDate(s: string) {
  const d = new Date(s)
  return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()}`
}
function statusText(st: string) { return ({success:'Thành công', pending:'Đang xử lý', failed:'Thất bại'} as any)[st] || st }
function viewDetail(item: Transaction) { alert(`Chi tiết: ${item.orderId}`) }
</script>

<style>
:root {
  --accent: #16a34a;
  --line: #e5e7eb;
  --muted: #6b7280;
  --success: #10b981;
  --pending: #f59e0b;
  --failed: #ef4444;
}
</style>

<style scoped>
.page { background:#f6f7fb; min-height:100vh; padding-bottom:40px; }
.container { max-width:1200px; margin:0 auto; padding:24px 16px 40px; }
.title { font-size:clamp(20px, 2.2vw, 24px); font-weight:800; margin-bottom:16px; }

/* Payment Methods Grid */
.grid { display:grid; grid-template-columns: 1fr 1fr; gap:16px; margin-bottom:32px; }
.card { background:#fff; border:1px solid var(--line); border-radius:14px; padding:20px; }
.method h2 { margin:0 0 8px; font-size:18px; font-weight:700; }
.method p { color:var(--muted); margin:0 0 12px; font-size:14px; }
.method.muted-card { opacity:0.6; }
.actions { display:flex; gap:8px; }

/* Primary Button */
.btn-primary{
  background: var(--accent) !important;
  border: 1px solid var(--accent) !important;
  color: #fff !important;
  padding: 10px 16px !important;
  border-radius: 10px !important;
  font-weight: 800 !important;
  cursor: pointer !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  transition: all 0.2s ease !important;
}
.btn-primary:not([disabled]):hover{ filter: brightness(1.1) !important; transform: translateY(-1px) !important; }
.btn-primary[disabled]{ opacity:.7 !important; cursor:not-allowed !important; }

.spinner{ width:16px; height:16px; border:2px solid rgba(255,255,255,.6); border-top-color:#fff; border-radius:50%; animation:spin .8s linear infinite; }
@keyframes spin{ to{ transform: rotate(360deg); } }

/* History Section */
.history-section { margin-top:32px; }
.section-header { display:flex; justify-content:space-between; align-items:center; margin-bottom:16px; flex-wrap:wrap; gap:12px; }
.section-title { font-size:clamp(18px, 2vw, 20px); font-weight:800; margin:0; }
.filters { display:flex; gap:10px; }
.filter-select {
  padding:10px 14px; border:1px solid var(--line); border-radius:10px; background:#fff;
  font-size:14px; font-weight:600; cursor:pointer; outline:none; min-width:150px;
}
.filter-select:focus { border-color:var(--accent); box-shadow:0 0 0 3px rgba(22,163,74,0.1); }

/* Stats */
.stats-grid { display:grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap:14px; margin-bottom:20px; }
.stat-card { background:#fff; border:1px solid var(--line); border-radius:12px; padding:16px; display:flex; align-items:center; gap:14px; }
.stat-icon { width:48px; height:48px; border-radius:10px; display:flex; align-items:center; justify-content:center; }
.stat-icon svg { width:24px; height:24px; }
.stat-icon.success { background:#ecfdf5; color:var(--success); }
.stat-icon.pending { background:#fef3c7; color:var(--pending); }
.stat-icon.total { background:#ede9fe; color:#8b5cf6; }
.stat-value { font-size:clamp(18px, 2vw, 20px); font-weight:800; margin-bottom:2px; }
.stat-label { font-size:12px; color:var(--muted); }

/* Desktop/Tablet Table */
.table-wrapper { overflow-x:auto; }
.table { width:100%; border-collapse:collapse; min-width:800px; }
.table thead { background:#f9fafb; }
.table th { padding:12px 14px; text-align:left; font-size:11px; font-weight:700; color:var(--muted); text-transform:uppercase; letter-spacing:0.5px; border-bottom:1px solid var(--line); }
.table tbody tr { border-bottom:1px solid var(--line); transition:background 0.2s ease; }
.table tbody tr:hover { background:#f9fafb; }
.table td { padding:14px; }
.order-id { font-weight:700; font-size:13px; }
.plan-name { font-size:14px; font-weight:600; }
.amount { font-weight:800; color:#111827; }
.method-badge { display:inline-flex; align-items:center; gap:6px; font-size:13px; color:var(--muted); }
.method-badge svg { width:16px; height:16px; }
.date { font-size:13px; color:var(--muted); }

/* Badges */
.badge { display:inline-flex; padding:5px 10px; border-radius:16px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.3px; }
.badge-success { background:#ecfdf5; color:#10b981; }
.badge-pending { background:#fef3c7; color:#f59e0b; }
.badge-failed { background:#fee2e2; color:#ef4444; }

/* View Button */
.btn-view { width:32px; height:32px; display:flex; align-items:center; justify-content:center; background:#fff; border:1px solid var(--line); border-radius:8px; cursor:pointer; transition:all 0.2s ease; }
.btn-view svg { width:16px; height:16px; }
.btn-view:hover { background:#f9fafb; border-color:var(--accent); color:var(--accent); }

/* Mobile Transaction Cards (ẩn trên desktop) */
.tx-list{ display:none; }
.tx-card{
  background:#fff; border:1px solid var(--line); border-radius:12px; padding:14px; margin-bottom:12px;
  display:grid; gap:8px;
}
.tx-row{ display:flex; justify-content:space-between; gap:12px; }
.tx-label{ color:var(--muted); font-size:12px; }
.tx-value{ font-size:14px; font-weight:600; text-align:right; }
.tx-strong{ font-weight:800; }
.tx-actions{ display:flex; justify-content:flex-end; }
.tx-actions .btn-view{ width:auto; height:auto; padding:8px 10px; }

/* Responsive */
@media (max-width: 1024px){
  .container{ padding:20px 12px 32px; }
}
@media (max-width: 900px){
  .grid{ grid-template-columns: 1fr; }
  .section-header { flex-direction:column; align-items:stretch; }
  .filters { flex-direction:column; }
  .filter-select { width:100%; min-width:auto; }
  .stats-grid { grid-template-columns:1fr; }
}
@media (max-width: 700px){
  .only-desktop{ display:none; } /* Ẩn bảng */
  .only-mobile{ display:block; } /* Hiện card */
  .tx-list{ display:block; }
}
</style>
