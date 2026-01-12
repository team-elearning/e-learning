<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { requestPasswordReset } from '@/modules/auth/api/auth.api'

const router = useRouter()
const loading = ref(false)
const emailSent = ref(false)
const email = ref('')
const error = ref<string | null>(null)

async function onSubmit() {
  if (!email.value) {
    error.value = 'Vui lòng nhập Email của bạn.'
    return
  }

  loading.value = true
  error.value = null

  try {
    await requestPasswordReset(email.value)
    emailSent.value = true
    ElMessage.success('Đã gửi link reset mật khẩu đến email của bạn!')
  } catch (e: any) {
    const data = e?.response?.data
    error.value = data?.email?.[0] || data?.detail || 'Không thể gửi yêu cầu. Vui lòng thử lại.'
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
      class="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-400/20 blur-[100px] pointer-events-none"
    ></div>
    <div
      class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-purple-400/20 blur-[100px] pointer-events-none"
    ></div>

    <div
      class="w-full max-w-md bg-white/80 backdrop-blur-xl border border-white/50 shadow-2xl rounded-3xl p-8 relative z-10"
    >
      <div class="text-center mb-8">
        <div
          class="h-12 w-12 bg-indigo-100 text-indigo-600 rounded-xl mx-auto flex items-center justify-center shadow-sm mb-4"
        >
          <span class="text-2xl">🔑</span>
        </div>
        <h1 class="text-2xl font-bold text-gray-900">Quên mật khẩu?</h1>
        <p class="text-slate-500 mt-2 text-sm">Nhập email để nhận liên kết đặt lại mật khẩu</p>
      </div>

      <!-- Success State -->
      <div v-if="emailSent" class="text-center space-y-6">
        <div class="p-4 bg-green-50 text-green-700 rounded-xl border border-green-200 text-sm">
          Đã gửi hướng dẫn đặt lại mật khẩu đến <strong>{{ email }}</strong
          >. Vui lòng kiểm tra hộp thư đến (và cả mục Spam).
        </div>
        <button
          @click="router.push('/login')"
          class="w-full py-3 rounded-xl bg-slate-100 text-slate-700 font-bold hover:bg-slate-200 transition-colors"
        >
          Quay lại đăng nhập
        </button>
      </div>

      <!-- Form State -->
      <form v-else @submit.prevent="onSubmit" class="space-y-6">
        <div
          v-if="error"
          class="p-3 rounded-lg bg-red-50 text-red-600 text-sm border border-red-100 flex gap-2"
        >
          <span>⚠️</span> {{ error }}
        </div>

        <div>
          <label class="block text-sm font-semibold text-gray-700 mb-1.5 ml-1">Email</label>
          <input
            v-model="email"
            type="email"
            placeholder="name@example.com"
            class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-[rgb(var(--primary))] focus:ring-4 focus:ring-blue-500/10 transition-all outline-none"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3.5 rounded-xl bg-gradient-to-r from-[rgb(var(--primary))] to-blue-600 text-white font-bold shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 hover:-translate-y-0.5 active:translate-y-0 transition-all disabled:opacity-70 disabled:pointer-events-none"
        >
          <span v-if="loading">Đang gửi...</span>
          <span v-else>Gửi yêu cầu</span>
        </button>

        <div class="text-center">
          <button
            type="button"
            @click="router.push('/login')"
            class="text-sm font-semibold text-slate-500 hover:text-[rgb(var(--primary))]"
          >
            ← Quay lại đăng nhập
          </button>
        </div>
      </form>
    </div>
  </div>
</template>
