<!-- src/pages/student/account/Profile.vue -->
<template>
  <div class="profile-page">
    <div class="container">
      <!-- Tabs -->
      <div class="tabs">
        <button class="tab active" type="button">CÁ NHÂN</button>
        <button class="tab" type="button" @click="goChangePwd">ĐỔI MẬT KHẨU</button>
        <button class="tab" type="button" @click="goParent">PHỤ HUYNH</button>
      </div>

      <!-- Card -->
      <div class="card">
        <div class="card-head">
          <h2 class="card-title">THÔNG TIN CÁ NHÂN</h2>
          <div class="last-updated">
            Lần cập nhật gần nhất: <b>{{ lastUpdated }}</b>
          </div>
        </div>

        <!-- Toast (thành công/thất bại khi lưu) -->
        <transition name="fade">
          <div v-if="toast.msg" :class="['toast', toast.type]">
            {{ toast.msg }}
          </div>
        </transition>

        <p v-if="profileError" class="err" role="alert">{{ profileError }}</p>

        <!-- FORM -->
        <form v-if="ready" class="form" @submit.prevent="saveProfile">
          <div class="row">
            <label class="label">Ảnh đại diện</label>
            <div class="field-inline">
              <!-- Avatar clickable -->
              <div class="avatar-wrapper" @click="openFile">
                <div class="avatar">
                  <img :src="avatarPreview || currentAvatar" alt="avatar" />
                  <div class="avatar-overlay">
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"
                      stroke-width="2" stroke="currentColor">
                      <path stroke-linecap="round" stroke-linejoin="round"
                        d="M6.827 6.175A2.31 2.31 0 015.186 7.23c-.38.054-.757.112-1.134.175C2.999 7.58 2.25 8.507 2.25 9.574V18a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9.574c0-1.067-.75-1.994-1.802-2.169a47.865 47.865 0 00-1.134-.175 2.31 2.31 0 01-1.64-1.055l-.822-1.316a2.192 2.192 0 00-1.736-1.039 48.774 48.774 0 00-5.232 0 2.192 2.192 0 00-1.736 1.039l-.821 1.316z" />
                      <path stroke-linecap="round" stroke-linejoin="round"
                        d="M16.5 12.75a4.5 4.5 0 11-9 0 4.5 4.5 0 019 0zM18.75 10.5h.008v.008h-.008V10.5z" />
                    </svg>
                  </div>
                </div>
              </div>
              <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onPickFile" />
              <small class="muted"><br />PNG/JPG ≤ 2MB</small>
            </div>
          </div>

          <div class="row" >
            <label  class="label">Tên đăng nhập</label>
            <div>
              <input
                v-model.trim="form.username"
                type="text"
                class="input locked-input"
                disabled
                tabindex="-1"
                aria-readonly="true"
              />
              <span class="helper muted">Tên đăng nhập do hệ thống cấp và không thể chỉnh sửa.</span>
            </div>
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
              <div class="field-inline dob-selects">
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
            <div class="field-inline gender-radio">
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
              <span class="helper muted">Email không bắt buộc, có thể để trống.</span>
            </div>
          </div>

          <div class="actions">
            <button type="submit" class="btn-primary" :class="{ 'is-busy': saving }"
              :disabled="saving || !isValidInfo || !isDirty">
              <span v-if="saving" class="spinner"></span>
              {{ saving ? 'ĐANG CẬP NHẬT...' : 'CẬP NHẬT' }}
            </button>
            <small v-if="!isValidInfo || !isDirty" class="btn-hint">
              {{ !isValidInfo ? 'Vui lòng điền đầy đủ thông tin bắt buộc' : 'Chưa có thay đổi nào' }}
            </small>
          </div>
        </form>

        <div v-else class="muted" style="padding: 12px 0">Đang tải thông tin…</div>
      </div>
    </div>
  </div>

  <!-- ===== Modal thông báo dung lượng ảnh ===== -->
  <transition name="modal-fade">
    <div
      v-if="limitModal.open"
      class="modal-backdrop"
      role="dialog"
      aria-modal="true"
      aria-labelledby="limit-title"
      @click.self="closeLimitModal"
    >
      <div class="modal-card" ref="limitCard" tabindex="-1">
        <div class="modal-header">
          <svg xmlns="http://www.w3.org/2000/svg" class="icon-alert" fill="none" viewBox="0 0 24 24"
            stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round"
              d="M12 9v3m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
          </svg>
          <h3 id="limit-title">Không thể tải ảnh</h3>
        </div>
        <div class="modal-body">
          <p>{{ limitModal.message }}</p>
          <small class="muted">Vui lòng chọn tệp PNG/JPG ≤ 2MB.</small>
        </div>
        <div class="modal-actions">
          <button class="btn-primary" type="button" @click="closeLimitModal">ĐÃ HIỂU</button>
        </div>
      </div>
    </div>
  </transition>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store/auth.store'
