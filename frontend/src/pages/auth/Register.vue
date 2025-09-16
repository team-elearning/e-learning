<template>
  <div class="space-y-6">
    <el-form ref="formRef" :model="form" :rules="rules" label-position="top">
      <el-form-item label="Họ và tên" prop="fullName">
        <el-input v-model="form.fullName" placeholder="Nguyễn Văn A" />
      </el-form-item>

      <el-form-item label="Username" prop="username">
        <el-input v-model="form.username" placeholder="nguyenvana" />
      </el-form-item>

      <el-form-item label="Email" prop="email">
        <el-input v-model="form.email" placeholder="you@example.com" />
      </el-form-item>

      <el-form-item label="Số điện thoại" prop="phone">
        <el-input v-model="form.phone" placeholder="09xxxxxxxx" />
      </el-form-item>

      <el-form-item label="Mật khẩu" prop="password">
        <el-input v-model="form.password" type="password" show-password />
      </el-form-item>

      <el-form-item label="Nhập lại mật khẩu" prop="confirm">
        <el-input v-model="form.confirm" type="password" show-password />
      </el-form-item>

      <el-form-item prop="agree">
        <el-checkbox v-model="form.agree">
          Tôi đã đọc và đồng ý với
          <a href="#" target="_blank" class="text-indigo-600 hover:underline">Điều khoản</a>
        </el-checkbox>
      </el-form-item>

      <el-button type="primary" class="w-full mt-2" :loading="loading" @click="onSubmit">
        Đăng ký
      </el-button>
    </el-form>

    <p class="text-center text-sm text-gray-500">
      Đã có tài khoản?
      <RouterLink to="/auth/login" class="text-indigo-600 hover:underline"> Đăng nhập </RouterLink>
    </p>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { authService } from '@/services/auth.service'
import { useRouter } from 'vue-router'

const router = useRouter()
const formRef = ref()
const loading = ref(false)

const form = ref({
  fullName: '',
  username: '',
  email: '',
  phone: '',
  password: '',
  confirm: '',
  agree: false,
})

const rules = {
  fullName: [{ required: true, message: 'Nhập họ tên', trigger: 'blur' }],
  username: [{ required: true, message: 'Nhập username', trigger: 'blur' }],
  email: [
    { required: true, message: 'Nhập email', trigger: 'blur' },
    { type: 'email', message: 'Email không hợp lệ', trigger: 'blur' },
  ],
  phone: [
    { required: true, message: 'Nhập số điện thoại', trigger: 'blur' },
    { pattern: /^0\d{9,10}$/, message: 'Số điện thoại không hợp lệ', trigger: 'blur' },
  ],
  password: [
    { required: true, message: 'Nhập mật khẩu', trigger: 'blur' },
    { min: 6, message: 'Tối thiểu 6 ký tự', trigger: 'blur' },
  ],
  confirm: [
    {
      validator: (_: any, value: string, cb: Function) => {
        if (value !== form.value.password) cb(new Error('Mật khẩu không khớp'))
        else cb()
      },
      trigger: 'blur',
    },
  ],
  agree: [
    {
      type: 'boolean',
      required: true,
      validator: (_: any, v: boolean) => v === true,
      message: 'Vui lòng đồng ý điều khoản',
      trigger: 'change',
    },
  ],
}

const onSubmit = async () => {
  await formRef.value?.validate(async (valid: boolean) => {
    if (!valid) return
    loading.value = true
    try {
      await authService.register(form.value)
      ElMessage.success('Đăng ký thành công. Vui lòng đăng nhập.')
      router.push('/auth/login')
    } catch (e: any) {
      ElMessage.error(e?.message || 'Đăng ký thất bại')
    } finally {
      loading.value = false
    }
  })
}
</script>
