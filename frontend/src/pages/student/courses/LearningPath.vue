<template>
  <div class="min-h-screen bg-slate-50">
    <div class="mx-auto max-w-5xl px-4 py-8">
      <h1 class="text-2xl font-extrabold text-slate-900">Lộ trình học</h1>
      <p class="mt-1 text-slate-600">Chọn lộ trình phù hợp để đạt mục tiêu theo từng giai đoạn.</p>

      <div class="mt-5 grid gap-4 sm:grid-cols-2">
        <!-- basic -->
        <section class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-extrabold text-slate-900">Khối 1–2 (Cơ bản)</h2>
            <span class="rounded-full border border-emerald-200 bg-emerald-50 px-3 py-1 text-xs font-bold text-emerald-700">Nền tảng</span>
          </div>
          <p class="mt-2 text-slate-700">Củng cố Toán, Tiếng Việt, Tiếng Anh với các bài ngắn dễ tiếp thu.</p>
          <ul class="mt-3 space-y-1 text-sm text-slate-700">
            <li>• Kiến thức cốt lõi theo tuần</li>
            <li>• Bài tập luyện thói quen học</li>
            <li>• Theo dõi tiến độ đơn giản</li>
          </ul>
          <div class="mt-4">
            <router-link
              class="inline-flex items-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-extrabold text-white hover:bg-slate-800"
              :to="{ name:'student-catalog', query:{ grade: 1 } }"
            >Bắt đầu ngay</router-link>
          </div>
        </section>

        <!-- advanced -->
        <section class="rounded-2xl border border-slate-200 bg-white p-5">
          <div class="flex items-center justify-between">
            <h2 class="text-lg font-extrabold text-slate-900">Khối 3–5 (Nâng cao)</h2>
            <span class="rounded-full border border-sky-200 bg-sky-50 px-3 py-1 text-xs font-bold text-sky-700">Mở rộng</span>
          </div>
          <p class="mt-2 text-slate-700">Hệ thống hoá & luyện thi: Toán, TV, Anh + Khoa học/Lịch sử.</p>
          <ul class="mt-3 space-y-1 text-sm text-slate-700">
            <li>• Quiz ôn tập định kỳ</li>
            <li>• Lộ trình theo mục tiêu</li>
            <li>• Báo cáo tiến bộ chi tiết</li>
          </ul>
          <div class="mt-4">
            <router-link
              class="inline-flex items-center rounded-xl bg-slate-900 px-4 py-2 text-sm font-extrabold text-white hover:bg-slate-800"
              :to="{ name:'student-catalog', query:{ grade: 3 } }"
            >Chọn khóa</router-link>
          </div>
        </section>
      </div>

      <div class="mt-6 flex justify-end">
        <router-link class="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50"
                     :to="{ name:'MyCourses' }">Về My Courses</router-link>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>
