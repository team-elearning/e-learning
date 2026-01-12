<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePasswordApi } from '@/modules/auth/api/auth.api'
import { useAuthStore } from '@/stores/auth.store'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)

const form = reactive({
  old_password: '',
  new_password: '',
  confirm_password: '',
})

async function onSubmit() {
  error.value = null

  if (!form.old_password || !form.new_password || !form.confirm_password) {
    error.value = 'Vui lòng điền đầy đủ các trường.'
    return
  }

  if (form.new_password !== form.confirm_password) {
    error.value = 'Mật khẩu xác nhận không khớp.'
    return
  }

  if (form.new_password.length < 6) {
    error.value = 'Mật khẩu mới phải có ít nhất 6 ký tự.'
    return
  }

  loading.value = true
  try {
    await changePasswordApi(form.old_password, form.new_password)
    ElMessage.success('Đổi mật khẩu thành công! Vui lòng đăng nhập lại.')

    // Logout and redirect to login
    authStore.logout()
    router.push('/login')
  } catch (e: any) {
    const data = e?.response?.data
    error.value =
      data?.old_password?.[0] ||
      data?.new_password?.[0] ||
      data?.detail ||
      'Đổi mật khẩu thất bại. Vui lòng kiểm tra lại mật khẩu cũ.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="p-6 max-w-2xl mx-auto">
    <div class="mb-8">
      <h1 class="text-2xl font-bold text-gray-900">Đổi mật khẩu</h1>
      <p class="text-slate-500 text-sm">Cập nhật mật khẩu để bảo vệ tài khoản</p>
    </div>

    <div class="bg-white rounded-2xl p-8 border border-slate-200 shadow-sm">
      <form @submit.prevent="onSubmit" class="space-y-6">
        <div
          v-if="error"
          class="p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm flex items-start gap-3"
        >
          <span>⚠️</span>
          <span>{{ error }}</span>
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Mật khẩu hiện tại</label>
          <input
            v-model="form.old_password"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:border-[rgb(var(--primary))] focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5">Mật khẩu mới</label>
          <input
            v-model="form.new_password"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:border-[rgb(var(--primary))] focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5"
            >Xác nhận mật khẩu mới</label
          >
          <input
            v-model="form.confirm_password"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-2.5 rounded-lg border border-slate-300 focus:border-[rgb(var(--primary))] focus:ring-2 focus:ring-blue-100 outline-none transition-all"
          />
        </div>

        <div class="pt-4 flex justify-end gap-3">
          <button
            type="button"
            @click="router.back()"
            class="px-5 py-2.5 rounded-lg border border-slate-300 text-slate-700 font-semibold hover:bg-slate-50 transition-colors"
          >
            Hủy
          </button>
          <button
            type="submit"
            :disabled="loading"
            class="px-6 py-2.5 rounded-lg bg-[rgb(var(--primary))] text-white font-bold shadow-lg shadow-blue-500/20 hover:shadow-blue-500/30 hover:-translate-y-0.5 transition-all disabled:opacity-70 disabled:pointer-events-none flex items-center gap-2"
          >
            <span
              v-if="loading"
              class="animate-spin h-4 w-4 border-2 border-white/30 border-t-white rounded-full"
            ></span>
            <span>{{ loading ? 'Đang xử lý...' : 'Xác nhận đổi' }}</span>
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