import { authService, type UpdateProfileDto } from '@/services/auth.service'

const router = useRouter()
const auth = useAuthStore()
const ready = ref(false)
const profileLoading = ref(false)
const profileError = ref('')

const MAX_AVATAR_SIZE = 2 * 1024 * 1024 // 2MB
const OVER_LIMIT_MSG = 'File ảnh vượt quá dung lượng cho phép (2MB)'

function goChangePwd() { router.push({ name: 'student-change-password' }) }
function goParent() { router.push({ name: 'student-parent' }) }

const defaultAvatar = 'https://i.pravatar.cc/80?img=10'
const currentAvatar = computed(() => auth.user?.avatar || auth.user?.avatarUrl || defaultAvatar)

const fileInput = ref<HTMLInputElement | null>(null)
const avatarFile = ref<File | null>(null)
const avatarPreview = ref<string>('')

function openFile() { fileInput.value?.click() }

/** MODAL: thông báo giới hạn dung lượng */
const limitModal = reactive<{ open: boolean; message: string }>({ open: false, message: '' })
const limitCard = ref<HTMLElement | null>(null)

function showLimitModal(msg = OVER_LIMIT_MSG) {
  limitModal.message = msg
  limitModal.open = true
  // focus bẫy trong modal
  queueMicrotask(() => limitCard.value?.focus())
}
function closeLimitModal() {
  limitModal.open = false
}

function handleEsc(e: KeyboardEvent) {
  if (e.key === 'Escape' && limitModal.open) {
    e.stopPropagation()
    closeLimitModal()
  }
}
window.addEventListener('keydown', handleEsc)
onBeforeUnmount(() => window.removeEventListener('keydown', handleEsc))

function onPickFile(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  if (file.size > MAX_AVATAR_SIZE) {
    // Hiển thị HỘP THOẠI
    showLimitModal()
    // reset lựa chọn file
    input.value = ''
    avatarFile.value = null
    avatarPreview.value = ''
    return
  }

  avatarFile.value = file
  const reader = new FileReader()
  reader.onload = () => (avatarPreview.value = String(reader.result || ''))
  reader.readAsDataURL(file)
}

/** FORM DATA */
const form = reactive({
  username: '',
  fullname: '',
  phone: '',
  email: '',
  emailUpdates: false,
  gender: 'male',
})

const dob = reactive({ day: 1, month: 1, year: 2000 })
const days = Array.from({ length: 31 }, (_, i) => i + 1)
const months = Array.from({ length: 12 }, (_, i) => i + 1)
const years = Array.from({ length: 60 }, (_, i) => 1980 + i)

function parseDobString(raw?: string | null) {
  if (!raw) return null
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return null
  return { day: date.getDate(), month: date.getMonth() + 1, year: date.getFullYear() }
}

