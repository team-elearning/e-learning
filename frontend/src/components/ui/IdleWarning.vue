<template>
  <el-dialog v-model="visible" title="Phiên làm việc sắp hết" width="420px">
    <p>
      Bạn đã không hoạt động trong một thời gian.<br />
      Hệ thống sẽ tự động đăng xuất sau <b>{{ countdown }} giây</b>.
    </p>

    <template #footer>
      <el-button @click="extendSession">Tiếp tục phiên</el-button>
      <el-button type="danger" @click="logout">Đăng xuất ngay</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from '@/store/auth.store'

const auth = useAuthStore()
const visible = ref(false)
const countdown = ref(60) // 60 giây cảnh báo

const logout = () => {
  visible.value = false
  auth.logout()
}

const extendSession = () => {
  visible.value = false
  countdown.value = 60
  window.dispatchEvent(new Event('reset-idle-timer')) // Emit cho composable
}

defineExpose({ visible, countdown })
</script>
