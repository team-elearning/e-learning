<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()

const logoSrc = '/favicon.png' // <-- đổi đúng file logo trong /public
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <!-- Top glow background -->
    <!-- <div class="pointer-events-none fixed inset-0 -z-10">
      <div
        class="absolute -top-40 left-1/2 -translate-x-1/2 h-[520px] w-[920px] rounded-full blur-3xl opacity-60"
        :style="{
          background:
            'radial-gradient(circle at 30% 30%, rgba(var(--brand-300),.55), transparent 60%), radial-gradient(circle at 70% 40%, rgba(var(--accent-500),.35), transparent 65%)',
        }"
      />
    </div> -->

    <!-- Header -->
    <!-- <header class="sticky top-0 z-50 border-b bg-white/70 backdrop-blur">
      <div class="mx-auto max-w-6xl px-4 py-3 flex items-center justify-between">
        <button class="flex items-center gap-3" @click="router.push('/')">
          <img
            :src="logoSrc"
            alt="Logo"
            class="h-9 w-9 rounded-xl object-contain bg-white border"
          />
          <div class="text-left leading-tight">
            <div class="font-semibold">EduRiot LMS</div>
            <div class="text-xs opacity-70">Learning made simple</div>
          </div>
        </button>

        <nav class="hidden md:flex items-center gap-2">
          <a class="px-3 py-2 rounded-xl hover:bg-slate-100" href="#features">Tính năng</a>
          <a class="px-3 py-2 rounded-xl hover:bg-slate-100" href="#roles">Vai trò</a>
          <a class="px-3 py-2 rounded-xl hover:bg-slate-100" href="#pricing">Gói</a>
          <a class="px-3 py-2 rounded-xl hover:bg-slate-100" href="#faq">FAQ</a>
        </nav>

        <div class="flex items-center gap-2">
          <el-button class="hidden sm:inline-flex" text @click="router.push('/login')"
            >Đăng nhập</el-button
          >
          <el-button type="primary" @click="router.push('/login')">Bắt đầu</el-button>
        </div>
      </div>
    </header> -->

    <!-- Page -->
    <main class="flex-1">
      <router-view />
    </main>

    <!-- Footer -->
    <!-- <footer class="border-t bg-white">
      <div class="mx-auto max-w-6xl px-4 py-10 grid gap-8 md:grid-cols-3">
        <div>
          <div class="font-semibold">EduRiot LMS</div>
          <div class="mt-2 text-sm text-slate-600">
            Nền tảng quản lý học tập cho Admin • Giáo viên • Học sinh.
          </div>
          <div class="mt-4 text-xs text-slate-500">
            © {{ new Date().getFullYear() }} EduRiot. All rights reserved.
          </div>
        </div>

        <div class="grid grid-cols-2 gap-6 text-sm">
          <div>
            <div class="font-medium">Sản phẩm</div>
            <div class="mt-2 space-y-2 text-slate-600">
              <a href="#features" class="block hover:underline">Tính năng</a>
              <a href="#roles" class="block hover:underline">Vai trò</a>
              <a href="#pricing" class="block hover:underline">Gói dịch vụ</a>
            </div>
          </div>
          <div>
            <div class="font-medium">Hỗ trợ</div>
            <div class="mt-2 space-y-2 text-slate-600">
              <a href="#faq" class="block hover:underline">FAQ</a>
              <a class="block hover:underline" href="#">Chính sách</a>
              <a class="block hover:underline" href="#">Liên hệ</a>
            </div>
          </div>
        </div>

        <div class="md:text-right">
          <div class="font-medium">Sẵn sàng bắt đầu?</div>
          <div class="mt-2 text-sm text-slate-600">
            Đăng nhập để trải nghiệm dashboard theo vai trò.
          </div>
          <div class="mt-4 flex md:justify-end">
            <el-button type="primary" @click="router.push('/login')">Đăng nhập</el-button>
          </div>
        </div>
      </div>
    </footer> -->
  </div>
</template>
