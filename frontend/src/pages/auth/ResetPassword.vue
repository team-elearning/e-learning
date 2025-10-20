<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="text-center">
      <div class="mx-auto w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mb-4 animate-bounce-slow">
        <svg class="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
        </svg>
      </div>
      <h1 class="text-xl font-bold text-gray-900 mb-2">Đặt lại mật khẩu</h1>
      <p class="text-sm text-gray-600">Nhập mật khẩu mới cho tài khoản của bạn</p>
    </div>

    <!-- Error Alert -->
    <div
      v-if="status === 'error'"
      class="rounded-xl border border-red-200 bg-red-50 p-4 text-sm text-red-700 animate-shake"
      role="alert"
    >
      <div class="flex items-start gap-3">
        <svg class="w-5 h-5 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
          <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd" />
        </svg>
        <p>{{ errMessage }}</p>
      </div>
    </div>

    <!-- Form -->
    <form @submit.prevent="submit" class="space-y-5" autocomplete="off">
      <!-- Password -->
      <div class="form-group">
        <label for="password" class="form-label">
          Mật khẩu mới
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <div class="input-icon">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <input
            id="password"
            v-model.trim="password"
            :type="showPassword ? 'text' : 'password'"
            name="new-password"
            placeholder="••••••••"
            autocomplete="new-password"
            class="form-input"
            :class="{ 'border-red-300': touchedPassword && !validPassword }"
            :disabled="loading"
            @blur="touchedPassword = true"
            @input="touchedPassword = false"
            required
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition p-1"
            @click="showPassword = !showPassword"
            tabindex="-1"
          >
            <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            </svg>
          </button>
        </div>
        <p v-if="touchedPassword && !validPassword" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>Mật khẩu tối thiểu 6 ký tự</span>
        </p>
      </div>

      <!-- Confirm Password -->
      <div class="form-group">
        <label for="confirm" class="form-label">
          Xác nhận mật khẩu
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <div class="input-icon">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <input
            id="confirm"
            v-model.trim="confirm"
            :type="showPassword ? 'text' : 'password'"
            name="confirm-password"
            placeholder="••••••••"
            autocomplete="new-password"
            class="form-input"
            :class="{ 'border-red-300': touchedConfirm && !validConfirm }"
            :disabled="loading"
            @blur="touchedConfirm = true"
            @input="touchedConfirm = false"
            required
          />
        </div>
        <p v-if="touchedConfirm && !validConfirm" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>Mật khẩu không khớp</span>
        </p>
      </div>

      <!-- Submit button -->
      <button
        type="submit"
        class="btn-primary"
        :disabled="!validPassword || !validConfirm || loading"
        :class="{ 'opacity-60 cursor-not-allowed': !validPassword || !validConfirm || loading }"
      >
        <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span v-if="!loading">Đặt lại mật khẩu</span>
        <span v-else>Đang xử lý...</span>
      </button>

      <!-- Back to login -->
      <div class="text-center">
        <RouterLink to="/auth/login" class="text-sm font-medium text-emerald-600 hover:text-emerald-700 transition inline-flex items-center gap-1">
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Quay lại đăng nhập
        </RouterLink>
      </div>
    </form>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useAuthStore } from '@/store/auth.store'
import { useRoute, useRouter } from 'vue-router'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const password = ref('')
const confirm = ref('')
const showPassword = ref(false)
const touchedPassword = ref(false)
const touchedConfirm = ref(false)
const loading = ref(false)
const status = ref<'idle' | 'success' | 'error'>('idle')
const errMessage = ref('')
const token = ref('')

const validPassword = computed(() => password.value.length >= 6)
const validConfirm = computed(() => confirm.value === password.value && confirm.value.length >= 6)

onMounted(() => {
  token.value = route.query.token as string
  if (!token.value) {
    errMessage.value = 'Link không hợp lệ hoặc đã hết hạn.'
    status.value = 'error'
  }
})

async function submit() {
  touchedPassword.value = true
  touchedConfirm.value = true
  
  if (!validPassword.value || !validConfirm.value || loading.value) return
  if (!token.value) return

  loading.value = true
  status.value = 'idle'
  errMessage.value = ''

  try {
    await auth.resetPassword(token.value, password.value)
    alert('Đặt lại mật khẩu thành công!')
    router.push('/auth/login')
  } catch (e: any) {
    status.value = 'error'
    errMessage.value = e?.message || 'Đặt lại mật khẩu thất bại.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.form-group {
  @apply space-y-2;
}

.form-label {
  @apply block text-sm font-medium text-gray-700;
}

.form-input {
  @apply w-full pl-11 pr-4 py-3 bg-white border border-gray-200 rounded-xl text-gray-900 placeholder-gray-400;
  @apply focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500;
  @apply transition duration-200;
  @apply disabled:bg-gray-50 disabled:cursor-not-allowed;
}

.form-input:hover:not(:disabled) {
  @apply border-gray-300;
}

.input-icon {
  @apply absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none z-10;
}

.form-error {
  @apply text-xs text-red-600 mt-1.5 flex items-start gap-1.5;
}

.btn-primary {
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0.75rem 1.5rem !important;
  border-radius: 0.75rem !important;
  background: linear-gradient(to right, rgb(5, 150, 105), rgb(20, 184, 166)) !important;
  color: white !important;
  font-weight: 600 !important;
  transition: all 0.2s !important;
  transform-origin: center !important;
  box-shadow: 0 10px 15px -3px rgba(5, 150, 105, 0.25) !important;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(to right, rgb(4, 120, 87), rgb(13, 148, 136)) !important;
}

.btn-primary:focus {
  outline: none !important;
  box-shadow: 0 0 0 2px rgba(5, 150, 105, 0.5), 0 10px 15px -3px rgba(5, 150, 105, 0.25) !important;
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.98) !important;
}

.btn-primary:disabled {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}

@keyframes bounce-slow {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-10px);
  }
}

.animate-bounce-slow {
  animation: bounce-slow 3s ease-in-out infinite;
}

@keyframes shake {
  0%, 100% {
    transform: translateX(0);
  }
  25% {
    transform: translateX(-10px);
  }
  75% {
    transform: translateX(10px);
  }
}

.animate-shake {
  animation: shake 0.3s ease-out;
}
</style>
