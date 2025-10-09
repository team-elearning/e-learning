<template>
  <div class="min-h-screen w-screen bg-gray-50 flex">
    <!-- Cột trái: brand/illustration (ẩn trên mobile) -->
    <section
      class="relative hidden lg:flex w-1/2 items-center justify-center overflow-hidden bg-gradient-to-br from-indigo-500 to-emerald-500"
    >
      <div class="absolute inset-0 bg-black/10"></div>
      <div class="relative z-10 px-10 text-white">
        <h1 class="text-3xl font-semibold mb-2">Welcome to Your Learning Space</h1>
        <p class="text-white/90">Học tập hiệu quả, quản lý lớp học thông minh, báo cáo rõ ràng.</p>
      </div>
    </section>

    <!-- Cột phải: form -->
    <section class="flex w-full lg:w-1/2 items-center justify-center">
      <div class="w-full max-w-md p-6 sm:p-8">
        <!-- Logo nhỏ + switch -->
        <div class="mb-8 text-center">
          <LogoEduriot :size="120" style="justify-content: center" />
          <h2 class="mt-3 text-xl font-semibold text-gray-800">Đăng nhập / Đăng ký</h2>
          <p class="text-sm text-gray-500">Truy cập bằng tài khoản của bạn</p>
        </div>

        <!-- Nơi render các trang auth -->
        <div class="rounded-lg bg-white p-6 shadow-sm ring-1 ring-black/5">
          <router-view />
        </div>

        <!-- Footer nhỏ -->
        <p class="mt-6 text-center text-xs text-gray-500">
          © {{ new Date().getFullYear() }} Your Org. All rights reserved.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import LogoEduriot from '@/components/ui/LogoEduriot.vue'
// no-op
</script>
