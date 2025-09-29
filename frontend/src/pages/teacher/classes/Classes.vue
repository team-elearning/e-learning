<!-- src/pages/teacher/classes/Classes.vue -->
<template>
  <div class="min-h-screen w-full overflow-x-hidden bg-slate-50">
    <main class="w-full mx-auto max-w-screen-2xl px-6 py-8 md:px-10">
      <!-- Header -->
      <div class="mb-5 flex items-center justify-between gap-3">
        <h1 class="text-2xl font-semibold">Lớp học</h1>
        <button
          class="inline-flex items-center rounded-xl bg-sky-600 px-4 py-2 font-semibold text-white hover:bg-sky-700"
          @click="createClass"
        >
          + Tạo lớp học
        </button>
      </div>

      <!-- Tools (chỉ UI, không fetch) -->
      <div class="mb-5 grid grid-cols-1 gap-3 md:grid-cols-3">
        <div class="md:col-span-2">
          <div class="flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-3 py-2">
            <svg viewBox="0 0 24 24" class="h-5 w-5 text-slate-400" fill="none" stroke="currentColor">
              <circle cx="11" cy="11" r="8" stroke-width="2" />
              <path d="M21 21l-4.3-4.3" stroke-width="2" />
            </svg>
            <input
              v-model.trim="q"
              type="text"
              placeholder="Tìm lớp theo tên, mã hoặc khoá… (không có dữ liệu)"
              class="w-full bg-transparent outline-none"
              disabled
            />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-2">
          <select class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm" disabled>
            <option>Tất cả trạng thái</option>
          </select>
          <select class="rounded-2xl border border-slate-200 bg-white px-3 py-2 text-sm" disabled>
            <option>Mới cập nhật</option>
          </select>
        </div>
      </div>

      <!-- Empty state -->
      <div class="grid place-items-center rounded-2xl border border-dashed border-slate-300 bg-white py-16">
        <div class="text-center max-w-md px-6">
          <div class="mx-auto mb-3 grid h-12 w-12 place-items-center rounded-xl bg-slate-100 text-slate-500">
            <svg viewBox="0 0 24 24" class="h-6 w-6" fill="none" stroke="currentColor">
              <rect x="3" y="4" width="18" height="14" rx="2" stroke-width="2"/>
              <path d="M3 10h18M8 14h.01M12 14h.01M16 14h.01" stroke-width="2"/>
            </svg>
          </div>
          <h2 class="mb-1 text-lg font-semibold text-slate-800">Chưa có lớp học</h2>
          <p class="mb-4 text-slate-500">
            Bạn chưa tạo lớp nào. Hãy bắt đầu bằng cách tạo lớp mới để quản lý học sinh, lịch học và bài tập.
          </p>
          <button
            class="inline-flex items-center rounded-xl bg-sky-600 px-4 py-2 font-semibold text-white hover:bg-sky-700"
            @click="createClass"
          >
            + Tạo lớp học
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const q = ref('') // chỉ để bind UI, không dùng fetch

function createClass() {
  // Điều hướng tới trang tạo lớp (tuỳ router của bạn)
  router.push({ path: '/teacher/classes/new' })
}
</script>

<style scoped>
:host, .min-h-screen { overflow-x: hidden; }
</style>
