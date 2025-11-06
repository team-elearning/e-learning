<template>
  <div class="space-y-6">
    <form @submit.prevent="onSubmit" class="space-y-5" autocomplete="off">
      <!-- Email -->
      <div class="form-group">
        <label for="email" class="form-label">
          Tên đăng nhập
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <div class="input-icon">
            <svg
              class="w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15.75 7.5a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M4.5 20.25a8.25 8.25 0 0115 0"
              />
            </svg>
          </div>
          <input
            id="email"
            v-model="form.email"
            type="text"
            name="email-field"
            placeholder="Email hoặc tên tài khoản"
            autocomplete="off"
            class="form-input"
            :class="{ 'border-red-300': errors.email }"
            @blur="validateEmail"
            @input="errors.email = ''"
          />
        </div>
        <p v-if="errors.email" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          <span>{{ errors.email }}</span>
        </p>
      </div>

      <!-- Password -->
      <div class="form-group">
        <label for="password" class="form-label">
          Mật khẩu
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <div class="input-icon">
            <svg
              class="w-5 h-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
          </div>
          <input
            id="password"
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            name="password-field"
            placeholder="••••••••"
            autocomplete="new-password"
            class="form-input"
            :class="{ 'border-red-300': errors.password }"
            @blur="validatePassword"
            @input="errors.password = ''"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition p-1"
            @click="showPassword = !showPassword"
            tabindex="-1"
          >
            <svg
              v-if="!showPassword"
              class="w-5 h-5"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
              />
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
              />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
              />
            </svg>
          </button>
        </div>
        <p v-if="errors.password" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          <span>{{ errors.password }}</span>
        </p>
      </div>

      <!-- Remember & Forgot -->
      <div class="flex items-center justify-between">
        <label class="flex items-center cursor-pointer group">
          <input
            v-model="form.remember"
            type="checkbox"
            class="w-4 h-4 text-pink-600 border-gray-300 rounded focus:ring-2 focus:ring-pink-500/30 transition"
          />
          <span class="ml-2 text-sm text-gray-600 group-hover:text-gray-900 transition"
            >Ghi nhớ đăng nhập</span
          >
        </label>
        <RouterLink
          to="/auth/forgot-password"
          class="text-sm font-medium text-pink-600 hover:text-pink-700 transition"
        >
          Quên mật khẩu?
        </RouterLink>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        class="btn-primary"
        :disabled="loading"
        :class="{ 'opacity-60 cursor-not-allowed': loading }"
      >
        <svg
          v-if="loading"
          class="animate-spin -ml-1 mr-2 h-5 w-5 text-white"
          xmlns="http://www.w3.org/2000/svg"
          fill="none"
          viewBox="0 0 24 24"
        >
          <circle
            class="opacity-25"
            cx="12"
            cy="12"
            r="10"
            stroke="currentColor"
            stroke-width="4"
          ></circle>
          <path
            class="opacity-75"
            fill="currentColor"
            d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
          ></path>
        </svg>
        <span v-if="!loading">Đăng nhập</span>
        <span v-else>Đang đăng nhập...</span>
      </button>
    </form>

    <!-- Divider -->
    <!-- <div class="relative">
      <div class="absolute inset-0 flex items-center">
        <div class="w-full border-t border-gray-200"></div>
      </div>
      <div class="relative flex justify-center text-sm">
        <span class="px-4 bg-white text-gray-500">hoặc tiếp tục với</span>
      </div>
    </div> -->

    <!-- Google Login -->
    <!-- <button type="button" class="btn-google" :disabled="loadingGoogle" @click="loginWithGoogle">
      <svg v-if="!loadingGoogle" class="w-5 h-5" viewBox="0 0 24 24">
        <path
          fill="#4285F4"
          d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
        />
        <path
          fill="#34A853"
          d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
        />
        <path
          fill="#FBBC05"
          d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
        />
        <path
          fill="#EA4335"
          d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
        />
      </svg>
      <svg
        v-else
        class="animate-spin h-5 w-5 text-gray-700"
        xmlns="http://www.w3.org/2000/svg"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        ></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>
      <span class="ml-3 font-medium">{{ loadingGoogle ? 'Đang kết nối...' : 'Google' }}</span>
    </button> -->

    <!-- Register Link -->
    <p class="text-center text-sm text-gray-600">
      Chưa có tài khoản?
      <RouterLink
        to="/auth/register"
        class="font-medium text-pink-600 hover:text-pink-700 transition"
      >
        Đăng ký ngay
      </RouterLink>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from '@/store/auth.store'

const auth = useAuthStore()

