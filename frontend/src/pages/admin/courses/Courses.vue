<template>
  <div class="space-y-4">
    <!-- Toolbar -->
    <div class="grid grid-cols-1 gap-3 md:grid-cols-4 xl:grid-cols-6 items-start">
      <el-input
        v-model="query.q"
        clearable
        placeholder="Tìm tên / mã / giáo viên"
        @clear="applyFilters"
        @keyup.enter="applyFilters"
        class="md:col-span-2 xl:col-span-2 w-full"
      >
        <template #prefix>🔎</template>
      </el-input>

      <el-select v-model="query.grade" clearable placeholder="Lớp" @change="applyFilters">
        <el-option v-for="g in [1, 2, 3, 4, 5]" :key="g" :label="`Lớp ${g}`" :value="g" />
      </el-select>

      <el-select v-model="query.subject" clearable placeholder="Môn" @change="applyFilters">
        <el-option v-for="s in subjects" :key="s.value" :label="s.label" :value="s.value" />
      </el-select>

      <el-select
        v-model="query.teacherId"
        clearable
        filterable
        placeholder="Giáo viên"
        @change="applyFilters"
      >
        <el-option v-for="t in teachers" :key="t.id" :label="t.name" :value="t.id" />
      </el-select>

      <el-select
        v-model="query.status"
        clearable
        placeholder="Trạng thái"
        @change="applyFilters"
        class="xl:col-span-1"
      >
        <el-option label="Bản nháp" value="draft" />
        <el-option label="Chờ duyệt" value="pending_review" />
        <el-option label="Đã xuất bản" value="published" />
        <el-option label="Từ chối" value="rejected" />
        <el-option label="Lưu trữ" value="archived" />
      </el-select>

      <div class="md:col-span-2 xl:col-span-2 min-w-0">
        <el-date-picker
          v-model="dateRange"
          type="daterange"
          unlink-panels
          range-separator="–"
          start-placeholder="Tạo từ"
          end-placeholder="đến"
          value-format="YYYY-MM-DD"
          class="w-full"
          @change="applyDateRange"
        />
      </div>

      <div class="md:col-span-2 xl:col-span-1 flex items-center gap-2 md:justify-end">
        <el-button @click="resetFilters">Xoá lọc</el-button>
        <el-button type="primary" plain @click="applyFilters">Lọc</el-button>
      </div>
    </div>

    <!-- Table -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="mb-3 flex items-center justify-between">
        <div class="text-sm text-gray-600">Tổng: {{ total }}</div>
        <div class="flex items-center gap-2">
          <el-button @click="goApproval">Hàng chờ duyệt</el-button>
          <el-button type="primary" @click="refresh" :loading="loading">Tải lại</el-button>
        </div>
      </div>

      <el-table :data="items" v-loading="loading" height="560" @row-dblclick="goDetail">
        <el-table-column label="" width="72">
          <template #default="{ row }">
            <img :src="row.thumbnail" class="h-10 w-16 rounded object-cover" />
          </template>
        </el-table-column>

        <el-table-column prop="title" label="Khoá học" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">
            <div
              class="font-medium text-gray-800 hover:text-blue-600 cursor-pointer"
              @click="goDetail(row)"
            >
              {{ row.title }}
            </div>
            <div class="text-xs text-gray-500">GV: {{ row.teacherName }}</div>
          </template>
        </el-table-column>

        <el-table-column label="Lớp/Môn" width="140">
          <template #default="{ row }">
            <div class="text-sm">Lớp {{ row.grade }}</div>
            <div class="text-xs text-gray-500">{{ subjectName(row.subject) }}</div>
          </template>
        </el-table-column>

        <el-table-column prop="lessonsCount" label="Bài" width="80" align="center" />
        <el-table-column prop="enrollments" label="HV" width="90" align="center" />

        <el-table-column prop="status" label="Trạng thái" width="140" align="center">
          <template #default="{ row }">
            <el-tag :type="statusTagType(row.status)" size="small">{{
              statusLabel(row.status)
            }}</el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="updatedAt" label="Cập nhật" min-width="160">
          <template #default="{ row }">{{ fmtDate(row.updatedAt) }}</template>
        </el-table-column>

        <el-table-column fixed="right" label="" width="250">
          <template #default="{ row }">
            <div class="flex gap-2 justify-end">
              <el-button size="small" @click="goDetail(row)">Xem</el-button>
              <el-button
                v-if="row.status !== 'published' && row.status !== 'archived'"
                size="small"
                type="success"
                plain
                @click="publish(row)"
                >Xuất bản</el-button
              >
              <el-button v-if="row.status === 'published'" size="small" @click="unpublish(row)"
                >Gỡ</el-button
              >
              <el-button
                v-if="row.status !== 'archived'"
                size="small"
                type="warning"
                plain
                @click="archive(row)"
                >Lưu trữ</el-button
              >
              <el-button v-else size="small" type="info" plain @click="restore(row)"
                >Khôi phục</el-button
              >
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
  type CourseStatus,
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

