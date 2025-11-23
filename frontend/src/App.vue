<!-- src/App.vue -->
<template>
  <!-- Element Plus config (tùy chọn, nhưng hữu ích) -->
  <el-config-provider namespace="el" :z-index="3000">
    <!-- Route outlet -->
    <RouterView v-slot="{ Component }">
      <Transition name="fade" mode="out-in">
        <component :is="Component" />
      </Transition>
    </RouterView>
  </el-config-provider>
</template>

<script setup lang="ts">
import { RouterView } from 'vue-router'
import { ElConfigProvider } from 'element-plus'
import { useIdleLogout } from './composables/useIdleLogout'
useIdleLogout(15) // 15 phút không hoạt động -> cảnh báo -> logout
</script>

<style>
/* Transition nhẹ nhàng khi đổi page */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
/* Ẩn icon mắt mặc định của Edge/Chrome */
input::-ms-reveal,
input::-ms-clear {
  display: none;
}

input::-webkit-credentials-auto-fill-button {
  visibility: hidden;
  display: none !important;
  pointer-events: none;
  height: 0;
  width: 0;
}
</style>
