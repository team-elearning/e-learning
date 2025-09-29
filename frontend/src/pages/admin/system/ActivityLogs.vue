<template>
  <div class="space-y-4">
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="flex items-center justify-between">
        <div class="text-lg font-semibold">Nhật ký hoạt động</div>
        <div class="flex items-center gap-2">
          <el-button @click="reset">Xoá lọc</el-button>
          <el-button type="primary" plain @click="apply">Lọc</el-button>
          <el-button :loading="exporting" @click="doExport">Xuất CSV</el-button>
        </div>
      </div>
    </div>

    <!-- Filters -->
    <div class="grid grid-cols-1 gap-3 md:grid-cols-4 xl:grid-cols-8">
      <el-input
        v-model="q"
        placeholder="Tìm (actor/action/target...)"
        clearable
        @keyup.enter="apply"
        @clear="apply"
        class="xl:col-span-2"
      />
      <el-select v-model="role" clearable placeholder="Vai trò" @change="apply">
        <el-option label="Admin" value="admin" />
        <el-option label="Giáo viên" value="teacher" />
        <el-option label="Học sinh" value="student" />
        <el-option label="System" value="system" />
      </el-select>
      <el-input v-model="action" placeholder="Action (vd: user.create)" @keyup.enter="apply" />
      <el-select v-model="targetType" clearable placeholder="Target type" @change="apply">
        <el-option label="user" value="user" />
        <el-option label="course" value="course" />
        <el-option label="exam" value="exam" />
        <el-option label="payment" value="payment" />
        <el-option label="config" value="config" />
        <el-option label="security" value="security" />
        <el-option label="system" value="system" />
      </el-select>
      <el-input v-model="targetId" placeholder="Target ID" @keyup.enter="apply" />
      <el-select v-model="result" clearable placeholder="Kết quả" @change="apply">
        <el-option label="success" value="success" />
        <el-option label="failed" value="failed" />
      </el-select>
      <el-input v-model="ip" placeholder="IP" @keyup.enter="apply" />
      <el-date-picker
        v-model="range"
        type="daterange"
        unlink-panels
        value-format="YYYY-MM-DD"
        start-placeholder="Từ"
        end-placeholder="Đến"
        @change="apply"
      />
    </div>

    <!-- Table -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="mb-2 text-sm text-gray-600">Tổng: {{ total }}</div>
      <el-table :data="items" v-loading="loading" height="560" @row-dblclick="open">
        <el-table-column prop="ts" label="Thời gian" width="180">
          <template #default="{ row }">{{ fmt(row.ts) }}</template>
        </el-table-column>
        <el-table-column label="Actor" min-width="180" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="font-medium">{{ row.actorName }}</div>
            <div class="text-xs text-gray-500">{{ row.actorRole }}</div>
          </template>
        </el-table-column>
        <el-table-column prop="action" label="Action" min-width="180" />
        <el-table-column label="Target" min-width="160" show-overflow-tooltip>
          <template #default="{ row }">{{ row.targetType }} #{{ row.targetId }}</template>
        </el-table-column>
        <el-table-column prop="result" label="KQ" width="90" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="row.result === 'success' ? 'success' : 'danger'">{{
              row.result
            }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="ip" label="IP" width="130" />
        <el-table-column prop="traceId" label="Trace" min-width="160" />
        <el-table-column fixed="right" width="110">
          <template #default="{ row }">
            <el-button size="small" @click="open(row)">Chi tiết</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="mt-3 flex justify-end">
        <el-pagination
          background
          layout="total, prev, pager, next"
          :total="total"
          :current-page="page"
          :page-size="pageSize"
          @current-change="
            (p: number) => {
              page = p
              fetch()
            }
          "
        />
      </div>
    </div>

    <!-- Drawer -->
    <el-drawer v-model="drawer" title="Chi tiết log" size="520px">
      <div v-if="current" class="space-y-3">
        <div class="text-sm">
          ID: <b>{{ current.id }}</b>
        </div>
        <div class="text-sm">Thời gian: {{ fmt(current.ts) }}</div>
        <div class="text-sm">Actor: {{ current.actorName }} ({{ current.actorRole }})</div>
        <div class="text-sm">
          Action: <b>{{ current.action }}</b>
        </div>
        <div class="text-sm">Target: {{ current.targetType }} #{{ current.targetId }}</div>
        <div class="text-sm">
          Kết quả:
          <el-tag size="small" :type="current.result === 'success' ? 'success' : 'danger'">{{
            current.result
          }}</el-tag>
        </div>
        <div class="text-sm">IP: {{ current.ip }} • UA: {{ current.userAgent }}</div>
        <div class="text-sm">Trace: {{ current.traceId }}</div>
        <div class="text-sm">Message: {{ current.message }}</div>
        <div class="text-sm">
          Meta:
          <pre class="bg-gray-50 p-2 rounded overflow-auto">{{ pretty(current.meta) }}</pre>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { logService, type LogItem, type LogQuery } from '@/services/log.service'

const items = ref<LogItem[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const exporting = ref(false)

const q = ref('')
const role = ref<'admin' | 'teacher' | 'student' | 'system' | ''>('')
const action = ref('')
const targetType = ref<LogQuery['targetType'] | ''>('')
const targetId = ref('')
const result = ref<'success' | 'failed' | ''>('')
const ip = ref('')
const range = ref<[string, string] | null>(null)

const drawer = ref(false)
const current = ref<LogItem | null>(null)

function params(): LogQuery {
  return {
    q: q.value || undefined,
    role: (role.value || undefined) as any,
    action: action.value || undefined,
    targetType: (targetType.value || undefined) as any,
    targetId: targetId.value ? Number(targetId.value) : undefined,
    result: (result.value || undefined) as any,
    ip: ip.value || undefined,
    from: range.value?.[0],
    to: range.value?.[1],
    page: page.value,
    pageSize,
  }
}
function reset() {
  q.value =
    role.value =
    action.value =
    targetType.value =
    targetId.value =
    result.value =
    ip.value =
      ''
  range.value = null
  page.value = 1
  fetch()
}
function apply() {
  page.value = 1
  fetch()
}
async function fetch() {
  loading.value = true
  try {
    const { items: rows, total: t } = await logService.list(params())
    items.value = rows
    total.value = t
  } finally {
    loading.value = false
  }
}
function fmt(iso?: string) {
  return iso ? new Date(iso).toLocaleString('vi-VN') : ''
}
function pretty(v: any) {
  try {
    return JSON.stringify(v ?? {}, null, 2)
  } catch {
    return String(v)
  }
}
async function doExport() {
  exporting.value = true
  try {
    const blob = await logService.exportCsv(params())
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `logs_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}
async function open(row: LogItem) {
  current.value = await logService.detail(row.id)
  drawer.value = true
}

onMounted(fetch)
</script>
