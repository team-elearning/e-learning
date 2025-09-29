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
            <div class="pwd-wrap">
              <input
                :type="show.cur ? 'text' : 'password'"
                v-model.trim="pwd.current"
                class="input"
                autocomplete="current-password"
              />
              <button type="button" class="eye" @click="show.cur = !show.cur" :aria-label="show.cur ? 'Ẩn' : 'Hiện'">
                <svg viewBox="0 0 24 24"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12Z"/><circle cx="12" cy="12" r="3.5"/></svg>
              </button>
              <p v-if="errs.current" class="err">{{ errs.current }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Mật khẩu mới <span class="req">*</span></label>
            <div class="pwd-wrap">
              <input
                :type="show.new1 ? 'text' : 'password'"
                v-model.trim="pwd.new1"
                class="input"
                autocomplete="new-password"
              />
              <button type="button" class="eye" @click="show.new1 = !show.new1" :aria-label="show.new1 ? 'Ẩn' : 'Hiện'">
                <svg viewBox="0 0 24 24"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12Z"/><circle cx="12" cy="12" r="3.5"/></svg>
              </button>
              <p v-if="errs.new1" class="err">{{ errs.new1 }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Nhập lại mật khẩu mới <span class="req">*</span></label>
            <div class="pwd-wrap">
              <input
                :type="show.new2 ? 'text' : 'password'"
                v-model.trim="pwd.new2"
                class="input"
                autocomplete="new-password"
              />
              <button type="button" class="eye" @click="show.new2 = !show.new2" :aria-label="show.new2 ? 'Ẩn' : 'Hiện'">
                <svg viewBox="0 0 24 24"><path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12Z"/><circle cx="12" cy="12" r="3.5"/></svg>
              </button>
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
.tab{ padding:10px 14px; border-radius:8px; border:1px solid transparent; background:#fff; cursor:pointer; font-weight:700; }
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
.row{ display:grid; grid-template-columns: 220px 1fr; gap:16px; align-items:center; margin-bottom:12px; }
.label{ text-align:left; color:#111827; font-weight:600; }
.req{ color:#ef4444; }
.input{ width:100%; padding:10px 12px; border:1px solid var(--line); border-radius:10px; background:#fff; outline:none; }
.input:focus{ border-color:var(--focus-border); box-shadow:0 0 0 3px var(--focus-ring); }
.actions{ display:flex; justify-content:flex-end; margin-top:16px; }
.btn-primary{ background:var(--accent); color:#fff; border:1px solid var(--accent); padding:12px 18px; border-radius:10px; font-weight:800; cursor:pointer; display:inline-flex; align-items:center; gap:8px; }
.btn-primary:disabled{ opacity:.6; cursor:not-allowed; }

/* Spinner */
.spinner{ width:14px; height:14px; border:2px solid rgba(255,255,255,.6); border-top-color:#fff; border-radius:50%; animation:spin .8s linear infinite; }
@keyframes spin{ to{ transform:rotate(360deg); } }

/* Password eye icon */
.pwd-wrap{ position:relative; }
.eye{
  position:absolute; right:10px; top:50%; transform:translateY(-50%);
  background:#fff; border:0; padding:4px; border-radius:6px; cursor:pointer;
}
.eye svg{ width:18px; height:18px; fill:#9ca3af; }

/* Errors */
.err{ color:#dc2626; font-size:12px; margin-top:6px; }

/* Responsive */
@media (max-width: 840px){
  .row{ grid-template-columns: 1fr; }
  .label{ margin-bottom:4px; }
}
</style>
