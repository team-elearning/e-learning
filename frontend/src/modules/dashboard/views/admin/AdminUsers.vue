<script setup lang="ts">
import { ref, onMounted, computed, reactive } from 'vue'
import { adminUsersApi, type AdminUser, type CreateUserDto } from '../../api/admin-users.api'
import {
  Search,
  Plus,
  MoreHorizontal,
  Edit,
  Trash2,
  CheckCircle,
  XCircle,
  Shield,
  User,
  GraduationCap,
  RefreshCw,
} from 'lucide-vue-next'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'

const users = ref<AdminUser[]>([])
const isLoading = ref(false)
const isSyncing = ref(false)
const searchQuery = ref('')

// Modal State
const showModal = ref(false)
const modalMode = ref<'create' | 'edit'>('create')
const isSubmitting = ref(false)
const formRef = ref<FormInstance>()

const formData = reactive({
  id: '',
  username: '',
  email: '',
  password: '',
  role: 'student',
  phone: '',
  is_active: true,
})

const rules = reactive<FormRules>({
  username: [
    { required: true, message: 'Vui lòng nhập tên đăng nhập', trigger: 'blur' },
    { min: 3, message: 'Tên đăng nhập phải có ít nhất 3 ký tự', trigger: 'blur' },
  ],
  email: [
    { required: true, message: 'Vui lòng nhập email', trigger: 'blur' },
    { type: 'email', message: 'Email không hợp lệ', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Vui lòng nhập mật khẩu', trigger: 'blur' },
    { min: 6, message: 'Mật khẩu phải có ít nhất 6 ký tự', trigger: 'blur' },
  ],
  role: [{ required: true, message: 'Vui lòng chọn vai trò', trigger: 'change' }],
})

// Filtered Users
const filteredUsers = computed(() => {
  if (!searchQuery.value) return users.value
  const lowerQuery = searchQuery.value.toLowerCase()
  return users.value.filter(
    (u) =>
      u.username.toLowerCase().includes(lowerQuery) ||
      u.email.toLowerCase().includes(lowerQuery) ||
      u.phone?.includes(lowerQuery),
  )
})

async function fetchUsers() {
  isLoading.value = true
  try {
    const res = await adminUsersApi.getUsers()
    users.value = res.data
  } catch (error) {
    ElMessage.error('Không thể tải danh sách người dùng')
  } finally {
    isLoading.value = false
  }
}

function openCreateModal() {
  modalMode.value = 'create'
  formData.id = ''
  formData.username = ''
  formData.email = ''
  formData.password = ''
  formData.role = 'student'
  formData.phone = ''
  formData.is_active = true
  showModal.value = true
}

function openEditModal(user: AdminUser) {
  modalMode.value = 'edit'
  formData.id = user.id
  formData.username = user.username
  formData.email = user.email
  formData.password = '' // Don't show password, optional to update
  formData.role = user.role
  formData.phone = user.phone || ''
  formData.is_active = user.is_active
  showModal.value = true
}

async function handleSubmit() {
  if (!formRef.value) return
  await formRef.value.validate(async (valid) => {
    if (valid) {
      isSubmitting.value = true
      try {
        if (modalMode.value === 'create') {
          await adminUsersApi.createUser({
            username: formData.username,
            email: formData.email,
            password: formData.password,
            role: formData.role,
            phone: formData.phone || undefined,
            is_active: formData.is_active,
          })
          ElMessage.success('Tạo người dùng thành công')
        } else {
          // Update
          const payload: any = {
            username: formData.username,
            email: formData.email,
            role: formData.role,
            phone: formData.phone || undefined,
            is_active: formData.is_active,
          }
          if (formData.password) {
            payload.password = formData.password
          }

          await adminUsersApi.updateUser(formData.id, payload)
          ElMessage.success('Cập nhật người dùng thành công')
        }
        showModal.value = false
        fetchUsers()
      } catch (error) {
        ElMessage.error('Có lỗi xảy ra, vui lòng thử lại')
      } finally {
        isSubmitting.value = false
      }
    }
  })
}

async function handleDelete(user: AdminUser) {
  try {
    await ElMessageBox.confirm(
      `Bạn có chắc chắn muốn xóa người dùng "${user.username}"? Hành động này không thể hoàn tác.`,
      'Xác nhận xóa',
      {
        confirmButtonText: 'Xóa',
        cancelButtonText: 'Hủy',
        type: 'warning',
        confirmButtonClass: 'el-button--danger',
      },
    )
    await adminUsersApi.deleteUser(user.id)
    ElMessage.success('Đã xóa người dùng')
    fetchUsers()
  } catch {
    // Cancelled
  }
}

async function handleSync() {
  isSyncing.value = true
  try {
    await adminUsersApi.syncData()
    ElMessage.success('Đồng bộ dữ liệu thành công')
    fetchUsers()
  } catch (error) {
    ElMessage.error('Đồng bộ thất bại, vui lòng thử lại')
  } finally {
    isSyncing.value = false
  }
}

function getRoleBadge(role: string) {
  switch (role) {
    case 'admin':
      return { class: 'bg-red-100 text-red-700', label: 'Admin', icon: Shield }
    case 'instructor':
      return { class: 'bg-purple-100 text-purple-700', label: 'Giảng viên', icon: GraduationCap }
    default:
      return { class: 'bg-blue-100 text-blue-700', label: 'Học viên', icon: User }
  }
}

onMounted(() => {
  fetchUsers()
})
</script>

<template>
  <div class="p-6 lg:p-8 min-h-screen bg-slate-50">
    <!-- Header -->
    <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Quản lý người dùng</h1>
        <p class="text-slate-500 mt-1">Quản lý tài khoản và phân quyền trong hệ thống</p>
      </div>
      <div class="flex items-center gap-3">
        <button
          @click="handleSync"
          :disabled="isSyncing"
          class="bg-white text-slate-700 border border-slate-300 px-4 py-2 rounded-lg font-semibold hover:bg-slate-50 transition flex items-center gap-2 shadow-sm disabled:opacity-50"
        >
          <RefreshCw class="w-5 h-5" :class="{ 'animate-spin': isSyncing }" />
          <span class="hidden sm:inline">{{ isSyncing ? 'Đang đồng bộ...' : 'Đồng bộ' }}</span>
        </button>
        <button
          @click="openCreateModal"
          class="bg-indigo-600 text-white px-4 py-2 rounded-lg font-semibold hover:bg-indigo-700 transition flex items-center gap-2 shadow-sm"
        >
          <Plus class="w-5 h-5" /> <span class="hidden sm:inline">Thêm mới</span>
          <span class="inline sm:hidden">Thêm</span>
        </button>
      </div>
    </div>

    <!-- Toolbar -->
    <div
      class="bg-white p-4 rounded-xl border border-slate-200 shadow-sm mb-6 flex items-center gap-4"
    >
      <div class="relative flex-1 max-w-md">
        <Search class="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Tìm kiếm theo tên, email, số điện thoại..."
          class="w-full pl-10 pr-4 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none transition"
        />
      </div>
      <!-- Add filters here if needed -->
    </div>

    <!-- Table -->
    <div class="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <!-- Loading State -->
      <div v-if="isLoading" class="p-8 text-center space-y-4">
        <div
          class="animate-spin w-8 h-8 border-4 border-indigo-600 border-t-transparent rounded-full mx-auto"
        ></div>
        <p class="text-slate-500">Đang tải dữ liệu...</p>
      </div>

      <!-- Empty State -->
      <div v-else-if="filteredUsers.length === 0" class="p-12 text-center">
        <div
          class="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mx-auto mb-4"
        >
          <User class="w-8 h-8 text-slate-400" />
        </div>
        <h3 class="text-lg font-medium text-gray-900">Không tìm thấy người dùng</h3>
        <p class="text-slate-500 mt-1">Thử thay đổi từ khóa tìm kiếm hoặc thêm người dùng mới.</p>
      </div>

      <div v-else class="overflow-x-auto">
        <table class="w-full text-left border-collapse">
          <thead>
            <tr
              class="bg-slate-50 border-b border-slate-200 text-xs uppercase tracking-wider text-slate-500 font-semibold"
            >
              <th class="px-6 py-4">Thông tin</th>
              <th class="px-6 py-4">Liên hệ</th>
              <th class="px-6 py-4">Vai trò</th>
              <th class="px-6 py-4">Trạng thái</th>
              <th class="px-6 py-4 text-right">Hành động</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-100">
            <tr
              v-for="user in filteredUsers"
              :key="user.id"
              class="hover:bg-slate-50/50 transition-colors group"
            >
              <td class="px-6 py-4">
                <div class="flex items-center gap-3">
                  <div
                    class="w-10 h-10 rounded-full bg-slate-200 flex items-center justify-center font-bold text-slate-600 overflow-hidden"
                  >
                    <img
                      :src="`https://ui-avatars.com/api/?name=${user.username}&background=random`"
                      class="w-full h-full object-cover"
                    />
                  </div>
                  <div>
                    <div class="font-medium text-gray-900">{{ user.username }}</div>
                    <div class="text-xs text-slate-500">ID: {{ user.id.slice(0, 8) }}...</div>
                  </div>
                </div>
              </td>
              <td class="px-6 py-4 text-sm">
                <div class="text-gray-600 mb-1">{{ user.email }}</div>
                <div class="text-slate-500 text-xs">{{ user.phone || 'Chưa cập nhật' }}</div>
              </td>
              <td class="px-6 py-4">
                <span
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
                  :class="getRoleBadge(user.role).class"
                >
                  <component :is="getRoleBadge(user.role).icon" class="w-3.5 h-3.5" />
                  {{ getRoleBadge(user.role).label }}
                </span>
              </td>
              <td class="px-6 py-4">
                <span
                  class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold"
                  :class="
                    user.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  "
                >
                  <component :is="user.is_active ? CheckCircle : XCircle" class="w-3.5 h-3.5" />
                  {{ user.is_active ? 'Hoạt động' : 'Đã khóa' }}
                </span>
              </td>
              <td class="px-6 py-4 text-right">
                <div
                  class="opacity-0 group-hover:opacity-100 transition-opacity flex justify-end gap-2"
                >
                  <button
                    @click="openEditModal(user)"
                    class="p-2 text-slate-500 hover:bg-indigo-50 hover:text-indigo-600 rounded-lg transition-colors"
                    title="Chỉnh sửa"
                  >
                    <Edit class="w-4 h-4" />
                  </button>
                  <button
                    @click="handleDelete(user)"
                    class="p-2 text-slate-500 hover:bg-red-50 hover:text-red-600 rounded-lg transition-colors"
                    title="Xóa"
                  >
                    <Trash2 class="w-4 h-4" />
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Modal Form -->
    <div v-if="showModal" class="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="showModal = false"></div>
      <div
        class="bg-white rounded-2xl shadow-xl w-full max-w-lg p-6 relative z-10 animate-in fade-in zoom-in-95 duration-200"
      >
        <h3 class="text-xl font-bold text-gray-900 mb-6">
          {{ modalMode === 'create' ? 'Thêm người dùng mới' : 'Cập nhật thông tin' }}
        </h3>

        <el-form :model="formData" :rules="rules" ref="formRef" label-position="top">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <el-form-item label="Tên đăng nhập" prop="username">
              <el-input v-model="formData.username" placeholder="Nhập username" />
            </el-form-item>
            <el-form-item label="Số điện thoại" prop="phone">
              <el-input v-model="formData.phone" placeholder="Nhập số điện thoại" />
            </el-form-item>
          </div>

          <el-form-item label="Email" prop="email">
            <el-input v-model="formData.email" placeholder="Nhập địa chỉ email" />
          </el-form-item>

          <el-form-item
            v-if="modalMode === 'create' || formData.password"
            :label="modalMode === 'edit' ? 'Mật khẩu mới (để trống nếu không đổi)' : 'Mật khẩu'"
            :prop="modalMode === 'create' ? 'password' : ''"
          >
            <el-input
              v-model="formData.password"
              type="password"
              placeholder="Nhập mật khẩu"
              show-password
            />
          </el-form-item>

          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <el-form-item label="Vai trò" prop="role">
              <el-select v-model="formData.role" placeholder="Chọn vai trò" class="w-full">
                <el-option label="Học viên" value="student" />
                <el-option label="Giảng viên" value="instructor" />
                <el-option label="Admin" value="admin" />
              </el-select>
            </el-form-item>

            <el-form-item label="Trạng thái" prop="is_active">
              <el-switch
                v-model="formData.is_active"
                active-text="Hoạt động"
                inactive-text="Vô hiệu hóa"
              />
            </el-form-item>
          </div>

          <div class="flex justify-end gap-3 mt-6">
            <button
              @click="showModal = false"
              class="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg font-medium transition-colors"
              type="button"
            >
              Hủy
            </button>
            <button
              @click="handleSubmit"
              class="px-6 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 transition"
              :disabled="isSubmitting"
            >
              {{
                isSubmitting ? 'Đang xử lý...' : modalMode === 'create' ? 'Tạo mới' : 'Lưu thay đổi'
              }}
            </button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>