function applyProfileToForm(data: any) {
  form.username = data?.name || data?.username || form.username
  form.fullname = data?.displayName || data?.name || data?.username || form.fullname
  form.phone = data?.phone || form.phone
  form.email = data?.email || form.email
  form.gender =
    data?.gender && String(data.gender).toLowerCase().startsWith('f')
      ? 'female'
      : data?.gender && String(data.gender).toLowerCase().startsWith('m')
        ? 'male'
        : form.gender

  const parsedDob = parseDobString(data?.dob)
  if (parsedDob) {
    dob.day = parsedDob.day
    dob.month = parsedDob.month
    dob.year = parsedDob.year
  }
}

async function fetchProfile() {
  profileLoading.value = true
  profileError.value = ''
  try {
    const data = await authService.getProfile()
    applyProfileToForm(data)
    auth.user = { ...(auth.user as any), ...data }
    if (typeof auth.persist === 'function') auth.persist()
  } catch (error: any) {
    profileError.value =
      error?.response?.data?.detail || error?.message || 'Không thể tải thông tin cá nhân.'
  } finally {
    profileLoading.value = false
  }
}

const initialJSON = ref<string>('')

function snapshot() {
  initialJSON.value = JSON.stringify({ ...form, dob: { ...dob }, avatarPreview: avatarPreview.value })
}

onMounted(async () => {
  await auth.init?.()
  if (auth.user) applyProfileToForm(auth.user)
  await fetchProfile()
  snapshot()
  ready.value = true
})

/** VALIDATION */
const errors = reactive<{ fullname?: string; phone?: string; email?: string }>({})
const isEmail = (v: string) => /^\S+@\S+\.\S+$/.test(v)

watch(
  () => ({ ...form }),
  () => {
    if (!ready.value) return
    errors.fullname = form.fullname ? '' : 'Vui lòng nhập họ và tên.'
    errors.phone = form.phone ? '' : 'Vui lòng nhập số điện thoại.'
    errors.email = form.email && !isEmail(form.email) ? 'Email không hợp lệ.' : ''
  },
  { deep: true }
)

const isValidInfo = computed(() => !errors.fullname && !errors.phone && !errors.email)
const isDirty = computed(() => {
  const now = JSON.stringify({ ...form, dob: { ...dob }, avatarPreview: avatarPreview.value })
  return now !== initialJSON.value
})

/** SAVE */
const saving = ref(false)
const lastUpdated = ref('chưa có')
const toast = reactive<{ msg: string; type: 'success' | 'error' | '' }>({ msg: '', type: '' })
let toastTimer: any
function showToast(msg: string, type: 'success' | 'error') {
  toast.msg = msg
  toast.type = type
  clearTimeout(toastTimer)
  toastTimer = setTimeout(() => (toast.msg = ''), 2500)
}

async function saveProfile() {
  if (!isValidInfo.value) {
    showToast('Vui lòng kiểm tra lại các trường bắt buộc.', 'error')
    return
  }
  if (!isDirty.value) return

  saving.value = true
  try {
    const payload: UpdateProfileDto = {
      displayName: form.fullname || auth.user?.displayName || auth.user?.name,
      name: form.fullname || auth.user?.name,
      email: form.email || auth.user?.email,
      phone: form.phone,
      gender: form.gender,
      avatar: avatarPreview.value || auth.user?.avatar,
      avatarUrl: avatarPreview.value || auth.user?.avatarUrl || auth.user?.avatar,
      dob: `${dob.year}-${String(dob.month).padStart(2, '0')}-${String(dob.day).padStart(2, '0')}`,
      language: auth.user?.language,
    }
    await auth.updateProfile(payload as any)
    await fetchProfile() // đồng bộ lại với dữ liệu vừa lưu trên server
    lastUpdated.value = new Date().toLocaleString()
    snapshot()
    avatarFile.value = null
    avatarPreview.value = ''
    if (fileInput.value) fileInput.value.value = ''
    showToast('Cập nhật hồ sơ thành công!', 'success')
  } catch (e) {
    showToast('Cập nhật thất bại. Thử lại sau.', 'error')
  } finally {
    saving.value = false
  }
}
</script>

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
.profile-page { background: var(--bg); min-height: 100vh; color: var(--text); }
.container { max-width: 1000px; margin: 0 auto; padding: 16px 10px 32px; }

