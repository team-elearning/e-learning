<template>
  <div class="space-y-4">
    <!-- KPIs -->
    <div class="grid grid-cols-2 gap-3 md:grid-cols-4">
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Số giao dịch</div>
        <div class="mt-2 text-2xl font-semibold">{{ metrics.count }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Doanh thu gộp</div>
        <div class="mt-2 text-2xl font-semibold">{{ money(metrics.gross) }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Net</div>
        <div class="mt-2 text-2xl font-semibold">{{ money(metrics.net) }}</div>
      </div>
      <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
        <div class="text-xs text-gray-500">Hoàn tiền (ước)</div>
        <div class="mt-2 text-2xl font-semibold">{{ money(metrics.refunds) }}</div>
      </div>
    </div>

    <!-- Toolbar -->
    <div class="grid grid-cols-1 items-start gap-3 md:grid-cols-4 xl:grid-cols-7">
      <el-input
        v-model="query.q"
        clearable
        placeholder="Tìm theo Mã GD / email / khoá học"
        @keyup.enter="applyFilters"
        @clear="applyFilters"
        class="md:col-span-2 xl:col-span-2 w-full"
      >
        <template #prefix>🔎</template>
      </el-input>

      <el-select v-model="query.status" clearable placeholder="Trạng thái" @change="applyFilters">
        <el-option label="Pending" value="Pending" />
        <el-option label="Processing" value="Processing" />
        <el-option label="Succeeded" value="Succeeded" />
        <el-option label="Failed" value="Failed" />
        <el-option label="Refunded" value="Refunded" />
        <el-option label="Disputed" value="Disputed" />
      </el-select>

      <el-select
        v-model="query.gateway"
        clearable
        placeholder="Cổng thanh toán"
        @change="applyFilters"
      >
        <el-option label="VNPay" value="VNPay" />
        <el-option label="Momo" value="Momo" />
        <el-option label="QR" value="QR" />
        <el-option label="Ngân hàng" value="Bank" />
      </el-select>

      <div class="md:col-span-2 xl:col-span-2">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          unlink-panels
          range-separator="–"
          start-placeholder="Từ ngày"
          end-placeholder="Đến ngày"
          value-format="YYYY-MM-DD"
          class="w-full"
          @change="applyDateRange"
        />
      </div>

      <div class="xl:col-span-1 flex items-center gap-2 md:justify-end">
        <el-button @click="resetFilters">Xoá lọc</el-button>
        <el-button type="primary" plain @click="applyFilters">Lọc</el-button>
      </div>
    </div>

    <!-- Table -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="mb-3 flex items-center justify-between">
        <div class="text-sm text-gray-600">Tổng: {{ total }}</div>
        <div class="flex items-center gap-2">
          <el-button @click="doExport" :loading="exporting">Xuất CSV</el-button>
          <el-button type="primary" @click="refresh" :loading="loading">Tải lại</el-button>
        </div>
      </div>

      <el-table :data="items" v-loading="loading" height="560" @row-dblclick="goDetail">
        <el-table-column prop="id" label="Mã GD" min-width="140" />
        <el-table-column label="Người mua" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="font-medium text-gray-800">{{ row.buyerName }}</div>
            <div class="text-xs text-gray-500">{{ row.buyerEmail }}</div>
          </template>
        </el-table-column>
        <el-table-column label="Khoá học" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ row.courseTitle }}</template>
        </el-table-column>
        <el-table-column prop="gateway" label="Cổng" width="110" />
        <el-table-column label="Số tiền" width="130" align="right">
          <template #default="{ row }">{{ money(row.amount) }}</template>
        </el-table-column>
        <el-table-column prop="status" label="Trạng thái" width="130" align="center">
          <template #default="{ row }">
            <el-tag size="small" :type="statusTagType(row.status)">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="createdAt" label="Thời gian" min-width="170">
          <template #default="{ row }">{{ fmt(row.createdAt) }}</template>
        </el-table-column>

        <el-table-column fixed="right" width="260">
          <template #default="{ row }">
            <div class="flex justify-end gap-2">
              <el-button size="small" @click="goDetail(row)">Xem</el-button>
              <el-button
                size="small"
                type="warning"
                plain
                v-if="row.status === 'Succeeded'"
                @click="promptRefund(row)"
              >
                Hoàn tiền
              </el-button>
              <el-button
                size="small"
                type="danger"
                plain
                v-if="row.status !== 'Disputed'"
                @click="markDispute(row)"
              >
                Tranh chấp
              </el-button>
            </div>
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  paymentService,
  type TxSummary,
  type TxStatus,
  type Gateway,
  type PageParams,
  type TxMetrics,
} from '@/services/payment.service'

