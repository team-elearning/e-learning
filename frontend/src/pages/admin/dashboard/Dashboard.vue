<template>
  <div class="space-y-6">
    <!-- Header / Filters -->
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="flex items-center gap-3">
        <el-date-picker
          v-model="range"
          type="daterange"
          range-separator="–"
          start-placeholder="Từ"
          end-placeholder="Đến"
          size="small"
        />
        <el-select v-model="granularity" size="small" class="w-32">
          <el-option label="Ngày" value="day" />
          <el-option label="Tuần" value="week" />
          <el-option label="Tháng" value="month" />
        </el-select>
      </div>

      <el-button size="small" type="primary" @click="fetchAll"> Làm mới </el-button>
    </div>

    <!-- KPI -->
    <div class="grid grid-cols-2 md:grid-cols-4 gap-3">
      <KpiCard title="Active users" value="1.3k" note="+3.2% hôm nay" />
      <KpiCard title="Đăng ký mới" value="96" note="7 ngày gần nhất" />
      <KpiCard title="Doanh thu" value="18.2M₫" note="ước tính" />
      <KpiCard title="Chờ duyệt" value="5" note="khoá học" />
    </div>

    <!-- Chart -->
    <div class="rounded-xl bg-white p-4 ring-1 ring-slate-200">
      <div class="mb-2 text-sm font-medium text-slate-700">Tổng quan doanh thu</div>
      <div class="h-40 rounded-lg bg-slate-50 grid place-items-center text-slate-400 text-sm">
        Revenue Chart (Mock)
      </div>
    </div>

    <!-- Tables -->
    <div class="grid grid-cols-1 xl:grid-cols-3 gap-4">
      <!-- Top Courses -->
      <div class="rounded-xl bg-white p-4 ring-1 ring-slate-200">
        <div class="mb-2 text-sm font-medium text-slate-700">Khoá học nổi bật</div>
        <el-table :data="topCourses" size="small" height="180">
          <el-table-column prop="title" label="Khoá học" />
          <el-table-column prop="enrollments" label="ĐK" width="80" align="right" />
        </el-table>
      </div>

      <!-- System -->
      <div class="rounded-xl bg-white p-4 ring-1 ring-slate-200">
        <div class="mb-2 text-sm font-medium text-slate-700">System status</div>
        <ul class="text-xs text-slate-600 space-y-1">
          <li>
            CPU: <b>{{ system.cpu }}%</b> • RAM: <b>{{ system.ram }}%</b>
          </li>
          <li>
            Disk: <b>{{ system.disk }}%</b>
          </li>
          <li>
            Backup: <b>{{ system.backup }}</b>
          </li>
          <li>
            SSL: <b>{{ system.ssl }} ngày</b>
          </li>
        </ul>
      </div>

      <!-- AI -->
      <div class="rounded-xl bg-white p-4 ring-1 ring-slate-200">
        <div class="mb-2 text-sm font-medium text-slate-700">AI status</div>
        <ul class="text-xs text-slate-600 space-y-1">
          <li>Model: <b>Bedrock / Titan</b></li>
          <li>Vectors: <b>1,284</b></li>
          <li>Last sync: <b>Hôm qua</b></li>
        </ul>

        <el-button size="small" class="mt-3" type="primary" plain @click="mockSyncAI">
          Sync AI (Mock)
        </el-button>
      </div>
    </div>

    <!-- Recent Transactions -->
    <div class="rounded-xl bg-white p-4 ring-1 ring-slate-200">
      <div class="mb-2 text-sm font-medium text-slate-700">Giao dịch gần đây</div>
      <el-table :data="transactions" size="small" height="220">
        <el-table-column prop="user" label="User" />
        <el-table-column prop="course" label="Khoá học" />
        <el-table-column prop="amount" label="Số tiền" width="120" align="right">
          <template #default="{ row }">
            {{ currency(row.amount) }}
          </template>
        </el-table-column>
        <el-table-column prop="status" label="TT" width="100" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="tsx">
import { ref, reactive, defineComponent } from 'vue'
import { ElMessage } from 'element-plus'

/* ================= KPI CARD ================= */
const KpiCard = defineComponent({
  props: {
    title: String,
    value: String,
    note: String,
  },
  setup(props) {
    return () => (
      <div class="rounded-xl bg-white p-3 ring-1 ring-slate-200">
        <div class="text-xs text-slate-500">{props.title}</div>
        <div class="text-lg font-semibold text-slate-900">{props.value}</div>
        <div class="text-[11px] text-slate-400">{props.note}</div>
      </div>
    )
  },
})

/* ================= STATE ================= */
const range = ref<[Date, Date] | null>(null)
const granularity = ref<'day' | 'week' | 'month'>('day')

const topCourses = ref([
  { title: 'Toán 5', enrollments: 120 },
  { title: 'Tiếng Anh 3', enrollments: 98 },
  { title: 'Tiếng Việt 4', enrollments: 76 },
])

const transactions = ref([
  {
    user: 'Nguyễn Văn A',
    course: 'Toán 5',
    amount: 350000,
    status: 'OK',
  },
  {
    user: 'Trần Thị B',
    course: 'Tiếng Anh 3',
    amount: 290000,
    status: 'OK',
  },
  {
    user: 'Lê Văn C',
    course: 'Tiếng Việt 4',
    amount: 320000,
    status: 'Refund',
  },
])

const system = reactive({
  cpu: 63,
  ram: 72,
  disk: 58,
  backup: '02:30 OK',
  ssl: 45,
})

/* ================= UTILS ================= */
function currency(v: number) {
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(v)
}

/* ================= ACTIONS ================= */
function fetchAll() {
  ElMessage.success('Đã làm mới dashboard (mock)')
}

function mockSyncAI() {
  ElMessage.success('AI Sync hoàn tất (mock)')
}
</script>
