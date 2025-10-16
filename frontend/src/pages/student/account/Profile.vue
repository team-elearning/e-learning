<!-- src/pages/student/account/Profile.vue -->
<template>
  <div class="profile-page">
    <div class="container">
      <!-- Tabs -->
      <div class="tabs">
        <button class="tab active" type="button">THÔNG TIN CÁ NHÂN</button>
        <button class="tab" type="button" @click="goChangePwd">ĐỔI MẬT KHẨU</button>
        <button class="tab" type="button" @click="goParent">THÔNG TIN PHỤ HUYNH</button>
      </div>

      <!-- Card -->
      <div class="card">
        <div class="card-head">
          <h2 class="card-title">THÔNG TIN CÁ NHÂN</h2>
          <div class="last-updated">
            Lần cập nhật gần nhất: <b>{{ lastUpdated }}</b>
          </div>
        </div>

        <!-- Toast -->
        <transition name="fade">
          <div v-if="toast.msg" :class="['toast', toast.type]">
            {{ toast.msg }}
          </div>
        </transition>

        <!-- FORM -->
        <form v-if="ready" class="form" @submit.prevent="saveProfile">
          <div class="row">
            <label class="label">Ảnh đại diện</label>
            <div class="field-inline">
              <div class="avatar">
                <img :src="avatarPreview || currentAvatar" alt="avatar" />
              </div>
              <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onPickFile" />
              <button class="btn-light" type="button" @click="openFile">Upload</button>
              <small class="muted">PNG/JPG ≤ 2MB (có thể để trống)</small>
            </div>
          </div>

          <div class="row">
            <label class="label">Tên đăng nhập</label>
            <input v-model.trim="form.username" type="text" class="input" />
            <span class="helper muted">Có thể để trống nếu hệ thống tự sinh.</span>
          </div>

          <div class="row">
            <label class="label">Họ và tên <span class="req">*</span></label>
            <div>
              <input v-model.trim="form.fullname" type="text" class="input" placeholder="Họ và tên" />
              <p v-if="errors.fullname" class="err">{{ errors.fullname }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Số điện thoại <span class="req">*</span></label>
            <div>
              <input v-model.trim="form.phone" type="tel" class="input" />
              <p v-if="errors.phone" class="err">{{ errors.phone }}</p>
            </div>
          </div>

          <div class="row">
            <label class="label">Ngày sinh</label>
            <div>
              <div class="field-inline">
                <select v-model.number="dob.day" class="input select">
                  <option v-for="d in days" :key="d" :value="d">Ngày {{ d }}</option>
                </select>
                <select v-model.number="dob.month" class="input select">
                  <option v-for="m in months" :key="m" :value="m">Tháng {{ m }}</option>
                </select>
                <select v-model.number="dob.year" class="input select">
                  <option v-for="y in years" :key="y" :value="y">Năm {{ y }}</option>
                </select>
              </div>
              <span class="helper muted">Có thể để trống.</span>
            </div>
          </div>

          <div class="row">
            <label class="label">Giới tính</label>
            <div class="field-inline">
              <label class="radio">
                <input type="radio" name="gender" value="male" v-model="form.gender" />
                <span></span> Nam
              </label>
              <label class="radio">
                <input type="radio" name="gender" value="female" v-model="form.gender" />
                <span></span> Nữ
              </label>
            </div>
          </div>

          <div class="row">
            <label class="label">Email</label>
            <div>
              <input v-model.trim="form.email" type="email" class="input" placeholder="you@example.com" />
              <p v-if="errors.email" class="err">{{ errors.email }}</p>
              <label class="check">
                <input type="checkbox" v-model="form.emailUpdates" />
                <span></span> Nhận thông báo qua email
              </label>
              <span class="helper muted">Email không bắt buộc, có thể để trống.</span>
            </div>
          </div>

          <div class="row">
            <label class="label">Địa chỉ</label>
            <div>
              <textarea v-model.trim="form.address" class="input" rows="3" placeholder="Có thể để trống"></textarea>
            </div>
          </div>

          <div class="row">
            <label class="label">Tỉnh/Thành phố</label>
            <select v-model="form.city" class="input select">
              <option value="">Chọn</option>
              <option>Hà Nội</option>
              <option>TP. Hồ Chí Minh</option>
              <option>Đà Nẵng</option>
              <option>N/A</option>
            </select>
          </div>

          <div class="row">
            <label class="label">Quận/Huyện</label>
            <select v-model="form.district" class="input select">
              <option value="">Chọn (có thể để trống)</option>
              <option>Quận 1</option>
              <option>Quận 2</option>
              <option>Khác</option>
            </select>
          </div>

          <div class="row">
            <label class="label">Phường/Xã</label>
            <select v-model="form.ward" class="input select">
              <option value="">Chọn (có thể để trống)</option>
              <option>Phường A</option>
              <option>Phường B</option>
              <option>Khác</option>
            </select>
          </div>

          <div class="actions">
            <button
              type="submit"
              class="btn-primary"
              :class="{ 'is-busy': saving }"
              :disabled="saving || !isValidInfo || !isDirty"
            >
              <span v-if="saving" class="spinner"></span>
              {{ saving ? 'ĐANG CẬP NHẬT...' : 'CẬP NHẬT' }}
            </button>
            <small v-if="!isValidInfo || !isDirty" class="btn-hint">
              {{ !isValidInfo ? 'Vui lòng điền đầy đủ thông tin bắt buộc' : 'Chưa có thay đổi nào' }}
            </small>
          </div>
        </form>

        <!-- Skeleton khi chưa sẵn sàng -->
        <div v-else class="muted" style="padding:12px 0">Đang tải thông tin…</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth.store'
import type { UpdateProfileDto } from '@/services/auth.service'

const router = useRouter()
const auth = useAuthStore()
const ready = ref(false)

// Tabs
function goChangePwd(){ router.push({ name: 'student-change-password' }) }
function goParent(){ router.push({ name: 'student-parent' }) }

/* Avatar */
const defaultAvatar = 'https://i.pravatar.cc/80?img=10'
const currentAvatar = computed(() => auth.avatar || defaultAvatar)

const fileInput = ref<HTMLInputElement | null>(null)
const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string>('')

function openFile(){ fileInput.value?.click() }
function onPickFile(e: Event) {
  const file = (e.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (file.size > 2 * 1024 * 1024) {
    alert('Ảnh quá 2MB!')
    ;(e.target as HTMLInputElement).value = ''
    return
  }
  avatarFile.value = file
  const reader = new FileReader()
  reader.onload = () => (avatarPreview.value = String(reader.result || ''))
  reader.readAsDataURL(file)
}

/* Form data */
const form = reactive({
  username: '',
  fullname: '',
  phone: '',
  email: '',
  emailUpdates: false,
  gender: 'male',
  address: '',
  city: '',
  district: '',
  ward: ''
})

// DOB demo
const dob = reactive({ day: 1, month: 1, year: 2000 })
const days = Array.from({ length: 31 }, (_, i) => i + 1)
const months = Array.from({ length: 12 }, (_, i) => i + 1)
const years = Array.from({ length: 60 }, (_, i) => 1980 + i)

/* Prefill + ready */
const initialJSON = ref<string>('')

function snapshot(){
  initialJSON.value = JSON.stringify({ ...form, avatarPreview: avatarPreview.value })
}

onMounted(() => {
  auth.init?.()
  if (auth.user) {
    form.username = auth.user.name || ''
    form.fullname = auth.user.name || ''
    form.phone = auth.user.phone || ''
    form.email = auth.user.email || ''
  }
  snapshot()
  ready.value = true
})

/* Validation (chỉ chạy khi ready) */
const errors = reactive<{ fullname?: string; phone?: string; email?: string }>({})
const isEmail = (v: string) => /^\S+@\S+\.\S+$/.test(v)

watch(() => ({ ...form }), () => {
  if (!ready.value) return
  errors.fullname = form.fullname ? '' : 'Vui lòng nhập họ và tên.'
  errors.phone = form.phone ? '' : 'Vui lòng nhập số điện thoại.'
  errors.email = form.email && !isEmail(form.email) ? 'Email không hợp lệ.' : ''
}, { deep: true, immediate: false })

const isValidInfo = computed(() => !errors.fullname && !errors.phone && !errors.email)

/* Dirty check */
const isDirty = computed(() => {
  const now = JSON.stringify({ ...form, avatarPreview: avatarPreview.value })
  return now !== initialJSON.value
})

/* Save */
const saving = ref(false)
const lastUpdated = ref('chưa có')
const toast = reactive<{ msg: string; type: 'success'|'error'|'' }>({ msg: '', type: '' })
let toastTimer: any
function showToast(msg: string, type: 'success'|'error') {
  toast.msg = msg; toast.type = type
  clearTimeout(toastTimer); toastTimer = setTimeout(() => (toast.msg = ''), 2500)
}

async function saveProfile() {
  if (!isValidInfo.value) { showToast('Vui lòng kiểm tra lại các trường bắt buộc.', 'error'); return }
  if (!isDirty.value) return

  saving.value = true
  try {
    const payload: UpdateProfileDto = {
      name: form.fullname,
      email: form.email || auth.user?.email,
      phone: form.phone,
      avatar: avatarPreview.value || auth.user?.avatar,
    }
    await auth.updateProfile(payload as any)
    lastUpdated.value = new Date().toLocaleString()
    snapshot()
    avatarFile.value = null
    avatarPreview.value = ''
    showToast('Cập nhật hồ sơ thành công!', 'success')
  } catch (e) {
    showToast('Cập nhật thất bại. Thử lại sau.', 'error')
  } finally {
    saving.value = false
  }
}
</script>

<!-- Theme -->
<style>
:root{
  --bg:#f6f7fb;
  --card:#fff;
  --text:#0f172a;
  --muted:#6b7280;
  --line:#e5e7eb;
  --accent:#16a34a;
  --accent-tint-bg:#ecfdf5;
  --accent-tint-border:#bbf7d0;
  --focus-border:#86efac;
  --focus-ring:rgba(22,163,74,.18);
}
</style>

<style scoped>
.profile-page{ background:var(--bg); min-height:100vh; color:var(--text); }
.container{ max-width:1000px; margin:0 auto; padding:24px 16px 40px; }
.tabs{ display:flex; gap:8px; background:#fff; border:1px solid var(--line); border-radius:10px; padding:6px; width:max-content; }
.tab{ padding:10px 14px; border-radius:8px; border:1px solid transparent; background:#fff; cursor:pointer; font-weight:700; }
.tab.active{ color:var(--accent); border-color:var(--accent-tint-border); background:var(--accent-tint-bg); }
.card{ background:var(--card); border:1px solid var(--line); border-radius:14px; margin-top:12px; padding:16px 16px 20px; }
.card-head{ display:flex; justify-content:space-between; align-items:center; gap:12px; }
.card-title{ font-weight:800; letter-spacing:.4px; }
.last-updated{ font-size:12px; color:var(--muted); }
.toast{ position:fixed; right:18px; bottom:18px; padding:10px 12px; border-radius:10px; border:1px solid; z-index:40;}
.toast.success{ background:#f0fdf4; color:#166534; border-color:#bbf7d0; }
.toast.error{ background:#fef2f2; color:#991b1b; border-color:#fecaca; }
.fade-enter-active,.fade-leave-active{ transition:opacity .2s; } .fade-enter-from,.fade-leave-to{ opacity:0; }
.form{ margin-top:6px; }
.row{ display:grid; grid-template-columns: 220px 1fr; gap:16px; align-items:center; margin-bottom:12px; }
.label{ text-align:left; color:#111827; font-weight:600; }
.req{ color:#ef4444; }
.input{ width:100%; padding:10px 12px; border:1px solid var(--line); border-radius:10px; background:#fff; outline:none; }
.input:focus{ border-color:var(--focus-border); box-shadow:0 0 0 3px var(--focus-ring); }
.select{ appearance:none; background-image: linear-gradient(45deg, transparent 50%, #9ca3af 50%), linear-gradient(135deg, #9ca3af 50%, transparent 50%); background-position: calc(100% - 18px) calc(1em + 2px), calc(100% - 13px) calc(1em + 2px); background-size: 5px 5px, 5px 5px; background-repeat:no-repeat; }
.field-inline{ display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
.helper{ display:block; margin-top:6px; font-size:12px; }
.err{ color:#dc2626; font-size:12px; margin-top:6px; }
.avatar{ width:72px; height:72px; border-radius:50%; overflow:hidden; border:1px solid var(--line); background:#fff; }
.avatar img{ width:100%; height:100%; object-fit:cover; }
.hidden{ display:none; }
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
  transition: all .2s ease !important;
}

/* Nút khi KHÔNG disabled - hover */
.btn-primary:not(:disabled):hover{ 
  filter: brightness(1.1) !important; 
  transform: translateY(-1px) !important;
}

/* Nút khi DISABLED - màu xám rõ ràng */
.btn-primary:disabled{
  background: #d1d5db !important;
  border-color: #d1d5db !important;
  color: #6b7280 !important;
  cursor: not-allowed !important;
  opacity: 1 !important;
}

/* Nút khi đang SAVING - giữ màu xanh + spinner */
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

.btn-light{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:8px 12px; cursor:pointer; font-weight:700; }
.spinner{ width:14px; height:14px; border:2px solid rgba(255,255,255,.6); border-top-color:#fff; border-radius:50%; animation:spin .8s linear infinite; }
@keyframes spin{ to{ transform:rotate(360deg); } }
.radio{ display:inline-flex; align-items:center; gap:8px; margin-right:16px; }
.radio input{ display:none; }
.radio span{ width:16px; height:16px; border:2px solid var(--focus-border); border-radius:50%; display:inline-block; position:relative; }
.radio input:checked + span::after{ content:''; position:absolute; inset:3px; background:var(--accent); border-radius:50%; }
.check{ display:flex; align-items:center; gap:8px; margin-top:8px; }
.check input{ display:none; }
.check span{ width:16px; height:16px; border:1px solid #cbd5e1; border-radius:4px; position:relative; }
.check input:checked + span::after{ content:''; position:absolute; left:3px; top:1px; width:8px; height:12px; border:2px solid var(--accent); border-top:0; border-left:0; transform:rotate(45deg); }
@media (max-width: 840px){
  .row{ grid-template-columns: 1fr; }
  .label{ margin-bottom:4px; }
}
</style>
