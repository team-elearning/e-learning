<template>
  <div class="space-y-4">
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="mb-2 font-semibold">Xuất báo cáo</div>
      <div class="grid grid-cols-1 gap-3 md:grid-cols-3">
        <el-select v-model="type" placeholder="Loại báo cáo">
          <el-option label="Doanh thu" value="revenue" />
          <el-option label="Người dùng" value="users" />
          <el-option label="Học tập" value="learning" />
          <el-option label="Nội dung" value="content" />
        </el-select>

        <el-date-picker
          v-model="range"
          type="daterange"
          unlink-panels
          range-separator="–"
          start-placeholder="Từ ngày"
          end-placeholder="Đến ngày"
          value-format="YYYY-MM-DD"
        />

        <div class="flex items-center gap-2">
          <el-button :disabled="!type" type="primary" @click="exportNow" :loading="exporting"
            >Xuất CSV</el-button
          >
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { reportService } from '@/services/report.service'

const type = ref<'revenue' | 'users' | 'learning' | 'content' | ''>('')
const range = ref<[string, string] | null>(null)
const exporting = ref(false)

function params() {
  return { from: range.value?.[0], to: range.value?.[1] }
}

async function exportNow() {
  if (!type.value) return
  exporting.value = true
  try {
    let blob: Blob
    if (type.value === 'revenue') blob = await reportService.exportRevenueCsv(params())
    else if (type.value === 'users') blob = await reportService.exportUsersCsv(params())
    else if (type.value === 'learning') blob = await reportService.exportLearningCsv(params())
    else blob = await reportService.exportContentCsv(params())
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${type.value}_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}
</script>