const loading = ref(false)
// const loadingGoogle = ref(false)
const showPassword = ref(false)

const form = reactive({
  email: '',
  password: '',
  remember: true,
})

const errors = reactive({
  email: '',
  password: '',
})

function validateEmail() {
  if (!form.email.trim()) {
    errors.email = 'Vui lòng nhập email hoặc username'
    return false
  }
  errors.email = ''
  return true
}

function validatePassword() {
  if (!form.password) {
    errors.password = 'Vui lòng nhập mật khẩu'
    return false
  }
  if (form.password.length < 6) {
    errors.password = 'Mật khẩu tối thiểu 6 ký tự'
    return false
  }
  errors.password = ''
  return true
}

function validate() {
  const emailValid = validateEmail()
  const passwordValid = validatePassword()
  return emailValid && passwordValid
}

const onSubmit = async () => {
  if (!validate()) return

  loading.value = true
  try {
    await auth.login(form.email, form.password, form.remember)
    showToast('Đăng nhập thành công!', 'success')
  } catch (e: any) {
    // showToast(e?.message || 'Đăng nhập thất bại', 'error')
    showToast('Đăng nhập thất bại', 'error')
  } finally {
    loading.value = false
  }
}

// const loginWithGoogle = async () => {
//   loadingGoogle.value = true
//   try {
//     await auth.loginWithGoogle()
//     showToast('Đăng nhập Google thành công!', 'success')
//   } catch (e: any) {
//     showToast(e?.message || 'Đăng nhập Google thất bại', 'error')
//   } finally {
//     loadingGoogle.value = false
//   }
// }

function showToast(message: string, type: 'success' | 'error') {
  const toast = document.createElement('div')
  toast.className = `fixed top-4 right-4 px-6 py-3 rounded-lg shadow-lg text-white z-50 animate-slide-in ${
    type === 'success' ? 'bg-pink-600' : 'bg-red-600'
  }`
  toast.textContent = message
  document.body.appendChild(toast)

  setTimeout(() => {
    toast.classList.add('animate-slide-out')
    setTimeout(() => toast.remove(), 300)
  }, 3000)
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
  @apply focus:outline-none focus:ring-2 focus:ring-pink-500/30 focus:border-pink-500;
  @apply transition duration-200;
}

.form-input:hover {
  @apply border-gray-300;
}

.input-icon {
  @apply absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none z-10;
}

.form-error {
  @apply text-xs text-red-600 mt-1.5 flex items-start gap-1.5;
}

/* Primary Button — Pink gradient */
.btn-primary {
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0.75rem 1.5rem !important;
  border-radius: 0.75rem !important;
  background: linear-gradient(
    to right,
    rgb(236, 72, 153),
    rgb(219, 39, 119)
  ) !important; /* #ec4899 → #db2777 */
  color: white !important;
  font-weight: 600 !important;
  transition: all 0.2s !important;
  transform-origin: center !important;
  box-shadow: 0 10px 15px -3px rgba(236, 72, 153, 0.25) !important;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(
    to right,
    rgb(219, 39, 119),
    rgb(190, 24, 93)
  ) !important; /* #db2777 → #be185d */
}

.btn-primary:focus {
  outline: none !important;
  box-shadow:
    0 0 0 2px rgba(236, 72, 153, 0.5),
    0 10px 15px -3px rgba(236, 72, 153, 0.25) !important;
}

.btn-primary:active:not(:disabled) {
  transform: scale(0.98) !important;
}

.btn-primary:disabled {
  opacity: 0.6 !important;
  cursor: not-allowed !important;
}

/* Google Button giữ nguyên */
.btn-google {
  width: 100% !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  padding: 0.75rem 1.5rem !important;
  border-radius: 0.75rem !important;
  background: white !important;
  border: 1px solid rgb(229, 231, 235) !important;
  color: rgb(55, 65, 81) !important;
  font-weight: 500 !important;
  transition: all 0.2s !important;
  transform-origin: center !important;
}

.btn-google:hover:not(:disabled) {
  background: rgb(249, 250, 251) !important;
  border-color: rgb(209, 213, 219) !important;
}

.btn-google:focus {
  outline: none !important;
  box-shadow: 0 0 0 2px rgb(229, 231, 235) !important;
}

.btn-google:active:not(:disabled) {
  transform: scale(0.98) !important;
}

/* Toast animation */
@keyframes slide-in {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
@keyframes slide-out {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}
.animate-slide-in {
  animation: slide-in 0.3s ease-out;
}
.animate-slide-out {
  animation: slide-out 0.3s ease-in;
}
</style>