/* Tabs */
.tabs { display: flex; gap: 4px; background: #fff; border: 1px solid var(--line); border-radius: 10px; padding: 4px; width: 100%; }
.tab { flex: 1; padding: 8px 4px; border-radius: 8px; border: 1px solid transparent; background: #fff; cursor: pointer; font-weight: 700; white-space: nowrap; text-align: center; font-size: 10px; line-height: 1.3; }
.tab.active { color: var(--accent); border-color: var(--accent-tint-border); background: var(--accent-tint-bg); }

/* Card */
.card { background: var(--card); border: 1px solid var(--line); border-radius: 12px; margin-top: 10px; padding: 12px; }
.card-head { display: flex; justify-content: space-between; gap: 8px; flex-wrap: wrap; margin-bottom: 10px; }
.card-title { font-weight: 800; font-size: 14px; }
.last-updated { font-size: 10px; color: var(--muted); width: 100%; }

/* Toast */
.toast { position: fixed; right: 10px; bottom: 10px; padding: 8px 10px; border-radius: 10px; border: 1px solid; z-index: 40; font-size: 12px; }
.toast.success { background: #f0fdf4; color: #166534; border-color: #bbf7d0; }
.toast.error { background: #fef2f2; color: #991b1b; border-color: #fecaca; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* Form */
.form { margin-top: 4px; }
.row { display: grid; grid-template-columns: 1fr; gap: 4px; margin-bottom: 10px; }
.label { text-align: left; color: #111827; font-weight: 600; font-size: 12px; margin-bottom: 4px; }
.req { color: #ef4444; }

.input { width: 100%; padding: 9px 10px; border: 1px solid var(--line); border-radius: 10px; background: #fff; outline: none; font-size: 14px; }
.input:focus { border-color: var(--focus-border); box-shadow: 0 0 0 3px var(--focus-ring); }
.input:disabled,
.input.locked-input {
  background: #f3f4f6;
  color: var(--muted);
  cursor: not-allowed;
  box-shadow: none;
}
.select {
  appearance: none;
  background-image:
    linear-gradient(45deg, transparent 50%, #9ca3af 50%),
    linear-gradient(135deg, #9ca3af 50%, transparent 50%);
  background-position:
    calc(100% - 14px) calc(1em + 2px),
    calc(100% - 9px) calc(1em + 2px);
  background-size: 5px 5px;
  background-repeat: no-repeat;
}
.field-inline { display: flex; flex-direction: column; gap: 6px; align-items: stretch; }
.helper { display: block; margin-top: 4px; font-size: 10px; color: var(--muted); line-height: 1.4; }
.err { color: #dc2626; font-size: 10px; margin-top: 4px; line-height: 1.4; }

/* Avatar */
.avatar-wrapper { cursor: pointer; flex-shrink: 0; }
.avatar { width: 56px; height: 56px; border-radius: 50%; overflow: hidden; border: 2px solid var(--line); background: #fff; position: relative; transition: all 0.2s ease; }
.avatar:hover { border-color: var(--accent); }
.avatar img { width: 100%; height: 100%; object-fit: cover; }
.avatar-overlay { position: absolute; inset: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; opacity: 0; transition: opacity 0.2s ease; }
.avatar:hover .avatar-overlay { opacity: 1; }
.avatar-overlay svg { width: 20px; height: 20px; color: #fff; }
.hidden { display: none; }

.actions { display: flex; flex-direction: column; gap: 6px; margin-top: 12px; }
.btn-primary { background: var(--accent) !important; color: #fff !important; border: 1px solid var(--accent) !important; padding: 10px 14px !important; border-radius: 10px !important; font-weight: 800 !important; cursor: pointer !important; display: flex !important; align-items: center !important; justify-content: center !important; gap: 6px !important; font-size: 12px !important; width: 100% !important; }
.btn-primary:disabled { background: #d1d5db !important; border-color: #d1d5db !important; color: #6b7280 !important; cursor: not-allowed !important; }
.btn-primary.is-busy { opacity: .7 !important; cursor: progress !important; }
.btn-hint { font-size: 10px; color: var(--muted); text-align: center; line-height: 1.4; }

.spinner { width: 12px; height: 12px; border: 2px solid rgba(255,255,255,.6); border-top-color:#fff; border-radius: 50%; animation: spin .8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg);} }

.radio { display: inline-flex; align-items: center; gap: 6px; margin-right: 10px; font-size: 12px; }
.radio input { display: none; }
.radio span { width: 14px; height: 14px; border: 2px solid var(--focus-border); border-radius: 50%; display: inline-block; position: relative; }
.radio input:checked + span::after { content: ''; position: absolute; inset: 2px; background: var(--accent); border-radius: 50%; }

.gender-radio { flex-direction: row !important; }

.check { display: flex; align-items: center; gap: 6px; margin-top: 6px; font-size: 11px; }
.check input { display: none; }
.check span { width: 14px; height: 14px; border: 1px solid #cbd5e1; border-radius: 4px; position: relative; }
.check input:checked + span::after { content: ''; position: absolute; left: 3px; top: 0; width: 6px; height: 10px; border: 2px solid var(--accent); border-top: 0; border-left: 0; transform: rotate(45deg); }

.muted { color: var(--muted); }

.dob-selects { flex-direction: row !important; gap: 4px !important; }
.dob-selects .select { flex: 1; min-width: 0; font-size: 12px; padding: 8px 6px; }

/* ===== Modal styles ===== */
.modal-backdrop {
  position: fixed; inset: 0;
  background: rgba(15, 23, 42, 0.5);
  display: grid; place-items: center;
  padding: 16px; z-index: 50;
}
.modal-card {
  width: 100%; max-width: 420px;
  background: #fff; border: 1px solid var(--line);
  border-radius: 14px; padding: 14px;
  outline: none;
  box-shadow: 0 20px 50px rgba(0,0,0,.15);
}
.modal-header { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.icon-alert { width: 22px; height: 22px; color: #f59e0b; }
.modal-header h3 { font-weight: 800; font-size: 15px; margin: 0; }
.modal-body { color: var(--text); font-size: 13px; line-height: 1.5; margin: 8px 0 12px; }
.modal-actions { display: flex; justify-content: flex-end; gap: 8px; }

.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity .15s ease; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

/* Breakpoints: đồng bộ ChangePassword */
@media (min-width: 641px) {
  .container { padding: 20px 14px 36px; }
  .tabs { gap: 6px; padding: 6px; }
  .tab { padding: 10px 10px; font-size: 12px; }
  .card { padding: 14px; }
  .card-title { font-size: 15px; }
  .label { font-size: 13px; }
  .avatar { width: 64px; height: 64px; }
  .avatar-overlay svg { width: 24px; height: 24px; }
}

@media (min-width: 841px) {
  .container { padding: 24px 16px 40px; }
  .tab { padding: 10px 14px; font-size: 13px; }
  .card { padding: 16px; }
  .card-title { font-size: 16px; }
  .row { grid-template-columns: 220px 1fr; gap: 14px; }
  .label { font-size: 14px; padding-top: 10px; }
  .avatar { width: 72px; height: 72px; }
  .avatar-overlay svg { width: 28px; height: 28px; }
  .field-inline { flex-direction: row; flex-wrap: wrap; }
  .actions { align-items: flex-end; }
  .btn-primary { width: auto !important; }
  .btn-hint { text-align: right; }
  .last-updated { width: auto; }
}
</style>
