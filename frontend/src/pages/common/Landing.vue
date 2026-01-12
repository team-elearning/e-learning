<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="min-h-screen flex flex-col font-sans">
    <!-- Navbar -->
    <header class="sticky top-0 z-50 glass border-b border-gray-100">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div
            class="h-8 w-8 rounded-lg bg-gradient-to-br from-[rgb(var(--primary))] to-[rgb(var(--secondary))] flex items-center justify-center text-white font-bold text-lg"
          >
            E
          </div>
          <span class="font-bold text-xl tracking-tight text-[rgb(var(--text))]">EduRiot</span>
        </div>
        <div class="flex items-center gap-4">
          <button
            @click="router.push('/login')"
            class="text-sm font-semibold text-[rgb(var(--text-light))] hover:text-[rgb(var(--primary))] transition"
          >
            Đăng nhập
          </button>
          <button
            @click="router.push('/register')"
            class="px-4 py-2 rounded-full bg-[rgb(var(--text))] text-white text-sm font-semibold hover:bg-slate-800 transition shadow-lg"
          >
            Đăng ký miễn phí
          </button>
        </div>
      </div>
    </header>

    <!-- Hero -->
    <main class="flex-grow">
      <section class="relative pt-20 pb-32 overflow-hidden">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div
            class="inline-flex items-center justify-center p-1 px-3 mb-6 rounded-full bg-blue-50 border border-blue-100"
          >
            <span class="flex h-2 w-2 rounded-full bg-[rgb(var(--primary))] mr-2"></span>
            <span class="text-xs font-semibold uppercase tracking-wide text-[rgb(var(--primary))]"
              >Nền tảng học tập thế hệ mới</span
            >
          </div>

          <h1
            class="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 leading-tight text-[rgb(var(--text))]"
          >
            Học tập không giới hạn <br />
            <span class="text-gradient">Kiến tạo tương lai</span>
          </h1>

          <p class="mt-4 max-w-2xl mx-auto text-xl text-[rgb(var(--text-light))] mb-10">
            Nền tảng quản lý học tập toàn diện dành cho Giáo viên và Học sinh. Trải nghiệm giao diện
            hiện đại, tối ưu hóa cho sự tập trung và hiệu quả.
          </p>

          <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              @click="router.push('/login')"
              class="h-12 px-8 rounded-full bg-[rgb(var(--primary))] text-white font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition flex items-center gap-2"
            >
              Bắt đầu ngay
              <span class="text-lg">→</span>
            </button>
            <button
              class="h-12 px-8 rounded-full bg-white border border-gray-200 text-[rgb(var(--text))] font-semibold hover:bg-gray-50 transition shadow-sm"
            >
              Tìm hiểu thêm
            </button>
          </div>
        </div>

        <!-- Decoration -->
        <div
          class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-blue-200/30 to-purple-200/30 rounded-full blur-3xl -z-10"
        ></div>
      </section>

      <!-- Feature Grid -->
      <section class="py-24 bg-white">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="grid md:grid-cols-3 gap-8">
            <!-- Feature 1 -->
            <div
              class="p-8 rounded-2xl bg-[rgb(var(--bg))] border border-[rgb(var(--border))] hover:shadow-lg transition duration-300"
            >
              <div
                class="h-12 w-12 rounded-xl bg-blue-100 flex items-center justify-center mb-6 text-2xl"
              >
                📚
              </div>
              <h3 class="text-xl font-bold mb-3 text-[rgb(var(--text))]">Quản lý khóa học</h3>
              <p class="text-[rgb(var(--text-light))]">
                Tổ chức bài giảng, tài liệu và lộ trình học tập một cách khoa học và dễ dàng truy
                cập.
              </p>
            </div>
            <!-- Feature 2 -->
            <div
              class="p-8 rounded-2xl bg-[rgb(var(--bg))] border border-[rgb(var(--border))] hover:shadow-lg transition duration-300"
            >
              <div
                class="h-12 w-12 rounded-xl bg-green-100 flex items-center justify-center mb-6 text-2xl"
              >
                📝
              </div>
              <h3 class="text-xl font-bold mb-3 text-[rgb(var(--text))]">
                Bài kiểm tra & Đánh giá
              </h3>
              <p class="text-[rgb(var(--text-light))]">
                Hệ thống thi trắc nghiệm online, tự động chấm điểm và báo cáo kết quả chi tiết.
              </p>
            </div>
            <!-- Feature 3 -->
            <div
              class="p-8 rounded-2xl bg-[rgb(var(--bg))] border border-[rgb(var(--border))] hover:shadow-lg transition duration-300"
            >
              <div
                class="h-12 w-12 rounded-xl bg-orange-100 flex items-center justify-center mb-6 text-2xl"
              >
                📊
              </div>
              <h3 class="text-xl font-bold mb-3 text-[rgb(var(--text))]">Báo cáo & Thống kê</h3>
              <p class="text-[rgb(var(--text-light))]">
                Theo dõi tiến độ học tập, chuyên cần và hiệu suất qua các biểu đồ trực quan.
              </p>
            </div>
          </div>
        </div>
      </section>
    </main>

    <footer
      class="py-6 text-center text-sm text-[rgb(var(--text-light))] border-t border-[rgb(var(--border))]"
    >
      © 2024 Eduriot LMS. All rights reserved.
    </footer>
  </div>
</template>
