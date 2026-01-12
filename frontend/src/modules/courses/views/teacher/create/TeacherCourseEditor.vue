<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElTabs, ElTabPane, ElMessage } from 'element-plus'
import { teacherCourseApi } from '../../../api/teacher-course.api'
import type { Course } from '../../../types/course.types'

// Components
import TeacherCourseCurriculum from './TeacherCourseCurriculum.vue'
import TeacherCourseSettings from './TeacherCourseSettings.vue'

const route = useRoute()
const courseId = route.params.id as string
const activeTab = ref('curriculum')
const isLoading = ref(false)
const course = ref<Course | null>(null)

async function fetchCourse() {
  isLoading.value = true
  try {
    const res = await teacherCourseApi.getCourseDetail(courseId)
    course.value = res.data
  } catch (error) {
    ElMessage.error('Không thể tải thông tin khóa học')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  fetchCourse()
})
</script>

<template>
  <div class="min-h-screen bg-slate-50 pb-20">
    <div v-if="isLoading" class="p-10 flex justify-center">
      <div
        class="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full"
      ></div>
    </div>

    <div v-else-if="course" class="max-w-7xl mx-auto">
      <!-- Header -->
      <div
        class="bg-white border-b border-slate-200 px-6 py-4 mb-6 sticky top-0 z-30 shadow-sm flex items-center justify-between"
      >
        <div>
          <div class="text-xs uppercase font-bold text-slate-500 tracking-wider mb-1">
            Chỉnh sửa khóa học
          </div>
          <h1 class="text-xl font-bold text-gray-900 flex items-center gap-2">
            {{ course.title }}
            <span
              v-if="!course.published"
              class="px-2 py-0.5 rounded text-xs bg-slate-100 text-slate-600 font-medium border border-slate-200"
              >DRAFT</span
            >
            <span
              v-else
              class="px-2 py-0.5 rounded text-xs bg-green-100 text-green-700 font-medium border border-green-200"
              >PUBLISHED</span
            >
          </h1>
        </div>
        <div class="flex gap-2">
          <a
            :href="`/teacher/courses/${courseId}`"
            target="_blank"
            class="px-3 py-1.5 text-sm font-medium text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors"
            >Xem trước</a
          >
        </div>
      </div>

      <div class="px-4 sm:px-6">
        <el-tabs
          v-model="activeTab"
          class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 custom-tabs"
        >
          <el-tab-pane label="Đề cương khóa học" name="curriculum">
            <TeacherCourseCurriculum :course-id="courseId" />
          </el-tab-pane>
          <el-tab-pane label="Thông tin cơ bản" name="settings">
            <TeacherCourseSettings :course="course" @updated="fetchCourse" />
          </el-tab-pane>
        </el-tabs>
      </div>
    </div>
  </div>
</template>

<style>
.custom-tabs .el-tabs__item {
  font-size: 16px;
  font-weight: 600;
}
</style>
