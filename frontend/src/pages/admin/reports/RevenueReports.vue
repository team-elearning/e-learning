<template>
  <div class="space-y-4">
    <!-- Filters -->
    <div class="grid grid-cols-1 items-start gap-3 md:grid-cols-3 xl:grid-cols-6">
      <el-date-picker
        v-model="range"
        type="daterange"
        unlink-panels
        range-separator="–"
        start-placeholder="Từ ngày"
        end-placeholder="Đến ngày"
        value-format="YYYY-MM-DD"
        class="md:col-span-2 xl:col-span-2 w-full"
        @change="applyRange"
      />
      <el-select v-model="gran" @change="reload" class="w-full" placeholder="Granularity">
        <el-option label="Theo ngày" value="day" />
        <el-option label="Theo tuần" value="week" />
        <el-option label="Theo tháng" value="month" />
      </el-select>
      <div class="md:col-span-2 xl:col-span-3 flex items-center gap-2 md:justify-end">
        <el-button @click="reset">Xoá lọc</el-button>
        <el-button type="primary" plain @click="reload">Lọc</el-button>
        <el-button @click="exportCsv" :loading="exporting">Xuất CSV</el-button>
      </div>
    </div>

    <!-- KPI cards -->
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Doanh thu gộp</div>
        <div class="mt-2 text-2xl font-semibold">{{ money(kpi.gross) }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Net</div>
        <div class="mt-2 text-2xl font-semibold">{{ money(kpi.net) }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Hoàn tiền</div>
        <div class="mt-2 text-2xl font-semibold">{{ money(kpi.refunds) }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Số đơn</div>
        <div class="mt-2 text-2xl font-semibold">{{ kpi.orders }}</div>
      </div>
    </div>

    <!-- Charts -->
    <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <div class="xl:col-span-2 rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-2 font-semibold">Dòng tiền theo {{ granLabel }}</div>
        <v-chart :option="lineOption" autoresize style="height: 360px" />
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-2 font-semibold">Tỷ trọng theo cổng</div>
        <v-chart :option="pieOption" autoresize style="height: 360px" />
      </div>
    </div>

    <!-- Top courses -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="mb-2 font-semibold">Khoá học doanh thu cao nhất</div>
      <el-table :data="topCourses" v-loading="loading.top" height="420">
        <el-table-column type="index" width="60" />
        <el-table-column prop="title" label="Khoá học" min-width="240" />
        <el-table-column prop="teacher" label="GV" width="140" />
        <el-table-column label="Gross" width="140" align="right">
          <template #default="{ row }">{{ money(row.gross) }}</template>
        </el-table-column>
        <el-table-column label="Net" width="140" align="right">
          <template #default="{ row }">{{ money(row.net) }}</template>
        </el-table-column>
        <el-table-column prop="orders" label="Đơn" width="100" align="center" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  reportService,
  type RevenuePoint,
  type RevenueByGateway,
  type RevenueTopCourse,
} from '@/services/report.service'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, PieChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
use([
  CanvasRenderer,
  LineChart,
  PieChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

const components = { VChart }

const range = ref<[string, string] | null>(null)
const gran = ref<'day' | 'week' | 'month'>('day')
const exporting = ref(false)
const loading = reactive({ series: false, pie: false, top: false })

const series = ref<RevenuePoint[]>([])
const byGateway = ref<RevenueByGateway[]>([])
const topCourses = ref<RevenueTopCourse[]>([])

const kpi = reactive({ gross: 0, net: 0, refunds: 0, orders: 0 })
const granLabel = computed(() =>
  gran.value === 'day' ? 'ngày' : gran.value === 'week' ? 'tuần' : 'tháng',
)
const money = (v: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v)

function params() {
  return { from: range.value?.[0], to: range.value?.[1], granularity: gran.value }
}
function applyRange() {
  reload()
}
function reset() {
  range.value = null
  gran.value = 'day'
  reload()
}

async function loadSeries() {
  loading.series = true
  try {
    series.value = await reportService.revenueTimeseries(params())
    // KPI
    const gross = series.value.reduce((a, b) => a + b.gross, 0)
    const net = series.value.reduce((a, b) => a + b.net, 0)
    const refunds = series.value.reduce((a, b) => a + b.refunds, 0)
    kpi.gross = gross
    kpi.net = net
    kpi.refunds = refunds
    kpi.orders = Math.round(gross / 99000)
  } finally {
    loading.series = false
  }
}
async function loadPie() {
  loading.pie = true
  try {
    byGateway.value = await reportService.revenueByGateway(params())
  } finally {
    loading.pie = false
  }
}
async function loadTop() {
  loading.top = true
  try {
    topCourses.value = await reportService.revenueTopCourses(params())
  } finally {
    loading.top = false
  }
}
async function exportCsv() {
  exporting.value = true
  try {
    const blob = await reportService.exportRevenueCsv(params())
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `revenue_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

async function reload() {
  await Promise.all([loadSeries(), loadPie(), loadTop()])
}

onMounted(reload)

// ----- ECharts options -----
const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['Gross', 'Net', 'Refunds'] },
  grid: { left: 32, right: 24, top: 36, bottom: 32 },
  xAxis: { type: 'category', data: series.value.map((x) => x.date) },
  yAxis: { type: 'value' },
  series: [
    { name: 'Gross', type: 'line', smooth: true, data: series.value.map((x) => x.gross) },
    { name: 'Net', type: 'line', smooth: true, data: series.value.map((x) => x.net) },
    { name: 'Refunds', type: 'line', smooth: true, data: series.value.map((x) => x.refunds) },
  ],
}))
const pieOption = computed(() => ({
  tooltip: { trigger: 'item' },
  legend: { top: 8 },
  series: [
    {
      name: 'Gateway',
      type: 'pie',
      radius: ['40%', '70%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      data: byGateway.value.map((x) => ({ name: x.gateway, value: x.amount })),
    },
  ],
}))
</script>
