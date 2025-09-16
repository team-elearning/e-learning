<template>
  <aside class="h-full flex flex-col bg-white border-r">
    <div class="p-4 font-bold text-lg border-b">Teacher Panel</div>
    <nav class="flex-1 p-2">
      <RouterLink to="/teacher/dashboard" class="block p-2 rounded hover:bg-blue-100"
        >Dashboard</RouterLink
      >
      <RouterLink to="/teacher/courses" class="block p-2 rounded hover:bg-blue-100"
        >Khóa học</RouterLink
      >
      <RouterLink to="/teacher/classes" class="block p-2 rounded hover:bg-blue-100"
        >Lớp học</RouterLink
      >
      <RouterLink to="/teacher/exams" class="block p-2 rounded hover:bg-blue-100"
        >Bài kiểm tra</RouterLink
      >
      <RouterLink to="/teacher/students" class="block p-2 rounded hover:bg-blue-100"
        >Học sinh</RouterLink
      >
    </nav>
  </aside>
</template>
<script setup lang="ts">
// TeacherSidebar logic here
</script>
