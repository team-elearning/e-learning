<template>
  <div class="profile-page">
    <div class="container">
      <!-- Tabs -->
      <div class="tabs">
        <button class="tab" type="button" @click="goProfile">THÔNG TIN CÁ NHÂN</button>
        <button class="tab active" type="button">ĐỔI MẬT KHẨU</button>
        <button class="tab" type="button" @click="goParent">THÔNG TIN PHỤ HUYNH</button>
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

        <!-- Form -->
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
                <button type="button" class="eye" @click="show.cur = !show.cur" :aria-label="show.cur ? 'Ẩn' : 'Hiện'">
                  <!-- Eye Icon (khi đang hiện password) -->
                  <svg v-if="show.cur" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                  </svg>
                  <!-- Eye Slash Icon (khi đang ẩn password) -->
                  <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
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
                <button type="button" class="eye" @click="show.new1 = !show.new1" :aria-label="show.new1 ? 'Ẩn' : 'Hiện'">
                  <svg v-if="show.new1" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
              </div>
              <p v-if="errs.new1" class="err">{{ errs.new1}}</p>
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
                <button type="button" class="eye" @click="show.new2 = !show.new2" :aria-label="show.new2 ? 'Ẩn' : 'Hiện'">
                  <svg v-if="show.new2" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
                  </svg>
                  <svg v-else xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                  </svg>
                </button>
              </div>
              <p v-if="errs.new2" class="err">{{ errs.new2}}</p>
            </div>
          </div>

          <div class="actions">
            <button 
              type="submit" 
              class="btn-primary" 
              :class="{ 'is-busy': saving }"
              :disabled="saving || !isValid"
            >
              <span v-if="saving" class="spinner"></span>
              {{ saving ? 'ĐANG CẬP NHẬT...' : 'CẬP NHẬT MẬT KHẨU' }}
            </button>
            <small v-if="!isValid" class="btn-hint">
              Vui lòng điền đầy đủ và chính xác tất cả các trường
            </small>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, watch, computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const goProfile = () => router.push({ name: 'student-profile' })
const goParent  = () => router.push({ name: 'student-parent' })

type Pwd = { current: string; new1: string; new2: string }
const pwd  = reactive<Pwd>({ current: '', new1: '', new2: '' })
const show = reactive({ cur: false, new1: false, new2: false })
const errs = reactive<{ current?: string; new1?: string; new2?: string }>({})

watch(() => ({ ...pwd }), () => {
  errs.current = pwd.current ? '' : 'Vui lòng nhập mật khẩu hiện tại.'
  errs.new1    = pwd.new1.length >= 6 ? '' : 'Mật khẩu mới tối thiểu 6 ký tự.'
  errs.new2    = pwd.new2 === pwd.new1 ? '' : 'Xác nhận mật khẩu chưa khớp.'
}, { deep: true, immediate: true })

const isValid = computed(() => !errs.current && !errs.new1 && !errs.new2)
const saving  = ref(false)

const toast = reactive<{ msg: string; type: 'success' | 'error' | '' }>({ msg: '', type: '' })
let toastTimer: number | undefined
function showToast(msg: string, type: 'success' | 'error') {
  toast.msg = msg; toast.type = type
  clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => (toast.msg = ''), 2500)
}

