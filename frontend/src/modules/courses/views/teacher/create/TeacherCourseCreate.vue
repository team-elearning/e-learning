<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { teacherCourseApi, type CreateCourseDto } from '../../../api/teacher-course.api'
import { ElMessage } from 'element-plus'
import { UploadCloud, Image as ImageIcon, Loader2 } from 'lucide-vue-next'
import axios from 'axios'

const router = useRouter()
const isSubmitting = ref(false)
const isUploading = ref(false)

const form = reactive<CreateCourseDto>({
  title: '',
  description: '',
  price: 0,
  subject: '',
  grade: 10,
  categories: [],
  tags: [],
  published: false,
  image_id: '',
})

// Mock data for Selects
const GRADES = [10, 11, 12]
const SUBJECTS = ['Toán', 'Vật Lí', 'Hóa Học', 'Sinh Học', 'Tiếng Anh', 'Văn', 'Lịch Sử', 'Địa Lý']

const thumbnailPreview = ref<string>('')

async function handleUploadThumbnail(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return

  isUploading.value = true
  try {
    // 1. Init Upload
    const initRes = await teacherCourseApi.uploadInit({
      filename: file.name,
      file_type: file.type,
      file_size: file.size,
      component: 'course_thumbnail',
    })
    const { file_id, upload_url, upload_fields } = initRes.data

    // 2. Upload to S3
    const formData = new FormData()
    // Append fields first (AWS requirement)
    Object.entries(upload_fields).forEach(([key, value]) => {
      formData.append(key, value)
    })
    formData.append('file', file)

    await axios.post(upload_url, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })

    // 3. Confirm
    await teacherCourseApi.uploadConfirm(file_id)

    // Success
    form.image_id = file_id
    thumbnailPreview.value = URL.createObjectURL(file) // Local preview
    ElMessage.success('Tải ảnh lên thành công')
  } catch (error) {
    console.error(error)
    ElMessage.error('Tải ảnh thất bại')
  } finally {
    isUploading.value = false
  }
}

async function handleSubmit() {
  if (!form.title) {
    ElMessage.warning('Vui lòng nhập tên khóa học')
    return
  }

  isSubmitting.value = true
  try {
    const res = await teacherCourseApi.createCourse(form)
    ElMessage.success('Tạo khóa học thành công')
    // Redirect to Editor (Phase 2)
    router.push(`/teacher/courses/${res.data.id}/edit`)
  } catch (error) {
    ElMessage.error('Có lỗi xảy ra khi tạo khóa học')
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <div class="max-w-3xl mx-auto p-6 lg:p-10">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900 mb-2">Tạo khóa học mới</h1>
      <p class="text-slate-500">Bước 1: Nhập thông tin cơ bản cho khóa học của bạn</p>
    </div>

    <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-6">
      <!-- Title -->
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1"
          >Tên khóa học <span class="text-red-500">*</span></label
        >
        <input
          v-model="form.title"
          type="text"
          placeholder="Ví dụ: Luyện thi Toán Đánh giá năng lực 2026"
          class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
        />
      </div>

      <!-- Thumbnail Upload -->
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Ảnh bìa khóa học</label>
        <div
          class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-slate-300 border-dashed rounded-lg hover:bg-slate-50 transition-colors relative group cursor-pointer"
        >
          <input
            type="file"
            accept="image/*"
            class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
            @change="handleUploadThumbnail"
            :disabled="isUploading"
          />
          <div class="space-y-1 text-center" :class="{ 'opacity-50': isUploading }">
            <div
              v-if="thumbnailPreview"
              class="relative w-full h-48 mx-auto mb-4 rounded-lg overflow-hidden shadow-sm"
            >
              <img :src="thumbnailPreview" class="w-full h-full object-cover" />
              <div
                class="absolute inset-0 bg-black/40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity text-white text-sm font-medium"
              >
                Click để thay đổi
              </div>
            </div>
            <div v-else>
              <div class="mx-auto h-12 w-12 text-slate-400">
                <ImageIcon class="w-12 h-12" />
              </div>
              <div class="flex text-sm text-slate-600 justify-center">
                <span class="font-medium text-indigo-600 hover:text-indigo-500">Tải ảnh lên</span>
                <p class="pl-1">hoặc kéo thả vào đây</p>
              </div>
              <p class="text-xs text-slate-500">PNG, JPG, GIF lên đến 5MB</p>
            </div>
            <div
              v-if="isUploading"
              class="absolute inset-0 flex items-center justify-center bg-white/80"
            >
              <div class="flex items-center gap-2 text-indigo-600 font-medium">
                <Loader2 class="w-5 h-5 animate-spin" />
                Đang tải lên...
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Grid info -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Môn học</label>
          <el-select v-model="form.subject" placeholder="Chọn môn học" class="w-full">
            <el-option v-for="s in SUBJECTS" :key="s" :label="s" :value="s" />
          </el-select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Khối lớp</label>
          <el-select v-model="form.grade" placeholder="Chọn khối lớp" class="w-full">
            <el-option v-for="g in GRADES" :key="g" :label="`Lớp ${g}`" :value="g" />
          </el-select>
        </div>
      </div>

      <!-- Categories & Tags -->
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Danh mục</label>
          <el-select
            v-model="form.categories"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="Chọn hoặc nhập danh mục"
            class="w-full"
          >
            <el-option label="Luyện thi đại học" value="Luyện thi đại học" />
            <el-option label="Cơ bản" value="Cơ bản" />
            <el-option label="Nâng cao" value="Nâng cao" />
          </el-select>
        </div>
        <div>
          <label class="block text-sm font-medium text-slate-700 mb-1">Thẻ (Tags)</label>
          <el-select
            v-model="form.tags"
            multiple
            filterable
            allow-create
            default-first-option
            placeholder="Nhập thẻ tìm kiếm (Tags)"
            class="w-full"
          >
          </el-select>
        </div>
      </div>

      <!-- Price -->
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Học phí (VNĐ)</label>
        <el-input-number
          v-model="form.price"
          :min="0"
          :step="10000"
          class="w-full"
          placeholder="0"
        />
        <p class="text-xs text-slate-500 mt-1">Để 0 nếu là khóa học miễn phí</p>
      </div>

      <!-- Description -->
      <div>
        <label class="block text-sm font-medium text-slate-700 mb-1">Mô tả ngắn</label>
        <textarea
          v-model="form.description"
          rows="4"
          class="w-full px-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
          placeholder="Giới thiệu tổng quan về khóa học..."
        ></textarea>
      </div>

      <div class="flex items-center justify-end gap-4 pt-4 border-t border-slate-100">
        <button
          @click="router.back()"
          class="px-5 py-2.5 text-slate-600 font-medium hover:bg-slate-50 rounded-lg transition-colors"
        >
          Hủy bỏ
        </button>
        <button
          @click="handleSubmit"
          :disabled="isSubmitting"
          class="px-6 py-2.5 bg-indigo-600 text-white font-medium rounded-lg hover:bg-indigo-700 transition shadow-sm flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Loader2 v-if="isSubmitting" class="w-5 h-5 animate-spin" />
          <span>{{ isSubmitting ? 'Đang khởi tạo...' : 'Tiếp tục: Xây dựng nội dung' }}</span>
        </button>
      </div>
    </div>
  </div>
</template>
