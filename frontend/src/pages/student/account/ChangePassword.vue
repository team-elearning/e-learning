<!-- src/pages/student/account/ChangePassword.vue -->
<template>
  <div class="profile-page">
    <div class="container">
      <!-- Tabs -->
      <div class="tabs">
        <button class="tab" type="button" @click="goProfile">CÁ NHÂN</button>
        <button class="tab active" type="button">ĐỔI MẬT KHẨU</button>
      </div>

      <!-- Card -->
      <div class="card">
        <div class="card-head">
          <h2 class="card-title">ĐỔI MẬT KHẨU</h2>
        </div>

        <!-- Toast -->
        <transition name="fade">
          <div v-if="toast.msg" :class="['toast', toast.type]">
            {{ toast.msg }}
          </div>
        </transition>

        <!-- FORM -->
        <form class="form" @submit.prevent="changePassword">
          <div class="row">
            <label class="label">Mật khẩu hiện tại <span class="req">*</span></label>
            <div>
              <div class="pwd-wrap">
                <input
                  :type="show.cur ? 'text' : 'password'"
                  v-model.trim="pwd.current"
                  class="input"
                  autocomplete="current-password"
                />
                <button
                  type="button"
                  class="eye"
                  @click="show.cur = !show.cur"
                  :aria-label="show.cur ? 'Ẩn' : 'Hiện'"
                >
                  <svg
                    v-if="show.cur"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
                    />
                  </svg>
                  <svg
                    v-else
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </button>
              </div>
              <p v-if="errs.current" class="err">{{ errs.current }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Mật khẩu mới <span class="req">*</span></label>
            <div>
              <div class="pwd-wrap">
                <input
                  :type="show.new1 ? 'text' : 'password'"
                  v-model.trim="pwd.new1"
                  class="input"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  class="eye"
                  @click="show.new1 = !show.new1"
                  :aria-label="show.new1 ? 'Ẩn' : 'Hiện'"
                >
                  <svg
                    v-if="show.new1"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
                    />
                  </svg>
                  <svg
                    v-else
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </button>
              </div>
              <p v-if="errs.new1" class="err">{{ errs.new1 }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Nhập lại mật khẩu mới <span class="req">*</span></label>
            <div>
              <div class="pwd-wrap">
                <input
                  :type="show.new2 ? 'text' : 'password'"
                  v-model.trim="pwd.new2"
                  class="input"
                  autocomplete="new-password"
                />
                <button
                  type="button"
                  class="eye"
                  @click="show.new2 = !show.new2"
                  :aria-label="show.new2 ? 'Ẩn' : 'Hiện'"
                >
                  <svg
                    v-if="show.new2"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"
                    />
                  </svg>
                  <svg
                    v-else
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke-width="1.5"
                    stroke="currentColor"
                  >
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"
                    />
                    <path
                      stroke-linecap="round"
                      stroke-linejoin="round"
                      d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                </button>
              </div>
              <p v-if="errs.new2" class="err">{{ errs.new2 }}</p>
            </div>
          </div>

          <div class="actions">
            <button type="submit" class="btn-primary" :disabled="saving || !isValid">
              <span v-if="saving" class="spinner"></span>
              CẬP NHẬT MẬT KHẨU
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth.store'

const router = useRouter()
const goProfile = () => router.push({ name: 'student-profile' })
// ❌ Đã xoá: const goParent = () => router.push({ name: 'student-parent' })
const auth = useAuthStore()

type Pwd = { current: string; new1: string; new2: string }
const pwd = reactive<Pwd>({ current: '', new1: '', new2: '' })
const show = reactive({ cur: false, new1: false, new2: false })
const errs = reactive<{ current?: string; new1?: string; new2?: string }>({})

watch(
  () => ({ ...pwd }),
  () => {
    errs.current = pwd.current ? '' : 'Vui lòng nhập mật khẩu hiện tại.'
    errs.new1 = pwd.new1.length >= 6 ? '' : 'Mật khẩu mới tối thiểu 6 ký tự.'
    errs.new2 = pwd.new2 === pwd.new1 ? '' : 'Xác nhận mật khẩu chưa khớp.'
  },
  { deep: true, immediate: true },
)

const isValid = computed(() => !errs.current && !errs.new1 && !errs.new2)
const saving = ref(false)

const toast = reactive<{ msg: string; type: 'success' | 'error' | '' }>({ msg: '', type: '' })
let toastTimer: number | undefined
function showToast(msg: string, type: 'success' | 'error') {
  toast.msg = msg
  toast.type = type
  clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => (toast.msg = ''), 2500)
}

async function changePassword() {
  if (!isValid.value) return
  saving.value = true
  try {
    await auth.changePassword(pwd.current, pwd.new1)
    showToast('Đổi mật khẩu thành công!', 'success')
    pwd.current = pwd.new1 = pwd.new2 = ''
  } catch (e) {
    showToast('Có lỗi xảy ra, vui lòng thử lại.', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<!-- Giữ nguyên biến toàn cục như Profile.vue -->
<style>
:root {
  --bg: #f6f7fb;
  --card: #fff;
  --text: #0f172a;
  --muted: #6b7280;
  --line: #e5e7eb;
  --accent: #16a34a;
  --accent-tint-bg: #ecfdf5;
  --accent-tint-border: #bbf7d0;
  --focus-border: #86efac;
  --focus-ring: rgba(22, 163, 74, 0.18);
}
</style>

<style scoped>
/* ===== layout giống Profile.vue bạn gửi ===== */
.profile-page {
  background: var(--bg);
  min-height: 100vh;
  color: var(--text);
}
.container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 16px 10px 32px;
}

/* Tabs */
.tabs {
  display: flex;
  gap: 4px;
  background: #fff;
  border: 1px solid var(--line);
  border-radius: 10px;
  padding: 4px;
  width: 100%;
}
.tab {
  flex: 1;
  padding: 8px 4px;
  border-radius: 8px;
  border: 1px solid transparent;
  background: #fff;
  cursor: pointer;
  font-weight: 700;
  white-space: nowrap;
  text-align: center;
  font-size: 10px;
  line-height: 1.3;
}
.tab.active {
  color: var(--accent);
  border-color: var(--accent-tint-border);
  background: var(--accent-tint-bg);
}

/* Card */
.card {
  background: var(--card);
  border: 1px solid var(--line);
  border-radius: 12px;
  margin-top: 10px;
  padding: 12px;
}
.card-head {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.card-title {
  font-weight: 800;
  font-size: 14px;
}

/* Toast */
.toast {
  position: fixed;
  right: 10px;
  bottom: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid;
  z-index: 40;
  font-size: 12px;
}
.toast.success {
  background: #f0fdf4;
  color: #166534;
  border-color: #bbf7d0;
}
.toast.error {
  background: #fef2f2;
  color: #991b1b;
  border-color: #fecaca;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Form */
.form {
  margin-top: 4px;
}
.row {
  display: grid;
  grid-template-columns: 1fr;
  gap: 4px;
  margin-bottom: 10px;
}
.label {
  text-align: left;
  color: #111827;
  font-weight: 600;
  font-size: 12px;
  margin-bottom: 4px;
}
.req {
  color: #ef4444;
}

.input {
  width: 100%;
  padding: 9px 40px 9px 10px;
  border: 1px solid var(--line);
  border-radius: 10px;
  background: #fff;
  outline: none;
  font-size: 14px;
}
.input:focus {
  border-color: var(--focus-border);
  box-shadow: 0 0 0 3px var(--focus-ring);
}

.pwd-wrap {
  position: relative;
  display: block;
  width: 100%;
}
.eye {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: transparent;
  border: 0;
  padding: 6px;
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #9ca3af;
  transition: all 0.2s;
}
.eye:hover {
  background: #f3f4f6;
  color: #6b7280;
}
.eye svg {
  width: 18px;
  height: 18px;
}

/* Actions + Button (y hệt sizing Profile) */
.actions {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 12px;
}
.btn-primary {
  background: var(--accent) !important;
  color: #fff !important;
  border: 1px solid var(--accent) !important;
  padding: 10px 14px !important;
  border-radius: 10px !important;
  font-weight: 800 !important;
  cursor: pointer !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  font-size: 12px !important;
  width: 100% !important; /* full-width mobile */
}
.btn-primary:disabled {
  background: #d1d5db !important;
  border-color: #d1d5db !important;
  color: #6b7280 !important;
  cursor: not-allowed !important;
}
.btn-primary:not(:disabled):hover {
  filter: brightness(1.06);
  transform: translateY(-1px);
  transition: 0.15s ease;
}
.spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(255, 255, 255, 0.6);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.err {
  color: #dc2626;
  font-size: 10px;
  margin-top: 4px;
  line-height: 1.4;
}

/* ===== Breakpoints trùng Profile.vue ===== */
@media (min-width: 641px) {
  .container {
    padding: 20px 14px 36px;
  }
  .tabs {
    gap: 6px;
    padding: 6px;
  }
  .tab {
    padding: 10px 10px;
    font-size: 12px;
  }
  .card {
    padding: 14px;
  }
  .card-title {
    font-size: 15px;
  }
}

@media (min-width: 841px) {
  .container {
    padding: 24px 16px 40px;
  }
  .tab {
    padding: 10px 14px;
    font-size: 13px;
  }
  .card {
    padding: 16px;
  }
  .card-title {
    font-size: 16px;
  }

  .row {
    grid-template-columns: 220px 1fr;
    gap: 14px;
  }
  .label {
    font-size: 14px;
    padding-top: 10px;
  }

  .actions {
    align-items: flex-end;
  }
  .btn-primary {
    width: auto !important;
  } /* nút co theo nội dung ở desktop */
}
</style>
