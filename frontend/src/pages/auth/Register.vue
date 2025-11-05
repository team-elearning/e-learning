UI xóa những
<template>
  <div class="register-wrapper">
    <form @submit.prevent="onSubmit" class="register-form" autocomplete="off">
      <!-- Full Name -->
      <!-- <div class="form-group">
        <label for="fullName" class="form-label"> Họ và tên <span class="required">*</span> </label>
        <div class="input-wrapper">
          <div class="input-icon">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
              />
            </svg>
          </div>
          <input
            id="fullName"
            v-model="form.fullName"
            type="text"
            placeholder="Nguyễn Văn A"
            class="form-input"
            :class="{ error: errors.fullName }"
            @blur="validateFullName"
            @input="errors.fullName = ''"
          />
        </div>
        <p v-if="errors.fullName" class="error-msg">
          <svg class="error-icon" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          {{ errors.fullName }}
        </p>
      </div> -->

      <!-- Username -->
      <div class="form-group">
        <label for="username" class="form-label"> Username <span class="required">*</span> </label>
        <div class="input-wrapper">
          <div class="input-icon">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
              />
            </svg>
          </div>
          <input
            id="username"
            v-model="form.username"
            type="text"
            placeholder="nguyenvana"
            class="form-input"
            :class="{ error: errors.username }"
            @blur="validateUsername"
            @input="errors.username = ''"
          />
        </div>
        <p v-if="errors.username" class="error-msg">
          <svg class="error-icon" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          {{ errors.username }}
        </p>
      </div>

      <!-- Email -->
      <div class="form-group">
        <label for="email" class="form-label"> Email <span class="required">*</span> </label>
        <div class="input-wrapper">
          <div class="input-icon">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
              />
            </svg>
          </div>
          <input
            id="email"
            v-model="form.email"
            type="email"
            placeholder="you@example.com"
            class="form-input"
            :class="{ error: errors.email }"
            @blur="validateEmail"
            @input="errors.email = ''"
          />
        </div>
        <p v-if="errors.email" class="error-msg">
          <svg class="error-icon" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          {{ errors.email }}
        </p>
      </div>

      <!-- Phone -->
      <div class="form-group">
        <label for="phone" class="form-label">
          Số điện thoại <span class="required">*</span>
        </label>
        <div class="input-wrapper">
          <div class="input-icon">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z"
              />
            </svg>
          </div>
          <input
            id="phone"
            v-model="form.phone"
            type="tel"
            placeholder="09xxxxxxxx"
            class="form-input"
            :class="{ error: errors.phone }"
            @blur="validatePhone"
            @input="errors.phone = ''"
          />
        </div>
        <p v-if="errors.phone" class="error-msg">
          <svg class="error-icon" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          {{ errors.phone }}
        </p>
      </div>

      <!-- Password -->
      <div class="form-group">
        <label for="password" class="form-label"> Mật khẩu <span class="required">*</span> </label>
        <div class="input-wrapper">
          <div class="input-icon">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
            placeholder="••••••••"
            class="form-input"
            :class="{ error: errors.password }"
            @blur="validatePassword"
            @input="errors.password = ''"
          />
          <button type="button" class="toggle-btn" @click="showPassword = !showPassword">
            <svg
              v-if="!showPassword"
              class="toggle-icon"
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
            <svg v-else class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
              />
            </svg>
          </button>
        </div>
        <p v-if="errors.password" class="error-msg">
          <svg class="error-icon" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          {{ errors.password }}
        </p>
        <div class="hint-wrapper">
          <div class="hint" :class="{ valid: form.password.length >= 6 }">
            <svg class="hint-icon" fill="currentColor" viewBox="0 0 20 20">
              <path
                fill-rule="evenodd"
                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                clip-rule="evenodd"
              />
            </svg>
            Tối thiểu 6 ký tự
          </div>
        </div>
      </div>

      <!-- Confirm Password -->
      <div class="form-group">
        <label for="confirm" class="form-label">
          Nhập lại mật khẩu <span class="required">*</span>
        </label>
        <div class="input-wrapper">
          <div class="input-icon">
            <svg class="icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <input
            id="confirm"
            v-model="form.confirm"
            :type="showConfirm ? 'text' : 'password'"
            placeholder="••••••••"
            class="form-input"
            :class="{ error: errors.confirm }"
            @blur="validateConfirm"
            @input="errors.confirm = ''"
          />
          <button type="button" class="toggle-btn" @click="showConfirm = !showConfirm">
            <svg
              v-if="!showConfirm"
              class="toggle-icon"
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
            <svg v-else class="toggle-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
              />
            </svg>
          </button>
        </div>
        <p v-if="errors.confirm" class="error-msg">
          <svg class="error-icon" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          {{ errors.confirm }}
        </p>
      </div>

      <!-- Terms -->
      <!-- <div class="terms-group">
        <label class="terms-label">
          <input v-model="form.agree" type="checkbox" class="terms-checkbox" />
          <span class="terms-text">
            Tôi đã đọc và đồng ý với
            <a href="#" class="terms-link">Điều khoản dịch vụ</a>
          </span>
        </label>
        <p v-if="errors.agree" class="error-msg">
          <svg class="error-icon" fill="currentColor" viewBox="0 0 20 20">
            <path
              fill-rule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
              clip-rule="evenodd"
            />
          </svg>
          {{ errors.agree }}
        </p>
      </div> -->

      <!-- Submit -->
      <button type="submit" class="submit-btn" :disabled="loading">
        <svg v-if="loading" class="spinner" fill="none" viewBox="0 0 24 24">
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
        <span v-if="!loading">Đăng ký</span>
        <span v-else>Đang xử lý...</span>
      </button>
    </form>

    <!-- Login Link -->
    <p class="login-link">
      Đã có tài khoản?
      <RouterLink to="/auth/login" class="login-link-text">Đăng nhập ngay</RouterLink>
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
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm: '',
})

