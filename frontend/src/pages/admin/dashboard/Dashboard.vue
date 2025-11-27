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
      <KpiCard
        title="Khoá hot chờ xử lý"
        :value="fmt(kpis.approvalsPending)"
        icon="clipboard-check"
      />
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <div class="xl:col-span-2 rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Doanh thu & giao dịch</div>
        <div class="h-64 grid place-items-center text-gray-400">
          [Chart placeholder – sau này nhét ECharts / Chart.js]
        </div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Top khoá học</div>
        <el-table :data="topCourses" size="small" height="16rem">
          <el-table-column prop="title" label="Khoá học" />
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
          <el-table-column prop="course" label="Khoá học" />
          <el-table-column prop="amount" label="Số tiền" width="110" align="right">
            <template #default="{ row }">
              {{ currency(row.amount) }}
            </template>
          </el-table-column>
          <el-table-column prop="gateway" label="Cổng" width="90" />
          <el-table-column prop="status" label="TT" width="110" />
        </el-table>
      </div>

      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Khoá học nổi bật</div>
        <el-table :data="featuredCourses" size="small" height="20rem">
          <el-table-column prop="title" label="Khoá học" />
          <el-table-column prop="teacher" label="GV" width="150" />
          <el-table-column prop="updatedAt" label="Cập nhật" width="140" />
          <el-table-column label="" width="150" align="right">
            <template #default="{ row }">
              <el-button size="small" type="primary" plain> Xem </el-button>
              <el-button size="small" type="default"> Chi tiết </el-button>
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
            Tài khoản bị khoá: <b>{{ security.lockedAccounts }}</b>
          </li>
          <li>
            SSL hết hạn trong: <b>{{ security.sslDaysToExpire }} ngày</b>
          </li>
        </ul>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-3 font-medium">Sức khoẻ hệ thống</div>
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

<script setup lang="tsx">
import { ref, reactive, onMounted, defineComponent, computed } from 'vue'
import { ElMessage } from 'element-plus'

/* ========= LOCAL KPI CARD COMPONENT ========= */
const KpiCard = defineComponent({
  name: 'KpiCard',
  props: {
    title: { type: String, required: true },
    value: { type: [String, Number], required: true },
    icon: { type: String, default: 'default' },
  },
  setup(props) {
    const emoji = computed(() => {
      switch (props.icon) {
        case 'users':
          return '👥'
        case 'user-plus':
          return '➕'
        case 'credit-card':
          return '💳'
        case 'activity':
          return '📈'
        case 'rotate-ccw':
          return '↩️'
        case 'clipboard-check':
          return '📋'
        default:
          return '📊'
      }
    })

    return () => (
      <div class="flex items-center gap-2 rounded-lg bg-white px-3 py-2 shadow-sm ring-1 ring-slate-200 md:rounded-xl md:px-4 md:py-3">
        <div class="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-100 md:h-9 md:w-9">
          <span class="text-lg">{emoji.value}</span>
        </div>
        <div class="min-w-0">
          <div class="text-[11px] text-slate-500 md:text-xs">{props.title}</div>
          <div class="text-sm font-semibold text-slate-900 md:text-base truncate">
            {props.value}
          </div>
        </div>
      </div>
    )
  },
})

/* ========= STATE ========= */

const range = ref<[Date, Date] | null>(null)
const granularity = ref<'day' | 'week' | 'month'>('day')

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
const featuredCourses = ref<any[]>([])

const security = reactive({
  failedLogins24h: 0,
  lockedAccounts: 0,
  sslDaysToExpire: 30,
})

const system = reactive({
  cpuP95: 0,
  ramP95: 0,
  disk: 0,
  backup: { lastRun: '-', status: '-' },
})

/* ========= FORMATTERS ========= */

function fmt(v: number) {
  return new Intl.NumberFormat('vi-VN').format(v || 0)
}
function currency(v: number) {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(v || 0)
}
function percent(v: number) {
  const n = Number.isFinite(v) ? v : 0
  return `${n.toFixed(1)}%`
}

/* ========= MOCK DATA ========= */

function fillMockData() {
  kpis.dau = 1320
  kpis.signups7d = 96
  kpis.gmvToday = 18200000
  kpis.txToday = 73
  kpis.refundRate7d = 2.7
  kpis.approvalsPending = 5

  topCourses.value = [
    { title: 'Toán 5 - Luyện thi', enrollments: 320 },
    { title: 'Tiếng Việt 4 - Đọc hiểu', enrollments: 210 },
    { title: 'Tiếng Anh 3 - Giao tiếp', enrollments: 165 },
    { title: 'Khoa học 5 - Ôn tập HKII', enrollments: 142 },
  ]

  recentTransactions.value = [
    {
      id: 'TX202411-0001',
      user: 'Nguyễn Văn A',
      course: 'Toán 5 - Luyện thi',
      amount: 350000,
      gateway: 'VNPAY',
      status: 'Thành công',
    },
    {
      id: 'TX202411-0002',
      user: 'Trần Thị B',
      course: 'Tiếng Anh 3 - Giao tiếp',
      amount: 290000,
      gateway: 'MOMO',
      status: 'Thành công',
    },
    {
      id: 'TX202411-0003',
      user: 'Lê Văn C',
      course: 'Tiếng Việt 4 - Đọc hiểu',
      amount: 320000,
      gateway: 'ZaloPay',
      status: 'Hoàn tiền',
    },
    {
      id: 'TX202411-0004',
      user: 'Phạm Thị D',
      course: 'Khoa học 5 - Ôn tập HKII',
      amount: 300000,
      gateway: 'VNPAY',
      status: 'Thành công',
    },
  ]

  featuredCourses.value = [
    {
      title: 'Toán 4 - Ôn tập cuối năm',
      teacher: 'GV. Nguyễn Thị Mai',
      updatedAt: 'Hôm qua',
    },
    {
      title: 'Tiếng Anh 5 - Luyện thi Movers',
      teacher: 'GV. Lê Hoàng',
      updatedAt: '2 ngày trước',
    },
    {
      title: 'Khoa học 4 - Thí nghiệm vui',
      teacher: 'GV. Trần Minh',
      updatedAt: '3 ngày trước',
    },
  ]

  security.failedLogins24h = 27
  security.lockedAccounts = 3
  security.sslDaysToExpire = 45

  system.cpuP95 = 63
  system.ramP95 = 72
  system.disk = 58
  system.backup = {
    lastRun: 'Hôm nay • 02:30',
    status: 'OK',
  }
}

/* ========= FETCH ========= */

async function fetchAll() {
  try {
    // sau này nối API:
    // const data = await reportService.getDashboard({ range: range.value, granularity: granularity.value })
    // map data -> state
    fillMockData()
  } catch (e) {
    ElMessage.error('Không tải được dữ liệu dashboard, đang hiển thị dữ liệu mẫu.')
    fillMockData()
  }
}

onMounted(() => {
  fetchAll()
})
</script>
