<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex min-w-0 items-center gap-4">
          <img :src="detail.thumbnail" class="h-16 w-28 rounded object-cover" />
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="truncate text-xl font-semibold text-gray-800">{{ detail.title }}</h2>
              <el-tag size="small">Lớp {{ detail.grade }}</el-tag>
              <el-tag size="small" type="info">{{ subjectName(detail.subject) }}</el-tag>
              <el-tag size="small" :type="statusTagType(detail.status)">{{
                statusLabel(detail.status)
              }}</el-tag>
            </div>
            <div class="mt-1 text-sm text-gray-500">
              GV: {{ detail.teacherName }} • {{ detail.lessonsCount }} bài •
              {{ detail.enrollments }} HV
            </div>
            <div class="mt-1 text-xs text-gray-500">
              Cập nhật: <b>{{ fmtDate(detail.updatedAt) }}</b>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <el-button v-if="detail.status === 'pending_review'" type="success" plain @click="approve"
            >Duyệt</el-button
          >
          <el-button v-if="detail.status === 'pending_review'" type="danger" plain @click="reject"
            >Từ chối</el-button
          >

          <el-button
            v-if="detail.status !== 'published' && detail.status !== 'archived'"
            type="success"
            @click="publish"
            >Xuất bản</el-button
          >
          <el-button v-if="detail.status === 'published'" @click="unpublish">Gỡ</el-button>

          <el-button v-if="detail.status !== 'archived'" type="warning" plain @click="archive"
            >Lưu trữ</el-button
          >
          <el-button v-else type="info" plain @click="restore">Khôi phục</el-button>
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab">
      <el-tab-pane label="Tổng quan" name="overview">
        <div
          class="rounded-lg bg-white p-4 ring-1 ring-black/5 grid grid-cols-1 gap-4 md:grid-cols-3"
        >
          <div class="md:col-span-2 space-y-3">
            <div class="text-gray-700 whitespace-pre-line" v-if="detail.description">
              {{ detail.description }}
            </div>
            <div class="grid grid-cols-3 gap-3">
              <div class="rounded border p-3">
                <div class="text-xs text-gray-500">Trình độ</div>
                <div class="mt-1 font-medium">{{ levelLabel(detail.level) }}</div>
              </div>
              <div class="rounded border p-3">
                <div class="text-xs text-gray-500">Thời lượng</div>
                <div class="mt-1 font-medium">{{ minutes(detail.durationMinutes) }}</div>
              </div>
              <div class="rounded border p-3">
                <div class="text-xs text-gray-500">Bài học</div>
                <div class="mt-1 font-medium">{{ detail.lessonsCount }}</div>
              </div>
            </div>
          </div>
          <div class="space-y-3">
            <div class="rounded border p-3">
              <div class="text-xs text-gray-500">Giáo viên</div>
              <div class="mt-1 font-medium">{{ detail.teacherName }}</div>
            </div>
            <div class="rounded border p-3">
              <div class="text-xs text-gray-500">Trạng thái</div>
              <div class="mt-1">
                <el-tag :type="statusTagType(detail.status)">{{
                  statusLabel(detail.status)
                }}</el-tag>
              </div>
            </div>
            <div class="rounded border p-3">
              <div class="text-xs text-gray-500">Ngày tạo</div>
              <div class="mt-1 font-medium">{{ fmtDate(detail.createdAt) }}</div>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <el-tab-pane label="Chương trình học" name="curriculum">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5 space-y-4">
          <div v-for="sec in detail.sections" :key="sec.id" class="rounded border p-3">
            <div class="mb-2 flex items-center justify-between">
              <div class="font-semibold">Chương {{ sec.order }}: {{ sec.title }}</div>
              <div class="text-xs text-gray-500">{{ sec.lessons.length }} bài</div>
            </div>
            <el-table :data="sec.lessons" size="small">
              <el-table-column type="index" label="#" width="50" />
              <el-table-column prop="title" label="Bài học" min-width="220" />
              <el-table-column prop="type" label="Loại" width="120">
                <template #default="{ row }">{{ typeLabel(row.type) }}</template>
              </el-table-column>
              <el-table-column prop="durationMinutes" label="Thời lượng" width="120">
                <template #default="{ row }">{{ minutes(row.durationMinutes) }}</template>
              </el-table-column>
              <el-table-column prop="isPreview" label="Học thử" width="110" align="center">
                <template #default="{ row }">
                  <el-tag v-if="row.isPreview" type="success" size="small">Có</el-tag>
                  <span v-else>—</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  courseService,
  type CourseDetail,
  type CourseStatus,
  type Subject,
  type Level,
} from '@/services/course.service'

const route = useRoute()
const id = computed(() => route.params.id as string)

const activeTab = ref<'overview' | 'curriculum'>('overview')
const detail = reactive<CourseDetail>({
  id: id.value,
  title: '',
  grade: 1,
  subject: 'math',
  teacherId: 0,
  teacherName: '',
  lessonsCount: 0,
  enrollments: 0,
  status: 'draft',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
  sections: [],
})

const subjects = courseService.subjects()
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
const typeLabel = (t: 'video' | 'pdf' | 'quiz') =>
  t === 'video' ? 'Video' : t === 'pdf' ? 'Tài liệu' : 'Quiz'
const levelLabel = (l?: Level) => (l === 'advanced' ? 'Nâng cao' : 'Cơ bản')
const minutes = (m?: number) => (m ? `${m} phút` : '—')

async function load() {
  const d = await courseService.detail(id.value)
  Object.assign(detail, d)
}

// Actions
async function approve() {
  await ElMessageBox.confirm('Duyệt khoá học này?', 'Xác nhận', { type: 'success' })
  await courseService.approve(detail.id)
  detail.status = 'published' // tuỳ quy trình: duyệt có thể vẫn ở trạng thái “đã duyệt, chưa xuất bản”
  ElMessage.success('Đã duyệt (mock)')
}
async function reject() {
  const { value, action } = await ElMessageBox.prompt('Lý do từ chối', 'Từ chối', {
    inputPlaceholder: 'Thiếu tài liệu, video mờ…',
  })
  if (action === 'confirm') {
    await courseService.reject(detail.id, value)
    detail.status = 'rejected'
    ElMessage.success('Đã từ chối (mock)')
  }
}
async function publish() {
  await courseService.publish(detail.id)
  detail.status = 'published'
  ElMessage.success('Đã xuất bản (mock)')
}
async function unpublish() {
  await courseService.unpublish(detail.id)
  detail.status = 'draft'
  ElMessage.success('Đã gỡ (mock)')
}
async function archive() {
  await ElMessageBox.confirm('Lưu trữ khoá học này?', 'Xác nhận', { type: 'warning' })
  await courseService.archive(detail.id)
  detail.status = 'archived'
  ElMessage.success('Đã lưu trữ (mock)')
}
async function restore() {
  await courseService.restore(detail.id)
  detail.status = 'draft'
  ElMessage.success('Đã khôi phục (mock)')
}

onMounted(load)
watch(() => route.params.id, load)
</script>
