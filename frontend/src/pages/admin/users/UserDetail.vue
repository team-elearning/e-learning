<template>
  <div class="">
    <!-- Header -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <div class="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div class="flex min-w-0 items-center gap-4">
          <img :src="detail.avatar || fallbackAvatar" class="h-16 w-16 rounded-full object-cover" />
          <div class="min-w-0">
            <div class="flex flex-wrap items-center gap-2">
              <h2 class="truncate text-xl font-semibold text-gray-800">
                {{ detail.name || detail.username || '—' }}
              </h2>
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

          <!-- Change Password -->
          <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
            <h3 class="text-lg font-semibold text-gray-800">Đổi mật khẩu</h3>
            <p class="text-sm text-gray-500">Đặt mật khẩu mới cho người dùng này.</p>
            <div class="mt-4">
              <el-button type="warning" @click="openChangePasswordDialog"> Đổi mật khẩu </el-button>
            </div>
          </div>

          <!-- Delete Account -->
          <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
            <h3 class="text-lg font-semibold text-gray-800">Xóa tài khoản</h3>
            <p class="text-sm text-gray-500">
              Xóa tài khoản này vĩnh viễn. Hành động này không thể hoàn tác.
            </p>
            <div class="mt-4">
              <el-button type="danger" :loading="deletingAccount" @click="deleteAccount">
                Xóa tài khoản
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Profile -->
    <div class="rounded-lg bg-white p-4 ring-1 ring-black/5">
      <el-form
        ref="profileRef"
        :model="form"
        :rules="profileRules"
        label-position="top"
        class="grid grid-cols-1 gap-4 md:grid-cols-2"
      >
        <el-form-item label="Họ và tên" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="Username" prop="username">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="Email" prop="email">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="Số điện thoại" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <div class="md:col-span-2">
          <el-button type="primary" :loading="savingProfile" @click="saveProfile">
            Lưu thay đổi
          </el-button>
        </div>
      </el-form>
    </div>

    <!-- Change Password Dialog -->
    <el-dialog
      title="Đổi mật khẩu"
      v-model="changePasswordDialogVisible"
      width="400px"
      @close="resetChangePasswordForm"
    >
      <el-form :model="changePasswordForm" :rules="changePasswordRules" ref="changePasswordRef">
        <el-form-item label="Mật khẩu mới" prop="newPassword">
          <el-input v-model="changePasswordForm.newPassword" type="password" />
        </el-form-item>
      </el-form>
      <div slot="footer" class="dialog-footer">
        <el-button @click="changePasswordDialogVisible = false">Hủy</el-button>
        <el-button type="primary" :loading="changingPassword" @click="changePassword">
          Xác nhận
        </el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance } from 'element-plus'
import {
  userService,
  type ID,
  type Role,
  type UserStatus,
  type UserDetail,
} from '@/services/user.service'

const route = useRoute()
const id = computed<ID>(() => route.params.id as any)
const fallbackAvatar = 'https://i.pravatar.cc/160?img=5'

// State
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
const form = reactive<any>({})
const profileRef = ref<FormInstance>()
const savingProfile = ref(false)
const deletingAccount = ref(false)

// Change Password State
const changePasswordDialogVisible = ref(false)
const changePasswordForm = reactive({ newPassword: '' })
const changePasswordRef = ref<FormInstance>()
const changingPassword = ref(false)

// Rules
const profileRules = {
  name: [],
  username: [{ required: true, message: 'Nhập username', trigger: 'blur' }],
  email: [{ required: true, type: 'email', message: 'Email không hợp lệ', trigger: 'blur' }],
}
const changePasswordRules = {
  newPassword: [{ required: true, message: 'Nhập mật khẩu mới', trigger: 'blur' }],
}

// Helpers
const fmtDate = (iso?: string) => (iso ? new Date(iso).toLocaleString('vi-VN') : '')
const roleLabel = (r?: Role) =>
  r === 'admin' ? 'Admin' : r === 'instructor' ? 'Giáo viên' : 'Học sinh'
const statusLabel = (s?: UserStatus) =>
  s === 'active'
    ? 'Hoạt động'
    : s === 'locked'
      ? 'Tạm khoá'
      : s === 'banned'
        ? 'Cấm vĩnh viễn'
        : 'Chờ duyệt'
const roleTagType = (r?: Role) =>
  r === 'admin' ? 'danger' : r === 'instructor' ? 'warning' : 'success'
const statusTagType = (s?: UserStatus) =>
  s === 'active' ? 'success' : s === 'locked' ? 'warning' : s === 'banned' ? 'danger' : 'info'

// Load data
async function load() {
  try {
    const d = await userService.detail(id.value)
    Object.assign(detail, d)
    Object.assign(form, JSON.parse(JSON.stringify(d)))
    if (!form.name && form.username) form.name = form.username
  } catch {
    ElMessage.error('Không tải được người dùng')
  }
}

// Save profile
async function saveProfile() {
  const ok = await profileRef.value?.validate().catch(() => false)
  if (!ok) return
  savingProfile.value = true
  try {
    await userService.update(detail.id, {
      username: form.username,
      email: form.email,
      phone: form.phone,
      name: form.name || undefined,
    })
    ElMessage.success('Đã lưu hồ sơ')
    Object.assign(detail, form)
  } catch {
    ElMessage.error('Lưu thất bại')
  } finally {
    savingProfile.value = false
  }
}

// Change password
function openChangePasswordDialog() {
  console.log('Opening change password dialog')
  changePasswordDialogVisible.value = true
  console.log('Dialog visibility:', changePasswordDialogVisible.value)
}
function resetChangePasswordForm() {
  changePasswordForm.newPassword = ''
}
async function changePassword() {
  const valid = await changePasswordRef.value?.validate().catch(() => false)
  if (!valid) return
  changingPassword.value = true
  try {
    await userService.setPassword(detail.id, { new_password: changePasswordForm.newPassword })
    ElMessage.success('Đã đổi mật khẩu')
    changePasswordDialogVisible.value = false
  } catch {
    ElMessage.error('Đổi mật khẩu thất bại')
  } finally {
    changingPassword.value = false
  }
}

// Delete account
async function deleteAccount() {
  try {
    await ElMessageBox.confirm(
      'Bạn có chắc chắn muốn xóa tài khoản này? Hành động này không thể hoàn tác.',
      'Xác nhận',
      { type: 'warning' },
    )
    deletingAccount.value = true
    await userService.delete(detail.id)
    ElMessage.success('Đã xóa tài khoản')
  } catch {
    ElMessage.error('Xóa tài khoản thất bại')
  } finally {
    deletingAccount.value = false
  }
}

onMounted(load)
</script>
<style>
.el-dialog {
  z-index: 9999 !important; /* Đảm bảo dialog không bị che khuất */
}
</style>
