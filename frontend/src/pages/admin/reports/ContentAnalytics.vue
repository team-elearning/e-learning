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
        <div class="text-xs text-gray-500">Khoá đã xuất bản</div>
        <div class="mt-2 text-2xl font-semibold">{{ kpi.totalPublished }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Tổng ghi danh</div>
        <div class="mt-2 text-2xl font-semibold">{{ kpi.totalEnrollments }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Đánh giá TB</div>
        <div class="mt-2 text-2xl font-semibold">{{ kpi.avgRating.toFixed(1) }}</div>
      </div>
    </div>

    <div class="grid grid-cols-1 gap-4 xl:grid-cols-3">
      <div class="xl:col-span-1 rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-2 font-semibold">Lượt xem theo môn</div>
        <v-chart :option="barOption" autoresize style="height: 320px" />
      </div>
      <div class="xl:col-span-2 rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="mb-2 font-semibold">Top nội dung phổ biến</div>
        <el-table :data="tops" height="320">
          <el-table-column type="index" width="60" />
          <el-table-column prop="title" label="Khoá học" min-width="240" />
          <el-table-column prop="views" label="Views" width="120" align="right" />
          <el-table-column prop="enrollments" label="Enrolls" width="120" align="right" />
          <el-table-column prop="rating" label="Rating" width="120" align="center" />
        </el-table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import {
  reportService,
  type ContentKPIs,
  type ViewsBySubject,
  type TopContentRow,
} from '@/services/report.service'
import VChart from 'vue-echarts'
import { use } from 'echarts/core'
import { CanvasRenderer } from 'echarts/renderers'
import { BarChart } from 'echarts/charts'
import {
  GridComponent,
  TooltipComponent,
  LegendComponent,
  TitleComponent,
} from 'echarts/components'
use([CanvasRenderer, BarChart, GridComponent, TooltipComponent, LegendComponent, TitleComponent])

const components = { VChart }

const range = ref<[string, string] | null>(null)
const exporting = ref(false)

const kpi = reactive<ContentKPIs>({ totalPublished: 0, totalEnrollments: 0, avgRating: 0 })
const subjectViews = ref<ViewsBySubject[]>([])
const tops = ref<TopContentRow[]>([])

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
    const blob = await reportService.exportContentCsv(params())
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `content_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

async function reload() {
  const [k, v, t] = await Promise.all([
    reportService.contentKpis(params()),
    reportService.viewsBySubject(params()),
    reportService.topContents(params()),
  ])
  Object.assign(kpi, k)
  subjectViews.value = v
  tops.value = t
}

onMounted(reload)

const barOption = computed(() => ({
  tooltip: {},
  grid: { left: 40, right: 16, top: 24, bottom: 40 },
  xAxis: { type: 'category', data: subjectViews.value.map((x) => x.subject) },
  yAxis: { type: 'value' },
  series: [{ name: 'Views', type: 'bar', data: subjectViews.value.map((x) => x.views) }],
}))
</script>