const errors = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm: '',
})

// ✅ Validate Username
function validateUsername() {
  if (!form.username.trim()) {
    errors.username = 'Vui lòng nhập username'
    return false
  }
  errors.username = ''
  return true
}

// ✅ Validate Email
function validateEmail() {
  if (!form.email.trim()) {
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

// ✅ Validate Phone
function validatePhone() {
  if (!form.phone.trim()) {
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

// ✅ Validate Password
function validatePassword() {
  if (!form.password.trim()) {
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

// ✅ Validate Confirm Password
function validateConfirm() {
  if (!form.confirm.trim()) {
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

// ✅ Tổng hợp validate
function validate() {
  return (
    validateUsername() &&
    validateEmail() &&
    validatePhone() &&
    validatePassword() &&
    validateConfirm()
  )
}

// ✅ Submit Register
const onSubmit = async () => {
  if (!validate()) return

  loading.value = true
  try {
    await authService.register({
      username: form.username,
      email: form.email,
      password: form.password,
      phone: form.phone,
    })

    showToast('Đăng ký thành công! Vui lòng đăng nhập.', 'success')
    router.push('/auth/login')
  } catch (e: any) {
    showToast(e?.message || 'Đăng ký thất bại', 'error')
  } finally {
    loading.value = false
  }
}

// ✅ Toast UI
function showToast(message: string, type: 'success' | 'error') {
  const toast = document.createElement('div')
  toast.className = `toast-notification ${type === 'success' ? 'toast-success' : 'toast-error'}`
  toast.innerHTML = `
    <strong>${type === 'success' ? '✅' : '❌'} ${message}</strong>
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
.register-wrapper {
  display: flex;
  flex-direction: column;
  gap: 0.875rem;
}

.register-form {
  display: flex;
  flex-direction: column;
  gap: 0.625rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.form-label {
  font-size: 0.75rem;
  font-weight: 600;
  color: #374151;
}

.required {
  color: #ef4444;
}

.input-wrapper {
  position: relative;
}

.input-icon {
  position: absolute;
  left: 0.625rem;
  top: 50%;
  transform: translateY(-50%);
  pointer-events: none;
  z-index: 10;
}

.icon {
  width: 1rem;
  height: 1rem;
  color: #9ca3af;
}

/* ==== PINK THEME INPUT ==== */
.form-input {
  width: 100%;
  padding: 0.5rem 2.5rem 0.5rem 2.25rem;
  background: white;
  border: 2px solid rgba(236, 72, 153, 0.2); /* pink-500 @ 0.2 */
  border-radius: 0.625rem;
  font-size: 0.8125rem;
  color: #1f2937;
  transition: all 0.2s;
}

.form-input::placeholder {
  color: #9ca3af;
}

.form-input:hover {
  border-color: rgba(236, 72, 153, 0.4);
}

.form-input:focus {
  outline: none;
  border-color: #ec4899; /* pink-500 */
  box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.12);
}

.form-input.error {
  border-color: #ef4444;
}

/* Toggle (show/hide password) */
.toggle-btn {
  position: absolute;
  right: 0.625rem;
  top: 50%;
  transform: translateY(-50%);
  background: none;
  border: none;
  cursor: pointer;
  padding: 0.25rem;
  color: #9ca3af;
  transition: color 0.2s;
}
.toggle-btn:hover {
  color: #ec4899;
}

.toggle-icon {
  width: 1rem;
  height: 1rem;
}

/* Error text */
.error-msg {
  display: flex;
  align-items: flex-start;
  gap: 0.1875rem;
  font-size: 0.625rem;
  color: #ef4444;
  margin-top: 0.125rem;
}
.error-icon {
  width: 0.625rem;
  height: 0.625rem;
  flex-shrink: 0;
  margin-top: 0.0625rem;
}

/* Password hints */
.hint-wrapper {
  margin-top: 0.25rem;
}

.hint {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  font-size: 0.625rem;
  color: #9ca3af;
  transition: color 0.2s;
}
.hint.valid {
  color: #ec4899;
} /* pink when valid */
.hint-icon {
  width: 0.75rem;
  height: 0.75rem;
  flex-shrink: 0;
}

/* Terms */
.terms-group {
  padding-top: 0.125rem;
}
.terms-label {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  cursor: pointer;
}

.terms-checkbox {
  margin-top: 0.0625rem;
  width: 0.875rem;
  height: 0.875rem;
  flex-shrink: 0;
  border: 2px solid rgba(236, 72, 153, 0.4);
  border-radius: 0.25rem;
  cursor: pointer;
  accent-color: #ec4899; /* pink */
}

.terms-text {
  font-size: 0.6875rem;
  color: #6b7280;
  line-height: 1.35;
}

.terms-link {
  color: #ec4899;
  font-weight: 700;
  text-decoration: none;
  transition: color 0.2s;
}
.terms-link:hover {
  color: #db2777;
}

/* ==== SUBMIT BUTTON – PINK GRADIENT ==== */
.submit-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #ec4899, #db2777, #be185d);
  background-size: 200% 200%;
  color: white;
  font-weight: 700;
  font-size: 0.8125rem;
  border: none;
  border-radius: 0.625rem;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 16px rgba(236, 72, 153, 0.3);
  animation: gradient-shift 3s ease infinite;
  margin-top: 0.25rem;
}

@keyframes gradient-shift {
  0%,
  100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 20px rgba(236, 72, 153, 0.4);
}

.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}
.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

/* Spinner */
.spinner {
  width: 1rem;
  height: 1rem;
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* Footer link */
.login-link {
  text-align: center;
  font-size: 0.75rem;
  color: #6b7280;
}
.login-link-text {
  font-weight: 700;
  color: #ec4899;
  text-decoration: none;
  transition: color 0.2s;
}
.login-link-text:hover {
  color: #db2777;
}

/* ==== TOAST ==== */
:global(.toast-notification) {
  position: fixed;
  top: 1rem;
  right: 1rem;
  max-width: calc(100vw - 2rem);
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 0.875rem 1rem;
  border-radius: 12px;
  backdrop-filter: blur(12px);
  box-shadow: 0 12px 30px rgba(0, 0, 0, 0.2);
  z-index: 9999;
  transform: translateX(400px);
  opacity: 0;
  transition: all 0.3s ease-out;
}

:global(.toast-success) {
  background: linear-gradient(135deg, rgba(236, 72, 153, 0.98), rgba(219, 39, 119, 0.98));
  border: 1px solid rgba(236, 72, 153, 0.5);
}

:global(.toast-error) {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.98), rgba(220, 38, 38, 0.98));
  border: 1px solid rgba(239, 68, 68, 0.5);
}

:global(.toast-icon-wrap) {
  width: 2rem;
  height: 2rem;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 10px;
}

:global(.toast-icon) {
  width: 1.25rem;
  height: 1.25rem;
  color: white;
  stroke-width: 2.5;
}
:global(.toast-body) {
  flex: 1;
  min-width: 0;
}
:global(.toast-title) {
  font-weight: 900;
  font-size: 0.875rem;
  color: white;
  margin-bottom: 0.25rem;
}
:global(.toast-msg) {
  font-size: 0.8125rem;
  color: rgba(255, 255, 255, 0.95);
  line-height: 1.3;
}

:global(.toast-bar) {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  width: 100%;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.3),
    rgba(255, 255, 255, 0.7),
    rgba(255, 255, 255, 0.3)
  );
  background-size: 200% 100%;
  animation:
    bar-shrink 3.5s linear forwards,
    bar-shimmer 1.5s linear infinite;
}
@keyframes bar-shrink {
  from {
    width: 100%;
  }
  to {
    width: 0%;
  }
}
@keyframes bar-shimmer {
  from {
    background-position: 200% 0;
  }
  to {
    background-position: -200% 0;
  }
}

/* RESPONSIVE */
@media (max-width: 640px) {
  .register-form {
    gap: 0.5rem;
  }
  .form-group {
    gap: 0.1875rem;
  }
  .form-label {
    font-size: 0.6875rem;
  }
  .form-input {
    padding: 0.4375rem 2.25rem 0.4375rem 2rem;
    font-size: 0.75rem;
  }
  .input-icon {
    left: 0.5rem;
  }
  .icon {
    width: 0.875rem;
    height: 0.875rem;
  }
  .toggle-btn {
    right: 0.5rem;
  }
  .toggle-icon {
    width: 0.875rem;
    height: 0.875rem;
  }
  .error-msg {
    font-size: 0.5625rem;
  }
  .error-icon {
    width: 0.5625rem;
    height: 0.5625rem;
  }
  .hint {
    font-size: 0.5625rem;
  }
  .hint-icon {
    width: 0.6875rem;
    height: 0.6875rem;
  }
  .terms-text {
    font-size: 0.625rem;
  }
  .submit-btn {
    padding: 0.4375rem 0.875rem;
    font-size: 0.75rem;
  }
  .spinner {
    width: 0.875rem;
    height: 0.875rem;
  }
  .login-link {
    font-size: 0.6875rem;
  }
  :global(.toast-notification) {
    top: 0.75rem;
    right: 0.75rem;
    left: 0.75rem;
    max-width: none;
  }
}
</style>
