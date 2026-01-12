<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="min-h-screen flex items-center justify-center p-4">
    <div class="w-full max-w-md border rounded-2xl p-6 space-y-3">
      <h1 class="text-xl font-semibold">Không có quyền truy cập</h1>
      <p class="text-sm opacity-70">Tài khoản của bạn không được phép vào trang này.</p>
      <el-button type="primary" class="w-full" @click="router.push('/login')">
        Về trang đăng nhập
      </el-button>
    </div>
  </div>
</template>
