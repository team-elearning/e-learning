<!-- src/pages/auth/ForgotPassword.vue -->
<template>
  <div class="w-full">
    <!-- Giữ đúng layout/spacing/màu như form Đăng nhập -->
    <div class="mx-auto w-full max-w-md">
      <!-- Title -->
      <h1 class="mb-2 text-xl font-semibold text-gray-900 text-center">Quên mật khẩu</h1>
      <p class="mb-4 text-center text-sm text-gray-500">
        Nhập email để nhận liên kết đặt lại mật khẩu.
      </p>

      <!-- Alert thành công / lỗi (cùng style login) -->
      <div
        v-if="status==='success'"
        class="mb-4 rounded-xl border border-[#79BBFF] bg-[#79BBFF1A] p-3 text-sm text-[#245]"
        role="alert"
      >
        Đã gửi email đặt lại mật khẩu tới <b>{{ email }}</b>. Vui lòng kiểm tra hộp thư (và cả mục Spam).
      </div>
      <div
        v-else-if="status==='error'"
        class="mb-4 rounded-xl border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700"
        role="alert"
      >
        {{ errMessage }}
      </div>

      <!-- Form (label có * như login, input & button đồng bộ màu/bo góc) -->
      <form @submit.prevent="submit" novalidate>
        <label for="email" class="mb-1 block text-sm font-medium text-gray-700">
          <span class="text-rose-500">*</span> Email
        </label>
        <input
          id="email"
          v-model.trim="email"
          type="email"
          autocomplete="email"
          :disabled="loading || status==='success'"
          class="block w-full rounded-md border border-gray-300 px-3 py-2 text-sm outline-none transition
                 focus:border-[#79BBFF] focus:ring-2 focus:ring-[#79BBFF]/30 disabled:cursor-not-allowed disabled:bg-gray-50"
          placeholder="you@example.com"
          @blur="touched = true"
          required
        />
        <p v-if="touched && !validEmail" class="mt-1 text-xs text-rose-600">
          Vui lòng nhập email hợp lệ.
        </p>

        <!-- Nút gửi (giống nút Đăng nhập) -->
        <button
          type="submit"
          :disabled="!validEmail || loading || status==='success'"
          class="mt-4 inline-flex w-full items-center justify-center rounded-md bg-[#48a0f8] px-4 py-2.5 text-sm font-semibold text-white transition
                 hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-50"
        >
          <svg
            v-if="loading"
            class="mr-2 h-4 w-4 animate-spin"
            viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"
          >
            <circle cx="12" cy="12" r="9" class="opacity-30"></circle>
            <path d="M21 12a9 9 0 00-9-9" stroke-linecap="round"></path>
          </svg>
          <span>{{ status==='success' ? 'Đã gửi liên kết' : 'Gửi liên kết đặt lại' }}</span>
        </button>

        <!-- Dòng phân cách “hoặc” giống login -->
        <div class="my-4 flex items-center gap-3">
          <div class="h-px flex-1 bg-gray-200"></div>
          <span class="text-xs text-gray-400">hoặc</span>
          <div class="h-px flex-1 bg-gray-200"></div>
        </div>

        <!-- Hành động phụ: quay lại đăng nhập / đăng ký (đồng bộ màu) -->
        <div class="flex items-center justify-between text-sm">
          <RouterLink to="/auth/login" class="font-medium text-[#2391ff] hover:underline">
            ← Quay lại đăng nhập
          </RouterLink>
          <RouterLink to="/auth/register" class="text-gray-600 hover:underline">
            Tạo tài khoản
          </RouterLink>
        </div>
      </form>

      <!-- Ghi chú dưới giống login -->
      <p class="mt-6 text-center text-xs text-gray-400">
        Bằng việc tiếp tục, bạn đồng ý với Điều khoản và Chính sách bảo mật của chúng tôi.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'

const email = ref('')
const touched = ref(false)
const loading = ref(false)
const status = ref<'idle' | 'success' | 'error'>('idle')
const errMessage = ref('')

const validEmail = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.value))

async function submit() {
  touched.value = true
  if (!validEmail.value || loading.value) return
  loading.value = true
  status.value = 'idle'
  errMessage.value = ''

  try {
    // TODO: thay bằng authService.forgotPassword(email.value)
    await new Promise((res) => setTimeout(res, 900))
    status.value = 'success'
  } catch (e: any) {
    status.value = 'error'
    errMessage.value = e?.message || 'Gửi email thất bại. Vui lòng thử lại.'
  } finally {
    loading.value = false
  }
}
</script>
