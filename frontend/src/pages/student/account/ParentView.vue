<!-- src/pages/student/account/ParentInfo.vue -->
<template>
  <div class="profile-page">
    <div class="container">
      <!-- Tabs -->
      <div class="tabs">
        <button class="tab" type="button" @click="goProfile">THÔNG TIN CÁ NHÂN</button>
        <button class="tab" type="button" @click="goChangePwd">ĐỔI MẬT KHẨU</button>
        <button class="tab active" type="button">THÔNG TIN PHỤ HUYNH</button>
      </div>

      <!-- Card -->
      <div class="card">
        <div class="card-head">
          <h2 class="card-title">THÔNG TIN PHỤ HUYNH</h2>
        </div>

        <!-- Toast -->
        <transition name="fade">
          <div v-if="toast.msg" :class="['toast', toast.type]">
            {{ toast.msg }}
          </div>
        </transition>

        <!-- Form -->
        <form class="form" @submit.prevent="save">
          <div class="row">
            <label class="label">Họ tên phụ huynh <span class="req">*</span></label>
            <div>
              <input v-model.trim="f.fullname" class="input" placeholder="Ví dụ: Nguyễn Văn B" />
              <p v-if="errs.fullname" class="err">{{ errs.fullname }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Số điện thoại <span class="req">*</span></label>
            <div>
              <input v-model.trim="f.phone" type="tel" class="input" inputmode="tel" placeholder="09xxxxxxxx" />
              <p v-if="errs.phone" class="err">{{ errs.phone }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Email</label>
            <div>
              <input v-model.trim="f.email" type="email" class="input" placeholder="parent@example.com" />
              <p v-if="errs.email" class="err">{{ errs.email }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Mối quan hệ</label>
            <select v-model="f.relation" class="input select">
              <option value="">Chọn</option>
              <option>Bố</option>
              <option>Mẹ</option>
              <option>Người giám hộ</option>
            </select>
          </div>

          <div class="row">
            <label class="label">Địa chỉ</label>
            <div>
              <textarea v-model.trim="f.address" class="input" rows="3" placeholder="Số nhà, đường, phường/xã, quận/huyện, tỉnh/thành"></textarea>
            </div>
          </div>

          <div class="actions">
            <button 
              class="btn-primary" 
              :class="{ 'is-busy': saving }"
              :disabled="saving || !isValid"
              type="submit"
            >
              <span v-if="saving" class="spinner"></span>
              {{ saving ? 'ĐANG LƯU...' : 'LƯU THÔNG TIN' }}
            </button>
            <small v-if="!isValid" class="btn-hint">
              Vui lòng điền đầy đủ thông tin bắt buộc
            </small>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const goProfile   = () => router.push({ name: 'student-profile' })
const goChangePwd = () => router.push({ name: 'student-change-password' })

type ParentForm = { fullname: string; phone: string; email: string; relation: string; address: string }
const f = reactive<ParentForm>({ fullname: '', phone: '', email: '', relation: '', address: '' })
const errs = reactive<{ fullname?: string; phone?: string; email?: string }>({})
const isEmail = (v: string) => /^\S+@\S+\.\S+$/.test(v)

watch(() => ({ ...f }), () => {
  errs.fullname = f.fullname ? '' : 'Vui lòng nhập họ tên phụ huynh.'
  errs.phone    = f.phone    ? '' : 'Vui lòng nhập số điện thoại.'
  errs.email    = f.email && !isEmail(f.email) ? 'Email không hợp lệ.' : ''
}, { deep: true, immediate: true })

const isValid = computed(() => !errs.fullname && !errs.phone && !errs.email)
const saving  = ref(false)

const toast = reactive<{ msg: string; type: 'success' | 'error' | '' }>({ msg: '', type: '' })
let toastTimer: number | undefined
function showToast(msg: string, type: 'success' | 'error') {
  toast.msg = msg; toast.type = type
  clearTimeout(toastTimer)
  toastTimer = window.setTimeout(() => (toast.msg = ''), 2500)
}

async function save() {
  if (!isValid.value) return
  saving.value = true
  try {
    // TODO: gọi API lưu phụ huynh
    await new Promise(r => setTimeout(r, 800))
    showToast('Đã lưu thông tin phụ huynh!', 'success')
  } catch (e) {
    showToast('Lưu thất bại, thử lại sau.', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<!-- GLOBAL THEME (đồng bộ các trang account) -->
<style>
:root{
  --bg:#f6f7fb; --card:#fff; --text:#0f172a; --muted:#6b7280; --line:#e5e7eb;
  --accent:#16a34a; --accent-tint-bg:#ecfdf5; --accent-tint-border:#bbf7d0;
  --focus-border:#86efac; --focus-ring:rgba(22,163,74,.18);
}
</style>

<!-- SCOPED -->
<style scoped>
/* ===== Layout chung (mobile-first) ===== */
.profile-page{ background:var(--bg); min-height:100vh; color:var(--text); }
.container{ max-width:1000px; margin:0 auto; padding:16px 10px 32px; }

/* Tabs: full-width mobile, co lại ở desktop (giống Profile.vue) */
.tabs{
  display:flex; gap:4px; background:#fff; border:1px solid var(--line);
  border-radius:10px; padding:4px; width:100%;
}
.tab{
  flex:1; padding:8px 4px; border-radius:8px; border:1px solid transparent;
  background:#fff; cursor:pointer; font-weight:700; white-space:nowrap;
  text-align:center; font-size:10px; line-height:1.3; transition:.2s;
}
.tab:hover:not(.active){ background:#f9fafb; }
.tab.active{ color:var(--accent); border-color:var(--accent-tint-border); background:var(--accent-tint-bg); }

/* Card */
.card{ background:var(--card); border:1px solid var(--line); border-radius:12px; margin-top:10px; padding:12px; }
.card-head{ display:flex; justify-content:space-between; align-items:center; gap:8px; flex-wrap:wrap; margin-bottom:10px; }
.card-title{ font-weight:800; font-size:14px; }

/* Toast */
.toast{ position:fixed; right:10px; bottom:10px; padding:8px 10px; border-radius:10px; border:1px solid; z-index:40; font-size:12px; }
.toast.success{ background:#f0fdf4; color:#166534; border-color:#bbf7d0; }
.toast.error{ background:#fef2f2; color:#991b1b; border-color:#fecaca; }
.fade-enter-active,.fade-leave-active{ transition:opacity .2s; } .fade-enter-from,.fade-leave-to{ opacity:0; }

/* Form + fields */
.form{ margin-top:6px; }
.row{ display:grid; grid-template-columns:1fr; gap:6px; margin-bottom:12px; }
.label{ text-align:left; color:#111827; font-weight:600; font-size:12px; }
.req{ color:#ef4444; }

.input{
  width:100%; padding:10px 12px; border:1px solid var(--line); border-radius:10px;
  background:#fff; outline:none; font-size:14px; transition:.2s;
}
.input:focus{ border-color:var(--focus-border); box-shadow:0 0 0 3px var(--focus-ring); }
.select{
  appearance:none;
  background-image: linear-gradient(45deg, transparent 50%, #9ca3af 50%), linear-gradient(135deg, #9ca3af 50%, transparent 50%);
  background-position: calc(100% - 14px) calc(1em + 2px), calc(100% - 9px) calc(1em + 2px);
  background-size: 5px 5px;
  background-repeat:no-repeat;
}

/* Actions + Button */
.actions{ display:flex; flex-direction:column; align-items:stretch; gap:8px; margin-top:16px; }

.btn-primary{
  background: var(--accent) !important;
  color:#fff !important;
  border:1px solid var(--accent) !important;
  padding:12px 18px !important;
  border-radius:10px !important;
  font-weight:800 !important;
  cursor:pointer !important;
  display:flex !important; align-items:center !important; justify-content:center !important;
  gap:8px !important; font-size:12px !important; width:100% !important;
}
.btn-primary:not(:disabled):hover{ filter:brightness(1.06); transform:translateY(-1px); transition:.15s ease; }
.btn-primary:disabled{
  background:#d1d5db !important; border-color:#d1d5db !important; color:#6b7280 !important;
  cursor:not-allowed !important; opacity:1 !important;
}
.btn-primary.is-busy{ opacity:.7 !important; }

.btn-hint{ font-size:10px; color:var(--muted); text-align:center; }

/* Errors */
.err{ color:#dc2626; font-size:12px; margin-top:6px; }

/* ===== Breakpoints khớp với Profile.vue ===== */
@media (min-width:641px){
  .container{ padding:20px 14px 36px; }
  .tabs{ gap:6px; padding:6px; }
  .tab{ padding:10px 10px; font-size:12px; }
  .card{ padding:14px; }
  .card-title{ font-size:15px; }
}

@media (min-width:841px){
  .container{ padding:24px 16px 40px; }
  .tabs{ width:max-content; }
  .tab{ padding:10px 14px; font-size:13px; }
  .card{ padding:16px; }
  .card-title{ font-size:16px; }

  .row{ grid-template-columns:220px 1fr; gap:14px; align-items:center; }
  .label{ font-size:14px; }

  .actions{ align-items:flex-end; }
  .btn-primary{ width:auto !important; } /* nút thu gọn ở desktop */
  .btn-hint{ text-align:right; }
}
</style>
