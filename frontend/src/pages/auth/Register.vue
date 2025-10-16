<template>
  <div class="space-y-6">
    <form @submit.prevent="onSubmit" class="space-y-5" autocomplete="off">
      <!-- Full Name -->
      <div class="form-group">
        <label for="fullName" class="form-label">
          Họ và tên
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <div class="input-icon">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
            </svg>
          </div>
          <input
            id="fullName"
            v-model="form.fullName"
            type="text"
            name="fullname-register"
            placeholder="Nguyễn Văn A"
            autocomplete="off"
            class="form-input"
            :class="{ 'border-red-300': errors.fullName }"
            @blur="validateFullName"
            @input="errors.fullName = ''"
          />
        </div>
        <p v-if="errors.fullName" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>{{ errors.fullName }}</span>
        </p>
      </div>

      <!-- Username -->
      <div class="form-group">
        <label for="username" class="form-label">
          Username
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <div class="input-icon">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
            </svg>
          </div>
          <input
            id="username"
            v-model="form.username"
            type="text"
            name="username-register"
            placeholder="nguyenvana"
            autocomplete="off"
            class="form-input"
            :class="{ 'border-red-300': errors.username }"
            @blur="validateUsername"
            @input="errors.username = ''"
          />
        </div>
        <p v-if="errors.username" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>{{ errors.username }}</span>
        </p>
      </div>

      <!-- Email -->
      <div class="form-group">
        <label for="email" class="form-label">
          Email
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <div class="input-icon">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <input
            id="email"
            v-model="form.email"
            type="email"
            name="email-register"
            placeholder="you@example.com"
            autocomplete="off"
            class="form-input"
            :class="{ 'border-red-300': errors.email }"
            @blur="validateEmail"
            @input="errors.email = ''"
          />
        </div>
        <p v-if="errors.email" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>{{ errors.email }}</span>
        </p>
      </div>

      <!-- Phone -->
      <div class="form-group">
        <label for="phone" class="form-label">
          Số điện thoại
          <span class="text-red-500">*</span>
        </label>
        <div class="relative">
          <div class="input-icon">
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
            </svg>
          </div>
          <input
            id="phone"
            v-model="form.phone"
            type="tel"
            name="phone-register"
            placeholder="09xxxxxxxx"
            autocomplete="off"
            class="form-input"
            :class="{ 'border-red-300': errors.phone }"
            @blur="validatePhone"
            @input="errors.phone = ''"
          />
        </div>
        <p v-if="errors.phone" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>{{ errors.phone }}</span>
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
            <svg class="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
          </div>
          <input
            id="password"
            v-model="form.password"
            :type="showPassword ? 'text' : 'password'"
            name="password-register"
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
            <svg v-if="!showPassword" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            </svg>
          </button>
        </div>
        <p v-if="errors.password" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>{{ errors.password }}</span>
        </p>
        <div class="mt-2 space-y-1">
          <div class="flex items-center gap-2 text-xs" :class="form.password.length >= 6 ? 'text-emerald-600' : 'text-gray-400'">
            <svg class="w-4 h-4 flex-shrink-0" :class="form.password.length >= 6 ? 'text-emerald-600' : 'text-gray-300'" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd" />
            </svg>
            <span>Tối thiểu 6 ký tự</span>
          </div>
        </div>
      </div>

      <!-- Confirm Password -->
      <div class="form-group">
        <label for="confirm" class="form-label">
          Nhập lại mật khẩu
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
            v-model="form.confirm"
            :type="showConfirm ? 'text' : 'password'"
            name="confirm-register"
            placeholder="••••••••"
            autocomplete="new-password"
            class="form-input"
            :class="{ 'border-red-300': errors.confirm }"
            @blur="validateConfirm"
            @input="errors.confirm = ''"
          />
          <button
            type="button"
            class="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition p-1"
            @click="showConfirm = !showConfirm"
            tabindex="-1"
          >
            <svg v-if="!showConfirm" class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <svg v-else class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
            </svg>
          </button>
        </div>
        <p v-if="errors.confirm" class="form-error">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>{{ errors.confirm }}</span>
        </p>
      </div>

      <!-- Terms -->
      <div class="pt-1">
        <label class="flex items-start cursor-pointer group">
          <input
            v-model="form.agree"
            type="checkbox"
            class="mt-0.5 w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-2 focus:ring-emerald-500/30 transition flex-shrink-0"
          />
          <span class="ml-3 text-sm text-gray-600 group-hover:text-gray-900 transition">
            Tôi đã đọc và đồng ý với 
            <a href="#" class="text-emerald-600 hover:text-emerald-700 font-medium">Điều khoản dịch vụ</a>
          </span>
        </label>
        <p v-if="errors.agree" class="form-error mt-1.5">
          <svg class="w-3.5 h-3.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
          <span>{{ errors.agree }}</span>
        </p>
      </div>

      <!-- Submit Button -->
      <button
        type="submit"
        class="btn-primary"
        :disabled="loading"
        :class="{ 'opacity-60 cursor-not-allowed': loading }"
      >
        <svg v-if="loading" class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
          <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
          <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
        </svg>
        <span v-if="!loading">Đăng ký</span>
        <span v-else>Đang xử lý...</span>
      </button>
    </form>

    <!-- Login Link -->
    <p class="text-center text-sm text-gray-600">
      Đã có tài khoản?
      <RouterLink
        to="/auth/login"
        class="font-medium text-emerald-600 hover:text-emerald-700 transition"
      >
        Đăng nhập ngay
      </RouterLink>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { authService } from '@/services/auth.service'
