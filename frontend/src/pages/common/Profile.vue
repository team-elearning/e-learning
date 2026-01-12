<script setup lang="ts">
import { ref, onMounted, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import {
  profileApi,
  type UserProfile,
  type UpdateProfileBody,
} from '@/modules/auth/api/profile.api'

const loading = ref(false)
const updating = ref(false)
const profile = ref<UserProfile | null>(null)

const form = reactive({
  display_name: '',
  phone: '',
  dob: '',
  gender: 'other' as 'male' | 'female' | 'other',
  language: 'vi',
})

async function fetchProfile() {
  loading.value = true
  try {
    const res = await profileApi.getProfile()
    profile.value = res.data

    // Fill form
    form.display_name = res.data.display_name || ''
    form.phone = res.data.phone || ''
    form.dob = res.data.dob || ''
    form.gender = res.data.gender || 'other'
    form.language = res.data.language || 'vi'
  } catch (error) {
    ElMessage.error('Không thể tải thông tin hồ sơ')
  } finally {
    loading.value = false
  }
}

async function handleUpdate() {
  updating.value = true
  try {
    const payload: UpdateProfileBody = {
      display_name: form.display_name,
      phone: form.phone,
      dob: form.dob || undefined, // Send undefined if empty string to avoid error if backend is strict, or handle appropriately
      gender: form.gender,
      language: form.language,
    }

    if (!payload.dob) delete payload.dob // Remove empty date if not set

    const res = await profileApi.updateProfile(payload)
    profile.value = res.data
    ElMessage.success('Cập nhật hồ sơ thành công!')
  } catch (error: any) {
    ElMessage.error(error?.response?.data?.detail || 'Cập nhật thất bại')
  } finally {
    updating.value = false
  }
}

function formatDate(dateString: string) {
  if (!dateString) return ''
  return new Date(dateString).toLocaleDateString('vi-VN')
}

onMounted(() => {
  fetchProfile()
})
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">Hồ sơ cá nhân</h1>
      <p class="text-slate-500 text-sm">Quản lý đóng tin cá nhân và cài đặt tài khoản</p>
    </div>

    <div v-if="loading" class="animate-pulse space-y-4">
      <div class="h-40 bg-slate-200 rounded-xl"></div>
      <div class="h-10 bg-slate-200 rounded w-1/3"></div>
    </div>

    <div v-else-if="profile" class="grid grid-cols-1 md:grid-cols-3 gap-8">
      <!-- Left Column: Avatar & Summary -->
      <div class="md:col-span-1">
        <div
          class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm flex flex-col items-center text-center"
        >
          <div
            class="w-32 h-32 rounded-full bg-slate-100 mb-4 overflow-hidden border-4 border-white shadow-lg relative group cursor-pointer"
          >
            <img
              v-if="profile.avatar_id"
              :src="profile.avatar_id"
              class="w-full h-full object-cover"
              alt="Avatar"
            />
            <div
              v-else
              class="w-full h-full flex items-center justify-center text-4xl bg-gradient-to-br from-blue-100 to-indigo-100 text-indigo-500"
            >
              {{ profile.username.charAt(0).toUpperCase() }}
            </div>

            <!-- Overlay for future upload feature -->
            <div
              class="absolute inset-0 bg-black/40 flex items-center justify-center text-white opacity-0 group-hover:opacity-100 transition-opacity"
            >
              <span class="text-xs font-bold">Thay đổi</span>
            </div>
          </div>

          <h2 class="text-xl font-bold text-gray-900">
            {{ profile.display_name || profile.username }}
          </h2>
          <span
            class="px-3 py-1 bg-slate-100 text-slate-600 rounded-full text-xs font-bold uppercase tracking-wider mt-2"
          >
            {{ profile.role }}
          </span>

          <div class="w-full mt-6 pt-6 border-t border-slate-100 text-left space-y-3">
            <div class="text-sm">
              <span class="text-slate-500 block text-xs uppercase mb-1">Email</span>
              <div class="font-medium text-slate-800 break-all">{{ profile.email }}</div>
            </div>
            <div class="text-sm">
              <span class="text-slate-500 block text-xs uppercase mb-1">Ngày tham gia</span>
              <div class="font-medium text-slate-800">{{ formatDate(profile.created_at) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- Right Column: Edit Form -->
      <div class="md:col-span-2">
        <div class="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
          <h3 class="text-lg font-bold text-gray-900 mb-6">Thông tin chi tiết</h3>

          <form @submit.prevent="handleUpdate" class="space-y-6">
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <!-- Username (Readonly) -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Tên đăng nhập</label>
                <input
                  type="text"
                  :value="profile.username"
                  disabled
                  class="w-full px-4 py-2.5 rounded-lg bg-slate-50 border border-slate-200 text-slate-500 cursor-not-allowed"
                />
              </div>

              <!-- Display Name -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Tên hiển thị</label>
                <input
                  v-model="form.display_name"
                  type="text"
                  class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:border-[rgb(var(--primary))] focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                  placeholder="Nhập tên hiển thị"
                />
              </div>

              <!-- Phone -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Số điện thoại</label>
                <input
                  v-model="form.phone"
                  type="tel"
                  class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:border-[rgb(var(--primary))] focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                  placeholder="0912..."
                />
              </div>

              <!-- DOB -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Ngày sinh</label>
                <input
                  v-model="form.dob"
                  type="date"
                  class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:border-[rgb(var(--primary))] focus:ring-2 focus:ring-blue-100 outline-none transition-all"
                />
              </div>

              <!-- Gender -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Giới tính</label>
                <select
                  v-model="form.gender"
                  class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:border-[rgb(var(--primary))] focus:ring-2 focus:ring-blue-100 outline-none transition-all bg-white"
                >
                  <option value="male">Nam</option>
                  <option value="female">Nữ</option>
                  <option value="other">Khác</option>
                </select>
              </div>

              <!-- Language -->
              <div>
                <label class="block text-sm font-semibold text-slate-700 mb-2">Ngôn ngữ</label>
                <select
                  v-model="form.language"
                  class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:border-[rgb(var(--primary))] focus:ring-2 focus:ring-blue-100 outline-none transition-all bg-white"
                >
                  <option value="vi">Tiếng Việt</option>
                  <option value="en">English</option>
                </select>
              </div>
            </div>

            <div class="pt-6 border-t border-slate-100 flex justify-end">
              <button
                type="submit"
                :disabled="updating"
                class="px-6 py-2.5 bg-[rgb(var(--primary))] text-white font-semibold rounded-lg shadow hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 transition-all disabled:opacity-70 flex items-center gap-2"
              >
                <span
                  v-if="updating"
                  class="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full"
                ></span>
                <span>{{ updating ? 'Đang lưu...' : 'Lưu thay đổi' }}</span>
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>
