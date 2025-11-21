<template>
  <div class="space-y-4">
    <!-- HEADER -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <!-- Left -->
        <div class="flex min-w-0 items-center gap-4">
          <img :src="thumbnail" class="h-16 w-28 rounded object-cover bg-gray-100 border" />

          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="truncate text-xl font-semibold text-gray-800">
                {{ detail?.title || 'Đang tải...' }}
              </h2>

              <el-tag size="small">Lớp {{ detail?.grade }}</el-tag>

              <el-tag size="small" type="info">
                {{ categoryName }}
              </el-tag>

              <el-tag size="small" :type="detail?.published ? 'success' : 'info'">
                {{ detail?.published ? 'Đã xuất bản' : 'Nháp' }}
              </el-tag>
            </div>

            <div class="mt-1 text-sm text-gray-500">
              {{ detail?.lessonsCount || 0 }} bài học • {{ detail?.module_count }} chương
            </div>
          </div>
        </div>

        <!-- Right: Actions -->
        <div class="flex flex-wrap items-center gap-2">
          <el-button type="primary" @click="goEdit">Sửa</el-button>

          <el-button v-if="detail?.published" @click="unpublish">Gỡ</el-button>

          <el-button v-else type="success" @click="publish">Xuất bản</el-button>
        </div>
      </div>
    </div>

    <!-- TABS -->
    <el-tabs v-model="activeTab">
      <!-- ======================= OVERVIEW ======================= -->
      <el-tab-pane label="Tổng quan" name="overview">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5 space-y-4">
          <div>
            <h3 class="font-semibold mb-2 text-gray-700">Mô tả</h3>
            <div class="whitespace-pre-line text-gray-700">
              {{ detail?.description || '—' }}
            </div>
          </div>

          <div>
            <h3 class="font-semibold mb-2 text-gray-700">Tags</h3>
            <div class="flex flex-wrap gap-2">
              <el-tag v-for="t in detail?.tags" :key="t.id" type="info" size="small">
                {{ t.name }}
              </el-tag>

              <span v-if="!detail?.tags?.length" class="text-gray-500 text-sm">Không có</span>
            </div>
          </div>
        </div>
      </el-tab-pane>

      <!-- ======================= CURRICULUM ======================= -->
      <el-tab-pane label="Chương trình học" name="curriculum">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5 space-y-4">
          <div v-for="mod in detail?.modules" :key="mod.id" class="rounded border p-3">
            <div class="mb-2 flex items-center justify-between">
              <div class="font-semibold">Chương {{ mod.position + 1 }}: {{ mod.title }}</div>
              <div class="text-xs text-gray-500">{{ mod.lessons.length }} bài học</div>
            </div>

            <el-table :data="mod.lessons" size="small" border>
              <el-table-column type="index" label="#" width="50" />

              <el-table-column prop="title" label="Bài học" min-width="240" />

              <el-table-column prop="content_type" label="Loại" width="120">
                <template #default="{ row }">
                  <span class="capitalize">{{ lessonTypeLabel(row.content_type) }}</span>
                </template>
              </el-table-column>

              <el-table-column label="Nội dung" min-width="120">
                <template #default="{ row }"> {{ row.content_blocks.length }} phần </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()

const activeTab = ref('overview')
const detail = reactive({})
const loading = ref(false)

const getAuth = () => ({
  Authorization: `Bearer ${localStorage.getItem('access')}`,
})

/* ========================= FETCH DETAIL ========================= */

async function load() {
  loading.value = true
  try {
    const { data } = await axios.get(`/api/content/admin/courses/${route.params.id}/`, {
      headers: getAuth(),
    })

    Object.assign(detail, data)

    // lấy thumbnail nếu có
    if (data.image_url) {
      thumbnail.value = await fetchImage(data.image_url)
    }
  } catch (err) {
    console.error(err)
    ElMessage.error('Không tải được dữ liệu khóa học.')
  } finally {
    loading.value = false
  }
}

/* ========================= IMAGE FETCH ========================= */

const thumbnail = ref('/no-image.png')

async function fetchImage(apiPath) {
  try {
    const res = await axios.get(apiPath, {
      headers: getAuth(),
      responseType: 'blob',
    })
    return URL.createObjectURL(res.data)
  } catch {
    return '/no-image.png'
  }
}

const categoryName = computed(() => {
  if (!detail.categories?.length) return '—'
  return detail.categories[0].name
})

function lessonTypeLabel(t) {
  if (t === 'lesson') return 'Bài học'
  if (t === 'video') return 'Video'
  if (t === 'exercise') return 'Bài tập'
  if (t === 'quiz') return 'Quiz'
  return t
}

/* ========================= ACTIONS ========================= */

async function publish() {
  await axios.post(`/api/content/admin/courses/${detail.id}/publish/`, {}, { headers: getAuth() })
  ElMessage.success('Đã xuất bản')
  detail.published = true
}

async function unpublish() {
  await axios.post(`/api/content/admin/courses/${detail.id}/unpublish/`, {}, { headers: getAuth() })
  ElMessage.success('Đã gỡ')
  detail.published = false
}

function goEdit() {
  router.push(`/admin/courses/${detail.id}/edit`)
}

onMounted(load)
</script>
<style scoped></style>
