<template>
  <div class="space-y-4">
    <!-- Header -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex min-w-0 items-center gap-4">
          <img :src="detail.avatar || fallbackAvatar" class="h-16 w-16 rounded-full object-cover" />
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="truncate text-xl font-semibold text-gray-800">{{ detail.name || '—' }}</h2>
              <el-tag size="small" :type="roleTagType(detail.role)">{{
                roleLabel(detail.role)
              }}</el-tag>
              <el-tag size="small" :type="statusTagType(detail.status)">{{
                statusLabel(detail.status)
              }}</el-tag>
            </div>
            <div class="mt-1 text-sm text-gray-500">
              @{{ detail.username }} • {{ detail.email }}
              <span v-if="detail.emailVerified" class="ml-1 text-emerald-600">(đã xác minh)</span>
            </div>
            <div class="mt-1 text-xs text-gray-500">
              Lần đăng nhập cuối: <b>{{ fmtDate(detail.lastLoginAt) || '—' }}</b> • Tạo lúc:
              <b>{{ fmtDate(detail.createdAt) }}</b>
            </div>
          </div>
        </div>

        <div class="flex flex-wrap items-center gap-2">
          <el-button @click="openEdit">Sửa</el-button>
          <el-button type="warning" plain @click="resetPassword" :loading="act.resetPass"
            >Reset mật khẩu</el-button
          >
          <el-button
            v-if="detail.status !== 'locked'"
            type="warning"
            @click="lock"
            :loading="act.lock"
            >Khoá</el-button
          >
          <el-button v-else type="success" @click="unlock" :loading="act.unlock">Mở khoá</el-button>
          <el-button type="danger" plain @click="ban" :loading="act.ban">Ban</el-button>
          <el-button type="danger" @click="revokeAll" :loading="act.revokeAll"
            >Thu hồi mọi phiên</el-button
          >
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <el-tabs v-model="activeTab">
      <!-- Profile -->
      <el-tab-pane label="Hồ sơ" name="profile">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
          <el-form
            ref="profileRef"
            :model="form"
            :rules="profileRules"
            label-position="top"
            class="grid grid-cols-1 gap-4 md:grid-cols-2"
          >
            <el-form-item label="Họ và tên" prop="name"
              ><el-input v-model="form.name"
            /></el-form-item>
            <el-form-item label="Username" prop="username"
              ><el-input v-model="form.username"
            /></el-form-item>
            <el-form-item label="Email" prop="email"
              ><el-input v-model="form.email"
            /></el-form-item>
            <el-form-item label="Số điện thoại" prop="phone"
              ><el-input v-model="form.phone"
            /></el-form-item>

            <el-form-item label="Ngôn ngữ">
              <el-select v-model="form.language"
                ><el-option label="Tiếng Việt" value="vi" /><el-option label="English" value="en"
              /></el-select>
            </el-form-item>
            <el-form-item label="Múi giờ"
              ><el-input v-model="form.timezone" placeholder="Asia/Bangkok"
            /></el-form-item>

            <el-form-item label="Bio" class="md:col-span-2">
              <el-input v-model="form.bio" type="textarea" :rows="3" />
            </el-form-item>

            <div class="md:col-span-2">
              <el-button type="primary" :loading="savingProfile" @click="saveProfile"
                >Lưu thay đổi</el-button
              >
            </div>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- Roles & permissions -->
      <el-tab-pane label="Vai trò & quyền" name="roles">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5 space-y-4">
          <div class="flex items-center gap-3">
            <div class="text-sm text-gray-600">Vai trò hiện tại:</div>
            <el-tag :type="roleTagType(detail.role)" round>{{ roleLabel(detail.role) }}</el-tag>
          </div>
          <div class="max-w-sm">
            <el-select v-model="roleToChange" placeholder="Chọn vai trò mới">
              <el-option label="Admin" value="admin" />
              <el-option label="Giáo viên" value="teacher" />
              <el-option label="Học sinh" value="student" />
            </el-select>
            <el-button
              class="ml-2"
              type="primary"
              :disabled="!roleToChange || roleToChange === detail.role"
              @click="changeRole"
              :loading="act.changeRole"
              >Đổi vai trò</el-button
            >
          </div>
          <div class="text-xs text-gray-500">* RBAC chi tiết có thể bổ sung sau.</div>
        </div>
      </el-tab-pane>

      <!-- Security -->
      <el-tab-pane label="Bảo mật" name="security">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5 space-y-3">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div class="rounded border p-3">
              <div class="text-sm text-gray-500">MFA / 2FA</div>
              <div class="mt-1 font-medium">{{ detail.mfaEnabled ? 'Đã bật' : 'Chưa bật' }}</div>
            </div>
            <div class="rounded border p-3">
              <div class="text-sm text-gray-500">Lần đổi mật khẩu gần nhất</div>
              <div class="mt-1 font-medium">{{ fmtDate(detail.passwordUpdatedAt) || '—' }}</div>
            </div>
            <div class="rounded border p-3">
              <div class="text-sm text-gray-500">Lượt nhập sai gần đây</div>
              <div class="mt-1 font-medium">{{ detail.failedAttempts ?? 0 }}</div>
            </div>
          </div>
          <div class="flex flex-wrap gap-2">
            <el-button type="warning" plain @click="resetPassword" :loading="act.resetPass"
              >Reset mật khẩu</el-button
            >
            <el-button @click="forcePasswordChange">Bắt đổi mật khẩu</el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- Sessions -->
      <el-tab-pane label="Phiên đăng nhập" name="sessions">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
          <div class="mb-3 flex items-center justify-between">
            <div class="text-sm text-gray-600">Tổng: {{ sessions.length }}</div>
            <el-button type="danger" @click="revokeAll" :loading="act.revokeAll"
              >Thu hồi tất cả</el-button
            >
          </div>
          <el-table :data="sessions" v-loading="loading.sessions" height="420">
            <el-table-column prop="device" label="Thiết bị" min-width="160" />
            <el-table-column prop="ip" label="IP" width="140" />
            <el-table-column prop="location" label="Vị trí" width="160" />
            <el-table-column prop="createdAt" label="Tạo lúc" min-width="170">
              <template #default="{ row }">{{ fmtDate(row.createdAt) }}</template>
            </el-table-column>
            <el-table-column prop="lastActiveAt" label="Hoạt động cuối" min-width="170">
              <template #default="{ row }">{{ fmtDate(row.lastActiveAt) }}</template>
            </el-table-column>
            <el-table-column fixed="right" width="140">
              <template #default="{ row }">
                <el-button
                  size="small"
                  type="danger"
                  plain
                  @click="revoke(row.sessionId)"
                  :loading="act.revoke"
                  >Thu hồi</el-button
                >
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>

      <!-- Login history -->
      <el-tab-pane label="Lịch sử đăng nhập" name="logins">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5 space-y-3">
          <div class="flex flex-wrap items-center gap-2">
            <el-date-picker
              v-model="loginRange"
              type="daterange"
              range-separator="–"
              start-placeholder="Từ"
              end-placeholder="Đến"
              value-format="YYYY-MM-DD"
            />
            <el-select v-model="loginResult" clearable placeholder="Kết quả">
              <el-option label="Thành công" value="success" />
              <el-option label="Thất bại" value="fail" />
            </el-select>
            <el-button @click="fetchLogins" :loading="loading.logins">Lọc</el-button>
          </div>
          <el-table :data="logins.items" v-loading="loading.logins" height="420">
            <el-table-column prop="time" label="Thời điểm" min-width="170">
              <template #default="{ row }">{{ fmtDate(row.time) }}</template>
            </el-table-column>
            <el-table-column prop="result" label="KQ" width="110">
              <template #default="{ row }">
                <el-tag :type="row.result === 'success' ? 'success' : 'danger'" size="small">{{
                  row.result
                }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="ip" label="IP" width="140" />
            <el-table-column prop="device" label="Thiết bị" min-width="160" />
            <el-table-column prop="reason" label="Lý do" min-width="160" show-overflow-tooltip />
          </el-table>
          <div class="flex justify-end">
            <el-pagination
              background
              layout="total, prev, pager, next"
              :total="logins.total"
              :current-page="loginPage"
              :page-size="loginPageSize"
              @current-change="
                (p: number) => {
                  loginPage = p
                  fetchLogins()
                }
              "
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- Activity -->
      <el-tab-pane label="Hoạt động" name="activity">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
          <el-table :data="activities.items" v-loading="loading.activities" height="420">
            <el-table-column prop="time" label="Thời điểm" min-width="170">
              <template #default="{ row }">{{ fmtDate(row.time) }}</template>
            </el-table-column>
            <el-table-column prop="action" label="Hành động" min-width="180" />
            <el-table-column prop="entity" label="Đối tượng" min-width="160" />
            <el-table-column prop="status" label="Trạng thái" width="110">
              <template #default="{ row }">
                <el-tag :type="row.status === 'ok' ? 'success' : 'danger'" size="small">{{
                  row.status
                }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="meta" label="Meta" min-width="220" show-overflow-tooltip />
          </el-table>
          <div class="mt-3 flex justify-end">
            <el-pagination
              background
              layout="total, prev, pager, next"
              :total="activities.total"
              :current-page="activityPage"
              :page-size="activityPageSize"
              @current-change="
                (p: number) => {
                  activityPage = p
                  fetchActivities()
                }
              "
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- Payments -->
      <el-tab-pane label="Giao dịch" name="payments">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
          <el-table :data="transactions.items" v-loading="loading.transactions" height="420">
            <el-table-column prop="id" label="Mã" width="140" />
            <el-table-column prop="courseTitle" label="Khóa học" min-width="200" />
            <el-table-column prop="amount" label="Số tiền" width="120" align="right">
              <template #default="{ row }">{{ currency(row.amount) }}</template>
            </el-table-column>
            <el-table-column prop="gateway" label="Cổng" width="100" />
            <el-table-column prop="status" label="TT" width="120" />
            <el-table-column prop="time" label="Thời gian" min-width="170">
              <template #default="{ row }">{{ fmtDate(row.time) }}</template>
            </el-table-column>
            <el-table-column fixed="right" width="120">
              <template #default="{ row }">
                <el-button size="small" @click="gotoTx(row.id)">Xem</el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="mt-3 flex justify-end">
            <el-pagination
              background
              layout="total, prev, pager, next"
              :total="transactions.total"
              :current-page="txPage"
              :page-size="txPageSize"
              @current-change="
                (p: number) => {
                  txPage = p
                  fetchTransactions()
                }
              "
            />
          </div>
        </div>
      </el-tab-pane>

      <!-- Notes -->
      <el-tab-pane label="Ghi chú" name="notes">
        <div class="rounded-lg bg-white p-4 ring-1 ring-black/5 space-y-4">
          <div class="flex items-start gap-2">
            <el-input
              v-model="newNote"
              type="textarea"
              :rows="2"
              placeholder="Thêm ghi chú nội bộ…"
            />
            <el-button
              type="primary"
              :disabled="!newNote.trim()"
              @click="addNote"
              :loading="act.addNote"
              >Thêm</el-button
            >
          </div>
          <div v-if="notes.length === 0" class="text-sm text-gray-500">Chưa có ghi chú.</div>
          <ul v-else class="space-y-3">
            <li v-for="n in notes" :key="n.id" class="rounded border p-3">
              <div class="flex items-center justify-between">
                <div class="font-medium text-gray-800">{{ n.author || 'Admin' }}</div>
                <div class="text-xs text-gray-500">{{ fmtDate(n.time) }}</div>
              </div>
              <p class="mt-1 text-sm text-gray-700 whitespace-pre-line">{{ n.note }}</p>
            </li>
          </ul>
        </div>
      </el-tab-pane>
    </el-tabs>

    <!-- Edit dialog -->
    <el-dialog v-model="editDialog" title="Sửa hồ sơ" width="520px">
      <el-form :model="form" :rules="profileRules" ref="editRef" label-position="top">
        <el-form-item label="Họ và tên" prop="name"><el-input v-model="form.name" /></el-form-item>
        <el-form-item label="Username" prop="username"
          ><el-input v-model="form.username"
        /></el-form-item>
        <el-form-item label="Email" prop="email"><el-input v-model="form.email" /></el-form-item>
        <el-form-item label="Số điện thoại" prop="phone"
          ><el-input v-model="form.phone"
        /></el-form-item>
        <!-- FIX: dùng computed hai chiều, không gán vào form.address?.city -->
        <el-form-item label="Thành phố">
          <el-input v-model="formAddressCity" placeholder="Thành phố" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">Huỷ</el-button>
        <el-button type="primary" :loading="savingProfile" @click="saveProfile">Lưu</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  userService,
  type ID,
  type Role,
  type UserStatus,
  type UserDetail,
  type SessionRow,
  type LoginEvent,
  type ActivityLog,
  type Transaction,
  type NoteItem,
} from '@/services/user.service'

const route = useRoute()
const router = useRouter()
const id = computed<ID>(() => route.params.id as any)

const activeTab = ref<
  'profile' | 'roles' | 'security' | 'sessions' | 'logins' | 'activity' | 'payments' | 'notes'
>('profile')
const fallbackAvatar = 'https://i.pravatar.cc/160?img=5'

// ===== state =====
const detail = reactive<UserDetail>({
  id: id.value,
  name: '',
  username: '',
  email: '',
  emailVerified: false,
  role: 'student',
  status: 'active',
  createdAt: new Date().toISOString(),
  updatedAt: new Date().toISOString(),
})
const loading = reactive({
  main: false,
  sessions: false,
  logins: false,
  activities: false,
  transactions: false,
})
const act = reactive({
  resetPass: false,
  lock: false,
  unlock: false,
  ban: false,
  revoke: false,
  revokeAll: false,
  changeRole: false,
  addNote: false,
})
const sessions = ref<SessionRow[]>([])
const loginRange = ref<[string, string] | null>(null)
const loginResult = ref<'success' | 'fail' | ''>('')
const logins = reactive<{ items: LoginEvent[]; total: number }>({ items: [], total: 0 })
const loginPage = ref(1)
const loginPageSize = 20
const activities = reactive<{ items: ActivityLog[]; total: number }>({ items: [], total: 0 })
const activityPage = ref(1)
const activityPageSize = 20
const transactions = reactive<{ items: Transaction[]; total: number }>({ items: [], total: 0 })
const txPage = ref(1)
const txPageSize = 20
const notes = ref<NoteItem[]>([])
const newNote = ref('')

// profile form
const profileRef = ref<FormInstance>()
const editRef = ref<FormInstance>()
const form = reactive<any>({})
const profileRules = {
  name: [{ required: true, message: 'Nhập họ tên', trigger: 'blur' }],
  username: [{ required: true, message: 'Nhập username', trigger: 'blur' }],
  email: [{ required: true, type: 'email', message: 'Email không hợp lệ', trigger: 'blur' }],
}
const savingProfile = ref(false)
const editDialog = ref(false)

// FIX: computed 2 chiều cho city (tránh gán vào optional chain)
const formAddressCity = computed<string>({
  get: () => form.address?.city ?? '',
  set: (v: string) => {
    form.address = { ...(form.address || {}), city: v }
  },
})

// ===== helpers =====
const fmtDate = (iso?: string) => (iso ? new Date(iso).toLocaleString('vi-VN') : '')
const currency = (v: number) =>
  new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(v)
const roleLabel = (r?: Role) =>
  r === 'admin' ? 'Admin' : r === 'teacher' ? 'Giáo viên' : 'Học sinh'
const statusLabel = (s?: UserStatus) =>
  s === 'active'
    ? 'Hoạt động'
    : s === 'locked'
      ? 'Tạm khoá'
      : s === 'banned'
        ? 'Cấm vĩnh viễn'
        : 'Chờ duyệt'
const roleTagType = (r?: Role) =>
  r === 'admin' ? 'danger' : r === 'teacher' ? 'warning' : 'success'
const statusTagType = (s?: UserStatus) =>
  s === 'active' ? 'success' : s === 'locked' ? 'warning' : s === 'banned' ? 'danger' : 'info'

// ===== load =====
async function load() {
  loading.main = true
  try {
    const d = await userService.detail(id.value)
    Object.assign(detail, d)
    Object.assign(form, JSON.parse(JSON.stringify(d))) // clone nông để form độc lập
    // preload
    fetchSessions()
    fetchLogins()
    fetchActivities()
    fetchTransactions()
    fetchNotes()
  } catch {
    ElMessage.error('Không tải được người dùng')
  } finally {
    loading.main = false
  }
}

async function fetchSessions() {
  loading.sessions = true
  try {
    sessions.value = await userService.sessions(id.value)
  } finally {
    loading.sessions = false
  }
}
async function fetchLogins() {
  loading.logins = true
  try {
    const res = await userService.loginHistory(id.value, {
      page: loginPage.value,
      pageSize: loginPageSize,
      result: loginResult.value || undefined,
      from: loginRange.value?.[0],
      to: loginRange.value?.[1],
    })
    Object.assign(logins, res)
  } finally {
    loading.logins = false
  }
}
async function fetchActivities() {
  loading.activities = true
  try {
    const res = await userService.activity(id.value, {
      page: activityPage.value,
      pageSize: activityPageSize,
    })
    Object.assign(activities, res)
  } finally {
    loading.activities = false
  }
}
async function fetchTransactions() {
  loading.transactions = true
  try {
    const res = await userService.transactionsByUser(id.value, {
      page: txPage.value,
      pageSize: txPageSize,
    })
    Object.assign(transactions, res)
  } finally {
    loading.transactions = false
  }
}
async function fetchNotes() {
  notes.value = await userService.listNotes(id.value)
}

// ===== actions =====
async function saveProfile() {
  const ok = await (profileRef.value || editRef.value)?.validate().catch(() => false)
  if (!ok) return
  savingProfile.value = true
  try {
    await userService.update(detail.id, {
      name: form.name,
      username: form.username,
      email: form.email,
      phone: form.phone,
      language: form.language,
      timezone: form.timezone,
      bio: form.bio,
      address: form.address,
    })
    ElMessage.success('Đã lưu hồ sơ')
    Object.assign(detail, form)
    editDialog.value = false
  } catch {
    ElMessage.error('Lưu thất bại')
  } finally {
    savingProfile.value = false
  }
}
function openEdit() {
  Object.assign(form, JSON.parse(JSON.stringify(detail)))
  editDialog.value = true
}

async function resetPassword() {
  await ElMessageBox.confirm(`Reset mật khẩu cho “${detail.name}”?`, 'Xác nhận', {
    type: 'warning',
  })
  act.resetPass = true
  try {
    await userService.resetPassword(detail.id)
    ElMessage.success('Đã gửi hướng dẫn reset')
  } finally {
    act.resetPass = false
  }
}
async function lock() {
  await ElMessageBox.confirm(`Khoá tài khoản “${detail.name}”?`, 'Xác nhận', { type: 'warning' })
  act.lock = true
  try {
    await userService.lock(detail.id)
    detail.status = 'locked'
    ElMessage.success('Đã khoá')
  } finally {
    act.lock = false
  }
}
async function unlock() {
  await ElMessageBox.confirm(`Mở khoá tài khoản “${detail.name}”?`, 'Xác nhận')
  act.unlock = true
  try {
    await userService.unlock(detail.id)
    detail.status = 'active'
    ElMessage.success('Đã mở khoá')
  } finally {
    act.unlock = false
  }
}
async function ban() {
  await ElMessageBox.confirm(`Cấm vĩnh viễn “${detail.name}”?`, 'Cảnh báo', { type: 'error' })
  act.ban = true
  try {
    await userService.ban(detail.id)
    detail.status = 'banned'
    ElMessage.success('Đã ban')
  } finally {
    act.ban = false
  }
}
async function revoke(sessionId: string) {
  act.revoke = true
  try {
    await userService.revokeSession(detail.id, sessionId)
    ElMessage.success('Đã thu hồi')
    fetchSessions()
  } finally {
    act.revoke = false
  }
}
async function revokeAll() {
  await ElMessageBox.confirm('Thu hồi tất cả phiên đang hoạt động?', 'Xác nhận', {
    type: 'warning',
  })
  act.revokeAll = true
  try {
    await userService.revokeAll(detail.id)
    ElMessage.success('Đã thu hồi')
    fetchSessions()
  } finally {
    act.revokeAll = false
  }
}

const roleToChange = ref<Role | ''>('')
async function changeRole() {
  if (!roleToChange.value || roleToChange.value === detail.role) return
  await ElMessageBox.confirm(`Đổi vai trò thành “${roleLabel(roleToChange.value)}”?`, 'Xác nhận')
  act.changeRole = true
  try {
    await userService.changeRole(detail.id, roleToChange.value as Role)
    detail.role = roleToChange.value as Role
    ElMessage.success('Đã đổi vai trò')
  } finally {
    act.changeRole = false
  }
}

function forcePasswordChange() {
  // placeholder – nếu backend hỗ trợ, gọi API riêng
  ElMessage.success('Đã bật yêu cầu đổi mật khẩu cho lần đăng nhập tới (mock)')
}
function gotoTx(txId: string) {
  router.push(`/admin/transactions/${txId}`)
}

onMounted(load)
watch(
  () => route.params.id,
  () => load(),
)
async function addNote() {
  if (!newNote.value.trim()) return
  act.addNote = true
  try {
    await userService.addNote(detail.id, newNote.value)
    ElMessage.success('Đã thêm ghi chú')
    newNote.value = ''
    fetchNotes()
  } catch {
    ElMessage.error('Thêm ghi chú thất bại')
  } finally {
    act.addNote = false
  }
}
</script>
