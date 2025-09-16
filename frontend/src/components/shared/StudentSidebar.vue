<template>
  <aside class="h-full flex flex-col bg-white border-r">
    <div class="p-4 font-bold text-lg border-b">Student Panel</div>
    <nav class="flex-1 p-2">
      <RouterLink to="/student/dashboard" class="block p-2 rounded hover:bg-purple-100"
        >Dashboard</RouterLink
      >
      <RouterLink to="/student/courses" class="block p-2 rounded hover:bg-purple-100"
        >Khóa học của tôi</RouterLink
      >
      <RouterLink to="/student/exams" class="block p-2 rounded hover:bg-purple-100"
        >Bài kiểm tra</RouterLink
      >
      <RouterLink to="/student/payments" class="block p-2 rounded hover:bg-purple-100"
        >Thanh toán</RouterLink
      >
      <RouterLink to="/student/account" class="block p-2 rounded hover:bg-purple-100"
        >Tài khoản</RouterLink
      >
    </nav>
  </aside>
</template>
<script setup lang="ts">
// StudentSidebar logic here
</script>
