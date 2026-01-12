<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { confirmPasswordReset } from '@/modules/auth/api/auth.api'

const route = useRoute()
const router = useRouter()

const uid = route.params.uid as string
const token = route.params.token as string

const form = ref({
  newPassword1: '',
  newPassword2: '',
})

const loading = ref(false)
const error = ref<string | null>(null)

async function onSubmit() {
  error.value = null

  if (form.value.newPassword1.length < 6) {
    error.value = 'Mật khẩu phải có ít nhất 6 ký tự'
    return
  }

  if (form.value.newPassword1 !== form.value.newPassword2) {
    error.value = 'Mật khẩu xác nhận không khớp'
    return
  }

  loading.value = true
  try {
    await confirmPasswordReset(uid, token, form.value.newPassword1, form.value.newPassword2)
    ElMessage.success('Đặt lại mật khẩu thành công!')
    router.push('/login')
  } catch (e: any) {
    const data = e?.response?.data
    if (data?.new_password1) {
      error.value = data.new_password1[0]
    } else if (data?.detail) {
      error.value = data.detail
    } else if (data?.token) {
      error.value = 'Link đặt lại mật khẩu không hợp lệ hoặc đã hết hạn.'
    } else {
      error.value = 'Đặt lại mật khẩu thất bại. Vui lòng thử lại.'
    }
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-slate-50"
  >
    <!-- Decorative Bloom -->
    <div
      class="absolute top-[-10%] right-[-10%] w-[60%] h-[60%] rounded-full bg-emerald-400/10 blur-[100px] pointer-events-none"
    ></div>

    <div
      class="w-full max-w-md bg-white/80 backdrop-blur-xl border border-white/50 shadow-2xl rounded-3xl p-8 relative z-10"
    >
      <div class="text-center mb-8">
        <div
          class="h-12 w-12 bg-emerald-100 text-emerald-600 rounded-xl mx-auto flex items-center justify-center shadow-sm mb-4"
        >
          <span class="text-2xl">🔐</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900">Đặt lại mật khẩu</h1>
        <p class="text-slate-500 mt-2 text-sm">Nhập mật khẩu mới cho tài khoản của bạn</p>
      </div>

      <form @submit.prevent="onSubmit" class="space-y-5">
        <div
          v-if="error"
          class="p-3 rounded-lg bg-red-50 text-red-600 text-sm border border-red-100 flex gap-2"
        >
          <span>⚠️</span> {{ error }}
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5 ml-1">Mật khẩu mới</label>
          <input
            v-model="form.newPassword1"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none"
          />
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5 ml-1"
            >Xác nhận mật khẩu</label
          >
          <input
            v-model="form.newPassword2"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-emerald-500 focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-600 text-white font-bold shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 hover:-translate-y-0.5 active:translate-y-0 transition-all disabled:opacity-70 disabled:pointer-events-none"
        >
          <span v-if="loading">Đang cập nhật...</span>
          <span v-else>Đổi mật khẩu</span>
        </button>
      </form>
    </div>
  </div>
</template>