const query = reactive<PageParams>({
  q: '',
  grade: undefined,
  subject: undefined,
  teacherId: undefined,
  status: undefined,
  page: page.value,
  pageSize,
})
const dateRange = ref<[string, string] | null>(null)

function subjectName(s: Subject) {
  return subjects.find((x) => x.value === s)?.label || s
}
function statusLabel(s: CourseStatus) {
  return s === 'draft'
    ? 'Bản nháp'
    : s === 'pending_review'
      ? 'Chờ duyệt'
      : s === 'published'
        ? 'Đã xuất bản'
        : s === 'rejected'
          ? 'Từ chối'
          : 'Lưu trữ'
}
function statusTagType(s: CourseStatus) {
  return s === 'draft'
    ? 'info'
    : s === 'pending_review'
      ? 'warning'
      : s === 'published'
        ? 'success'
        : s === 'rejected'
          ? 'danger'
          : 'info'
}
const fmtDate = (iso?: string) => (iso ? new Date(iso).toLocaleString('vi-VN') : '')

function applyDateRange() {
  query.from = dateRange.value?.[0]
  query.to = dateRange.value?.[1]
  applyFilters()
}
function resetFilters() {
  query.q = ''
  query.grade = undefined
  query.subject = undefined
  query.teacherId = undefined
  query.status = undefined
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
    const { items: rows, total: t } = await courseService.list({
      ...query,
      page: page.value,
      pageSize,
    })
    items.value = rows
    total.value = t
  } finally {
    loading.value = false
  }
}
function refresh() {
  fetch()
}

function goDetail(row: CourseSummary) {
  router.push(`/admin/courses/${row.id}`)
}
function goApproval() {
  router.push('/admin/courses/approval')
}

// Actions
async function publish(row: CourseSummary) {
  await ElMessageBox.confirm(`Xuất bản khoá “${row.title}”?`, 'Xác nhận')
  await courseService.publish(row.id)
  ElMessage.success('Đã xuất bản (mock)')
  fetch()
}
async function unpublish(row: CourseSummary) {
  await ElMessageBox.confirm(`Gỡ xuất bản khoá “${row.title}”?`, 'Xác nhận')
  await courseService.unpublish(row.id)
  ElMessage.success('Đã gỡ (mock)')
  fetch()
}
async function archive(row: CourseSummary) {
  await ElMessageBox.confirm(`Lưu trữ khoá “${row.title}”?`, 'Xác nhận', { type: 'warning' })
  await courseService.archive(row.id)
  ElMessage.success('Đã lưu trữ (mock)')
  fetch()
}
async function restore(row: CourseSummary) {
  await courseService.restore(row.id)
  ElMessage.success('Đã khôi phục (mock)')
  fetch()
}

onMounted(async () => {
  teachers.value = await courseService.listTeachers()
  fetch()
})
</script>
