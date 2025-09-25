<template>
  <div class="space-y-4">
    <div class="grid grid-cols-1 items-start gap-3 md:grid-cols-3">
      <el-date-picker
        v-model="range"
        type="daterange"
        unlink-panels
        range-separator="–"
        start-placeholder="Từ ngày"
        end-placeholder="Đến ngày"
        value-format="YYYY-MM-DD"
        class="md:col-span-2 w-full"
        @change="reload"
      />
      <div class="flex items-center gap-2 md:justify-end">
        <el-button @click="reset">Xoá</el-button>
        <el-button type="primary" plain @click="reload">Lọc</el-button>
        <el-button @click="exportCsv" :loading="exporting">Xuất CSV</el-button>
      </div>
    </div>

    <!-- KPIs -->
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">DAU</div>
        <div class="mt-1 text-2xl font-semibold">{{ kpi.dau }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">MAU</div>
        <div class="mt-1 text-2xl font-semibold">{{ kpi.mau }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Người dùng mới</div>
        <div class="mt-1 text-2xl font-semibold">{{ kpi.newUsers }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Đang hoạt động</div>
        <div class="mt-1 text-2xl font-semibold">{{ kpi.activeUsers }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <div class="xl:col-span-2 rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-2 font-semibold">Hoạt động người dùng theo ngày</div>
        <v-chart :option="lineOption" autoresize style="height: 360px" />
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-2 font-semibold">Phân bố theo vai trò</div>
        <v-chart :option="roleOption" autoresize style="height: 360px" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  reportService,
  type UserKPIs,
  type UserSeriesPoint,
  type UserByRole,
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
const exporting = ref(false)
const kpi = reactive<UserKPIs>({ dau: 0, mau: 0, newUsers: 0, activeUsers: 0 })
const series = ref<UserSeriesPoint[]>([])
const byRole = ref<UserByRole[]>([])

function params() {
  return { from: range.value?.[0], to: range.value?.[1] }
}
function reset() {
  range.value = null
  reload()
}
async function exportCsv() {
  exporting.value = true
  try {
    const blob = await reportService.exportUsersCsv(params())
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `users_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

async function reload() {
  kpi.dau = kpi.mau = kpi.newUsers = kpi.activeUsers = 0
  series.value = []
  byRole.value = []
  const [k, s, r] = await Promise.all([
    reportService.userKpis(params()),
    reportService.userSeries(params()),
    reportService.userByRole(params()),
  ])
  Object.assign(kpi, k)
  series.value = s
  byRole.value = r
}

onMounted(reload)

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  legend: { data: ['DAU', 'New Users'] },
  grid: { left: 32, right: 24, top: 36, bottom: 32 },
  xAxis: { type: 'category', data: series.value.map((x) => x.date) },
  yAxis: { type: 'value' },
  series: [
    { name: 'DAU', type: 'line', smooth: true, data: series.value.map((x) => x.dau) },
    { name: 'New Users', type: 'line', smooth: true, data: series.value.map((x) => x.newUsers) },
  ],
}))
const roleOption = computed(() => ({
  tooltip: { trigger: 'item' },
  series: [
    {
      name: 'Role',
      type: 'pie',
      radius: ['40%', '70%'],
      itemStyle: { borderRadius: 6, borderColor: '#fff', borderWidth: 2 },
      data: byRole.value.map((x) => ({ name: x.role, value: x.count })),
    },
  ],
}))
</script>
