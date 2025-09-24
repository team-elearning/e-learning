<template>
  <div class="activity">
    <ul class="list">
      <li v-for="(it,i) in items" :key="i">
        <div class="dot"></div>
        <div class="content">
          <b>{{ it.title }}</b>
          <div class="muted small">{{ it.time }}</div>
        </div>
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
const items = [
  { title: 'Đăng nhập hệ thống', time: 'Hôm nay, 09:25' },
  { title: 'Cập nhật thông tin hồ sơ', time: 'Hôm qua, 19:10' },
  { title: 'Đổi mật khẩu', time: '2 ngày trước, 08:02' },
]
</script>

<style scoped>
.activity{ padding:8px 0; }
.list{ list-style:none; padding:0; margin:0; display:flex; flex-direction:column; gap:10px; }
.list li{ display:flex; gap:12px; align-items:flex-start; padding:10px 12px; border:1px solid var(--line); border-radius:12px; background:#fff; }
.dot{ width:10px; height:10px; border-radius:50%; background:var(--accent); margin-top:6px; }
.content .small{ font-size:12px; }
.muted{ color:#6b7280; }
</style>