const router = useRouter()

// state
const items = ref<TxSummary[]>([])
const total = ref(0)
let page = ref(1)
const pageSize = 20
const loading = ref(false)
const exporting = ref(false)
const metrics = reactive<TxMetrics>({ count: 0, gross: 0, net: 0, refunds: 0, disputed: 0 })

const query = reactive<PageParams>({
  q: '',
  status: undefined,
  gateway: undefined,
  page: page.value,
  pageSize,
})
const dateRange = ref<[string, string] | null>(null)

// helpers
const fmt = (iso?: string) => (iso ? new Date(iso).toLocaleString('vi-VN') : '')
const money = (v: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v)
const statusTagType = (s: TxStatus) =>
  s === 'Succeeded'
    ? 'success'
    : s === 'Processing'
      ? 'warning'
      : s === 'Pending'
        ? 'info'
        : s === 'Refunded'
          ? 'info'
          : s === 'Disputed'
            ? 'danger'
            : 'danger'

// actions
function applyDateRange() {
  query.from = dateRange.value?.[0]
  query.to = dateRange.value?.[1]
  applyFilters()
}
function resetFilters() {
  query.q = ''
  query.status = undefined
  query.gateway = undefined
  query.from = undefined
  query.to = undefined
  dateRange.value = null
  page.value = 1
  fetch()
}
function applyFilters() {
  page.value = 1
  fetch()
}

async function fetch() {
  loading.value = true
  try {
    const { items: rows, total: t } = await paymentService.list({
      ...query,
      page: page.value,
      pageSize,
    })
    items.value = rows
    total.value = t
    const m = await paymentService.metrics({ ...query })
    Object.assign(metrics, m)
  } finally {
    loading.value = false
  }
}
function refresh() {
  fetch()
}
function goDetail(row: TxSummary) {
  router.push(`/admin/transactions/${row.id}`)
}

async function doExport() {
  try {
    exporting.value = true
    const blob = await paymentService.exportCsv({ ...query })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `transactions_${new Date().toISOString().slice(0, 10)}.csv`
    a.click()
    URL.revokeObjectURL(url)
  } finally {
    exporting.value = false
  }
}

async function promptRefund(row: TxSummary) {
  const { value, action } = await ElMessageBox.prompt(
    `Nhập số tiền muốn hoàn (<= ${money(row.amount)})`,
    `Hoàn tiền ${row.id}`,
    { inputValue: String(row.amount), inputPattern: /^\d+$/, inputErrorMessage: 'Không hợp lệ' },
  )
  if (action === 'confirm') {
    await paymentService.refund(row.id, Number(value))
    ElMessage.success('Đã tạo yêu cầu hoàn tiền (mock)')
    fetch()
  }
}
async function markDispute(row: TxSummary) {
  const { value, action } = await ElMessageBox.prompt(
    'Ghi chú cho tranh chấp (tuỳ chọn)',
    `Đánh dấu tranh chấp ${row.id}`,
  )
  if (action === 'confirm') {
    await paymentService.markDispute(row.id, value)
    ElMessage.success('Đã đánh dấu tranh chấp (mock)')
    fetch()
  }
}

onMounted(fetch)
</script>
