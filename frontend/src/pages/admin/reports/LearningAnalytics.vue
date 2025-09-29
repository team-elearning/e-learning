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
    <div class="grid grid-cols-3 gap-3">
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Hoàn thành TB</div>
        <div class="mt-2 text-2xl font-semibold">{{ kpi.avgCompletion }}%</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Điểm TB Quiz</div>
        <div class="mt-2 text-2xl font-semibold">{{ kpi.avgScore }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Thời gian học TB</div>
        <div class="mt-2 text-2xl font-semibold">{{ kpi.avgTimeSpentMin }} phút</div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <div class="xl:col-span-2 rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-2 font-semibold">Tỉ lệ hoàn thành theo ngày</div>
        <v-chart :option="lineOption" autoresize style="height: 320px" />
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-2 font-semibold">Điểm TB theo môn</div>
        <v-chart :option="barOption" autoresize style="height: 320px" />
      </div>
    </div>

    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="mb-2 font-semibold">Học sinh có nguy cơ tụt</div>
      <el-table :data="atRisk" height="420" v-loading="loading.table">
        <el-table-column prop="userId" label="ID" width="90" />
        <el-table-column prop="name" label="Học sinh" min-width="200" />
        <el-table-column prop="className" label="Lớp" width="120" />
        <el-table-column prop="progress" label="Tiến độ (%)" width="140" align="center" />
        <el-table-column label="Hoạt động cuối" min-width="180">
          <template #default="{ row }">{{ fmt(row.lastActiveAt) }}</template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  reportService,
  type LearningKPIs,
  type CompletionPoint,
  type ScoreBySubject,
  type AtRiskRow,
} from '@/services/report.service'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { LineChart, BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
use([
  CanvasRenderer,
  LineChart,
  BarChart,
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
])

const components = { VChart }

const range = ref<[string, string] | null>(null)
const exporting = ref(false)

const kpi = reactive<LearningKPIs>({ avgCompletion: 0, avgScore: 0, avgTimeSpentMin: 0 })
const completion = ref<CompletionPoint[]>([])
const scores = ref<ScoreBySubject[]>([])
const atRisk = ref<AtRiskRow[]>([])
const loading = reactive({ table: false })

function params() {
  return { from: range.value?.[0], to: range.value?.[1] }
}
function reset() {
  range.value = null
  reload()
}
function fmt(iso?: string) {
  return iso ? new Date(iso).toLocaleString('vi-VN') : ''
}

async function exportCsv() {
  exporting.value = true
  try {
    const blob = await reportService.exportLearningCsv(params())
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `learning_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

async function reload() {
  const [k, c, s] = await Promise.all([
    reportService.learningKpis(params()),
    reportService.completionSeries(params()),
    reportService.scoreBySubject(params()),
  ])
  Object.assign(kpi, k)
  completion.value = c
  scores.value = s
  loading.table = true
  try {
    atRisk.value = await reportService.atRiskStudents(params())
  } finally {
    loading.table = false
  }
}

onMounted(reload)

const lineOption = computed(() => ({
  tooltip: { trigger: 'axis' },
  grid: { left: 32, right: 24, top: 24, bottom: 32 },
  xAxis: { type: 'category', data: completion.value.map((x) => x.date) },
  yAxis: { type: 'value', max: 100 },
  series: [
    {
      name: 'Completion %',
      type: 'line',
      smooth: true,
      data: completion.value.map((x) => x.completion),
    },
  ],
}))
const barOption = computed(() => ({
  tooltip: {},
  grid: { left: 40, right: 16, top: 24, bottom: 40 },
  xAxis: { type: 'category', data: scores.value.map((x) => x.subject) },
  yAxis: { type: 'value', max: 100 },
  series: [{ name: 'Avg Score', type: 'bar', data: scores.value.map((x) => x.avgScore) }],
}))
</script>
