<template>
  <div class="space-y-4">
    <div class="flex flex-wrap items-center gap-2">
      <el-input
        v-model="query.q"
        placeholder="Tìm theo tên / GV"
        clearable
        @keyup.enter="apply"
        @clear="apply"
      >
        <template #prefix>🔎</template>
      </el-input>
      <el-select v-model="query.subject" clearable placeholder="Môn" @change="apply">
        <el-option v-for="s in subjects" :key="s.value" :label="s.label" :value="s.value" />
      </el-select>
      <el-select
        v-model="query.teacherId"
        clearable
        filterable
        placeholder="Giáo viên"
        @change="apply"
      >
        <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>
      <el-button @click="reset">Xoá lọc</el-button>
      <el-button type="primary" plain @click="apply">Lọc</el-button>
      <div class="ml-auto flex items-center gap-2">
        <el-button type="success" :disabled="selIds.length === 0" @click="bulkApprove"
          >Duyệt {{ selIds.length }}</el-button
        >
        <el-button type="danger" :disabled="selIds.length === 0" @click="bulkReject"
          >Từ chối {{ selIds.length }}</el-button
        >
      </div>
    </div>

    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <el-table :data="items" v-loading="loading" height="560" @selection-change="onSelection">
        <el-table-column type="selection" width="42" fixed="left" />
        <el-table-column label="" width="72">
          <template #default="{ row }"
            ><img :src="row.thumbnail" class="h-10 w-16 rounded object-cover"
          /></template>
        </el-table-column>
        <el-table-column label="Khoá học" min-width="260" show-overflow-tooltip>
          <template #default="{ row }">
            <div class="font-medium text-gray-800">{{ row.title }}</div>
            <div class="text-xs text-gray-500">
              GV: {{ row.teacherName }} • Lớp {{ row.grade }} • {{ subjectName(row.subject) }}
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="lessonsCount" label="Bài" width="80" align="center" />
        <el-table-column prop="updatedAt" label="Cập nhật" min-width="160">
          <template #default="{ row }">{{ fmtDate(row.updatedAt) }}</template>
        </el-table-column>
        <el-table-column fixed="right" width="240">
          <template #default="{ row }">
            <div class="flex justify-end gap-2">
              <el-button size="small" type="success" plain @click="approve(row)">Duyệt</el-button>
              <el-button size="small" type="danger" plain @click="reject(row)">Từ chối</el-button>
              <el-button size="small" @click="view(row)">Xem</el-button>
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
  courseService,
  type CourseSummary,
  type PageParams,
  type Subject,
} from '@/services/course.service'

const router = useRouter()
const subjects = courseService.subjects()
const teachers = ref<{ id: number | string; name: string }[]>([])
const items = ref<CourseSummary[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 20
const loading = ref(false)
const selIds = ref<(number | string)[]>([])

const query = reactive<PageParams>({ q: '', subject: undefined, teacherId: undefined })

function subjectName(s: Subject) {
  return subjects.find((x) => x.value === s)?.label || s
}
const fmtDate = (iso?: string) => (iso ? new Date(iso).toLocaleString('vi-VN') : '')

async function fetch() {
  loading.value = true
  try {
    const { items: rows, total: t } = await courseService.list({
      ...query,
      status: 'pending_review',
      page: page.value,
      pageSize,
    })
    items.value = rows
    total.value = t
  } finally {
    loading.value = false
  }
}
function onSelection(rows: CourseSummary[]) {
  selIds.value = rows.map((r) => r.id)
}
function reset() {
  query.q = ''
  query.subject = undefined
  query.teacherId = undefined
  page.value = 1
  fetch()
}
function apply() {
  page.value = 1
  fetch()
}

async function approve(row: CourseSummary) {
  await ElMessageBox.confirm(`Duyệt khoá “${row.title}”?`, 'Xác nhận', { type: 'success' })
  await courseService.approve(row.id)
  ElMessage.success('Đã duyệt (mock)')
  fetch()
}
async function reject(row: CourseSummary) {
  const { value, action } = await ElMessageBox.prompt(
    'Lý do từ chối (tuỳ chọn)',
    'Từ chối khoá học',
    { inputPlaceholder: 'Ví dụ: thiếu tài liệu, video mờ…' },
  )
  if (action === 'confirm') {
    await courseService.reject(row.id, value)
    ElMessage.success('Đã từ chối (mock)')
    fetch()
  }
}
async function bulkApprove() {
  await ElMessageBox.confirm(`Duyệt ${selIds.value.length} khoá đã chọn?`, 'Xác nhận', {
    type: 'success',
  })
  await courseService.bulkApprove(selIds.value)
  ElMessage.success('Đã duyệt (mock)')
  fetch()
}
async function bulkReject() {
  const { value, action } = await ElMessageBox.prompt(
    `Nhập lý do từ chối (áp dụng cho ${selIds.value.length} khoá)`,
    'Từ chối hàng loạt',
  )
  if (action === 'confirm') {
    await courseService.bulkReject(selIds.value, value)
    ElMessage.success('Đã từ chối (mock)')
    fetch()
  }
}
function view(row: CourseSummary) {
  router.push(`/admin/courses/${row.id}`)
}

onMounted(async () => {
  teachers.value = await courseService.listTeachers()
  fetch()
})
</script>