import { useRouter } from 'vue-router'

const router = useRouter()

const loading = ref(false)
const showPassword = ref(false)
const showConfirm = ref(false)

const form = reactive({
  fullName: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm: '',
  agree: false,
})

const errors = reactive({
  fullName: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm: '',
  agree: '',
})

function validateFullName() {
  if (!form.fullName) {
    errors.fullName = 'Vui lòng nhập họ tên'
    return false
  }
  errors.fullName = ''
  return true
}

function validateUsername() {
  if (!form.username) {
    errors.username = 'Vui lòng nhập username'
    return false
  }
  errors.username = ''
  return true
}

function validateEmail() {
  if (!form.email) {
    errors.email = 'Vui lòng nhập email'
    return false
  }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) {
    errors.email = 'Email không hợp lệ'
    return false
  }
  errors.email = ''
  return true
}

function validatePhone() {
  if (!form.phone) {
    errors.phone = 'Vui lòng nhập số điện thoại'
    return false
  }
  if (!/^0\d{9,10}$/.test(form.phone)) {
    errors.phone = 'Số điện thoại không hợp lệ'
    return false
  }
  errors.phone = ''
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

function validateConfirm() {
  if (!form.confirm) {
    errors.confirm = 'Vui lòng nhập lại mật khẩu'
    return false
  }
  if (form.password !== form.confirm) {
    errors.confirm = 'Mật khẩu không khớp'
    return false
  }
  errors.confirm = ''
  return true
}

function validateAgree() {
  if (!form.agree) {
    errors.agree = 'Vui lòng đồng ý với điều khoản'
    return false
  }
  errors.agree = ''
  return true
}

function validate() {
  const fullNameValid = validateFullName()
  const usernameValid = validateUsername()
  const emailValid = validateEmail()
  const phoneValid = validatePhone()
  const passwordValid = validatePassword()
  const confirmValid = validateConfirm()
  const agreeValid = validateAgree()
  
  return fullNameValid && usernameValid && emailValid && phoneValid && passwordValid && confirmValid && agreeValid
}

const onSubmit = async () => {
  if (!validate()) return

  loading.value = true
  try {
    await authService.register({
      fullName: form.fullName,
      username: form.username,
      email: form.email,
      phone: form.phone,
      password: form.password,
      confirm: form.confirm,
      agree: form.agree,
    })
    
    showToast('Đăng ký thành công. Vui lòng đăng nhập.', 'success')
    router.push('/auth/login')
  } catch (e: any) {
    showToast(e?.message || 'Đăng ký thất bại', 'error')
  } finally {
    loading.value = false
  }
}

function showToast(message: string, type: 'success' | 'error') {
  const toast = document.createElement('div')
  toast.className = `fixed top-4 right-4 max-w-[calc(100vw-2rem)] sm:max-w-sm px-6 py-3 rounded-lg shadow-lg text-white z-[9999] ${
    type === 'success' ? 'bg-emerald-600' : 'bg-red-600'
  }`
  toast.style.cssText = `
    word-break: break-word;
    transform: translateX(400px);
    opacity: 0;
    transition: all 0.3s ease-out;
  `
  
  document.body.appendChild(toast)
  
  requestAnimationFrame(() => {
    toast.style.transform = 'translateX(0)'
    toast.style.opacity = '1'
  })
  
  setTimeout(() => {
    toast.style.transform = 'translateX(400px)'
    toast.style.opacity = '0'
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
  @apply focus:outline-none focus:ring-2 focus:ring-emerald-500/30 focus:border-emerald-500;
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
</style>