async function changePassword() {
  if (!isValid.value) return
  saving.value = true
  try {
    // TODO: gọi API đổi mật khẩu
    await new Promise(r => setTimeout(r, 800))
    showToast('Đổi mật khẩu thành công!', 'success')
    pwd.current = pwd.new1 = pwd.new2 = ''
  } catch (e) {
    showToast('Có lỗi xảy ra, vui lòng thử lại.', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<!-- ======= GLOBAL THEME (đồng bộ Profile) ======= -->
<style>
:root{
  --bg:#f6f7fb; --card:#fff; --text:#0f172a; --muted:#6b7280; --line:#e5e7eb;
  --accent:#16a34a; --accent-tint-bg:#ecfdf5; --accent-tint-border:#bbf7d0;
  --focus-border:#86efac; --focus-ring:rgba(22,163,74,.18);
}
</style>

<!-- ======= SCOPED STYLES ======= -->
<style scoped>
.profile-page{ background:var(--bg); min-height:100vh; color:var(--text); }
.container{ max-width:1000px; margin:0 auto; padding:24px 16px 40px; }

/* Tabs */
.tabs{ display:flex; gap:8px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:6px; width:max-content; }
.tab{ padding:10px 14px; border-radius:8px; border:1px solid transparent; background:#fff; cursor:pointer; font-weight:700; transition: all 0.2s ease; }
.tab:hover:not(.active){ background:#f9fafb; }
.tab.active{ color:var(--accent); border-color:var(--accent-tint-border); background:var(--accent-tint-bg); }

/* Card */
.card{ background:var(--card); border:1px solid var(--line); border-radius:14px; margin-top:12px; padding:16px 16px 20px; }
.card-head{ display:flex; justify-content:space-between; align-items:center; gap:12px; }
.card-title{ font-weight:800; }

/* Toast */
.toast{ position:fixed; right:18px; bottom:18px; padding:10px 12px; border-radius:10px; border:1px solid; z-index:40;}
.toast.success{ background:#f0fdf4; color:#166534; border-color:#bbf7d0; }
.toast.error{ background:#fef2f2; color:#991b1b; border-color:#fecaca; }
.fade-enter-active,.fade-leave-active{ transition:opacity .2s; } .fade-enter-from,.fade-leave-to{ opacity:0; }

/* Form */
.form{ margin-top:6px; }
.row{ display:grid; grid-template-columns: 220px 1fr; gap:16px; align-items:start; margin-bottom:12px; }
.label{ text-align:left; color:#111827; font-weight:600; padding-top:10px; }
.req{ color:#ef4444; }
.input{ width:100%; padding:10px 40px 10px 12px; border:1px solid var(--line); border-radius:10px; background:#fff; outline:none; transition: all 0.2s ease; }
.input:focus{ border-color:var(--focus-border); box-shadow:0 0 0 3px var(--focus-ring); }
.actions{ display:flex; flex-direction:column; align-items:flex-end; gap:8px; margin-top:16px; }

/* ===========================
   NÚT PRIMARY - DÙNG !IMPORTANT
   =========================== */
.btn-primary{
  background: var(--accent) !important;
  color: #fff !important;
  border: 1px solid var(--accent) !important;
  padding: 12px 18px !important;
  border-radius: 10px !important;
  font-weight: 800 !important;
  cursor: pointer !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  transition: all 0.2s ease !important;
}

/* Nút khi KHÔNG disabled - hover */
.btn-primary:not(:disabled):hover{ 
  filter: brightness(1.1) !important;
  transform: translateY(-1px) !important;
}

/* Nút khi DISABLED - màu xám */
.btn-primary:disabled{
  background: #d1d5db !important;
  border-color: #d1d5db !important;
  color: #6b7280 !important;
  cursor: not-allowed !important;
  opacity: 1 !important;
}

/* Nút khi đang SAVING */
.btn-primary.is-busy{
  background: var(--accent) !important;
  color: #fff !important;
  opacity: .7 !important;
  cursor: progress !important;
}

.btn-hint{
  font-size:12px;
  color:var(--muted);
  text-align:right;
  font-style:italic;
}

/* Spinner */
.spinner{ width:14px; height:14px; border:2px solid rgba(255,255,255,.6); border-top-color:#fff; border-radius:50%; animation:spin .8s linear infinite; }
@keyframes spin{ to{ transform:rotate(360deg); } }

/* Password eye icon */
.pwd-wrap{ 
  position:relative; 
  display:block;
  width: 100%;
}
.eye{
  position:absolute !important;
  right:8px !important;
  top:50% !important;
  transform:translateY(-50%) !important;
  background:transparent !important;
  border:0 !important;
  padding:6px !important;
  border-radius:6px !important;
  cursor:pointer !important;
  z-index: 10 !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  transition: all 0.2s ease !important;
  color: #9ca3af !important;
}
.eye:hover{ 
  background:#f3f4f6 !important;
  color: #6b7280 !important;
}
.eye svg{ 
  width:20px !important;
  height:20px !important;
}

/* Errors */
.err{ color:#dc2626; font-size:12px; margin-top:6px; display:block; }

/* Responsive */
@media (max-width: 840px){
  .row{ grid-template-columns: 1fr; align-items: stretch; }
  .label{ margin-bottom:4px; padding-top:0; }
}
</style>
