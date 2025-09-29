<template>
  <div class="space-y-6">
    <!-- Filters -->
    <div class="flex flex-wrap items-center gap-3">
      <el-date-picker
        v-model="range"
        type="daterange"
        range-separator="–"
        start-placeholder="Từ"
        end-placeholder="Đến"
      />
      <el-select v-model="granularity" placeholder="Granularity" class="w-40">
        <el-option label="Ngày" value="day" />
        <el-option label="Tuần" value="week" />
        <el-option label="Tháng" value="month" />
      </el-select>
      <el-button type="primary" @click="fetchAll">Làm mới</el-button>
    </div>

    <!-- KPI cards -->
    <div class="grid grid-cols-2 md:grid-cols-4 xl:grid-cols-6 gap-3">
      <KpiCard title="DAU" :value="fmt(kpis.dau)" icon="users" />
      <KpiCard title="ĐK mới (7d)" :value="fmt(kpis.signups7d)" icon="user-plus" />
      <KpiCard title="GMV hôm nay" :value="currency(kpis.gmvToday)" icon="credit-card" />
      <KpiCard title="Giao dịch hôm nay" :value="fmt(kpis.txToday)" icon="activity" />
      <KpiCard title="Refund rate (7d)" :value="percent(kpis.refundRate7d)" icon="rotate-ccw" />
      <KpiCard title="Chờ duyệt" :value="fmt(kpis.approvalsPending)" icon="clipboard-check" />
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="xl:col-span-2 rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Doanh thu & giao dịch</div>
        <div class="h-64 grid place-items-center text-gray-400">[Chart placeholder]</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Top khóa học</div>
        <el-table :data="topCourses" size="small" height="16rem">
          <el-table-column prop="title" label="Khóa học" />
          <el-table-column prop="enrollments" label="ĐK" width="80" align="right" />
        </el-table>
      </div>
    </div>

    <!-- Tables -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Giao dịch gần đây</div>
        <el-table :data="recentTransactions" size="small" height="20rem">
          <el-table-column prop="id" label="Mã" width="120" />
          <el-table-column prop="user" label="Người mua" />
          <el-table-column prop="course" label="Khóa học" />
          <el-table-column prop="amount" label="Số tiền" width="110" align="right">
            <template #default="{ row }">{{ currency(row.amount) }}</template>
          </el-table-column>
          <el-table-column prop="gateway" label="Cổng" width="90" />
          <el-table-column prop="status" label="TT" width="110" />
        </el-table>
      </div>

      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Duyệt khóa học</div>
        <el-table :data="pendingApprovals" size="small" height="20rem">
          <el-table-column prop="title" label="Khóa học" />
          <el-table-column prop="teacher" label="GV" width="150" />
          <el-table-column prop="submittedAt" label="Gửi lúc" width="120" />
          <el-table-column label="" width="150" align="right">
            <template #default="{ row }">
              <el-button size="small" type="success">Duyệt</el-button>
              <el-button size="small" type="danger" plain>Từ chối</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- Security & System -->
    <div class="grid grid-cols-1 xl:grid-cols-2 gap-4">
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Bảo mật</div>
        <ul class="text-sm text-gray-700 space-y-2">
          <li>
            Đăng nhập thất bại 24h: <b>{{ security.failedLogins24h }}</b>
          </li>
          <li>
            Tài khoản bị khóa: <b>{{ security.lockedAccounts }}</b>
          </li>
          <li>
            SSL hết hạn trong: <b>{{ security.sslDaysToExpire }} ngày</b>
          </li>
        </ul>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Sức khỏe hệ thống</div>
        <ul class="text-sm text-gray-700 space-y-2">
          <li>
            CPU p95: <b>{{ system.cpuP95 }}%</b> • RAM p95: <b>{{ system.ramP95 }}%</b> • Disk:
            <b>{{ system.disk }}%</b>
          </li>
          <li>
            Backup lần gần nhất: <b>{{ system.backup.lastRun }}</b> • Trạng thái:
            <b>{{ system.backup.status }}</b>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ElMessage } from 'element-plus'
// import services thực sau này
// import { reportService } from '@/services/report.service'

const range = ref<[Date, Date] | null>(null)
const granularity = ref<'day' | 'week' | 'month'>('day')

// mock state (khi nối API thì thay)
const kpis = reactive({
  dau: 0,
  signups7d: 0,
  gmvToday: 0,
  txToday: 0,
  refundRate7d: 0,
  approvalsPending: 0,
})
const topCourses = ref<any[]>([])
const recentTransactions = ref<any[]>([])
const pendingApprovals = ref<any[]>([])
const security = reactive({ failedLogins24h: 0, lockedAccounts: 0, sslDaysToExpire: 30 })
const system = reactive({ cpuP95: 0, ramP95: 0, disk: 0, backup: { lastRun: '-', status: '-' } })

function fmt(v: number) {
  return new Intl.NumberFormat().format(v)
}
function currency(v: number) {
  return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v)
}
function percent(v: number) {
  return `${v.toFixed(1)}%`
}

async function fetchAll() {
  try {
    // const data = await reportService.getDashboard({ range: range.value, granularity: granularity.value })
    // map vào state
  } catch (e) {
    ElMessage.error('Không tải được dữ liệu dashboard')
  }
}

// onMounted(() => fetchAll())
</script>

<!-- KpiCard nhỏ gọn -->
<script lang="ts">
export default {}
</script>

<!-- Bạn có thể đặt KpiCard vào components/ui/KpiCard.vue -->
