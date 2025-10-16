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
              <input v-model.trim="f.phone" class="input" placeholder="09xxxxxxxx" />
              <p v-if="errs.phone" class="err">{{ errs.phone }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Email</label>
            <div>
              <input v-model.trim="f.email" class="input" placeholder="parent@example.com" />
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
.row{ display:grid; grid-template-columns: 220px 1fr; gap:16px; align-items:center; margin-bottom:12px; }
.label{ text-align:left; color:#111827; font-weight:600; }
.req{ color:#ef4444; }
.input{ width:100%; padding:10px 12px; border:1px solid var(--line); border-radius:10px; background:#fff; outline:none; transition: all 0.2s ease; }
.input:focus{ border-color:var(--focus-border); box-shadow:0 0 0 3px var(--focus-ring); }
.select{ appearance:none; background-image: linear-gradient(45deg, transparent 50%, #9ca3af 50%), linear-gradient(135deg, #9ca3af 50%, transparent 50%); background-position: calc(100% - 18px) calc(1em + 2px), calc(100% - 13px) calc(1em + 2px); background-size: 5px 5px, 5px 5px; background-repeat:no-repeat; }

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

/* Errors */
.err{ color:#dc2626; font-size:12px; margin-top:6px; }

/* Responsive */
@media (max-width: 840px){
  .row{ grid-template-columns: 1fr; }
  .label{ margin-bottom:4px; }
}
</style>
