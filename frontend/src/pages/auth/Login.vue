<template>
  <div class="space-y-6">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="Email" prop="email">
        <el-input v-model="form.email" placeholder="you@example.com" />
      </el-form-item>

      <el-form-item label="Mật khẩu" prop="password">
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>

      <div class="flex items-center justify-between">
        <el-checkbox v-model="form.remember">Ghi nhớ</el-checkbox>
        <RouterLink to="/auth/forgot-password" class="text-sm text-indigo-600 hover:underline">
          Quên mật khẩu?
        </RouterLink>
      </div>

      <el-button type="primary" class="w-full mt-4" :loading="loading" @click="onSubmit">
        Đăng nhập
      </el-button>

      <el-divider>hoặc</el-divider>

      <el-button class="w-full" @click="loginWithGoogle" :loading="loadingGoogle">
        Đăng nhập bằng Google
      </el-button>
    </el-form>

    <p class="text-center text-sm text-gray-500">
      Chưa có tài khoản?
      <RouterLink to="/auth/register" class="text-indigo-600 hover:underline"> Đăng ký </RouterLink>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/store/auth.store'

const auth = useAuthStore()
const formRef = ref()
const loading = ref(false)
const loadingGoogle = ref(false)

const form = ref({
  email: '',
  password: '',
  remember: true,
})

const rules = {
  email: [
    { required: true, message: 'Nhập email', trigger: 'blur' },
    { type: 'email', message: 'Email không hợp lệ', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Nhập mật khẩu', trigger: 'blur' },
    { min: 6, message: 'Tối thiểu 6 ký tự', trigger: 'blur' },
  ],
}

const onSubmit = async () => {
  await formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      await auth.login(form.value.email, form.value.password, form.value.remember)
      ElMessage.success('Đăng nhập thành công')
      // redirect theo role đã làm trong store
    } catch (e: any) {
      ElMessage.error(e?.message || 'Đăng nhập thất bại')
    } finally {
      loading.value = false
    }
  })
}

const loginWithGoogle = async () => {
  loadingGoogle.value = true
  // TODO: tích hợp OAuth thực — tạm mock
  setTimeout(async () => {
    await auth.loginWithGoogle()
    ElMessage.success('Đăng nhập Google thành công')
    loadingGoogle.value = false
  }, 800)
}
</script>
