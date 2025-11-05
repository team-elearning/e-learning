<template>
  <div v-if="ui.showIdleWarning" class="fixed inset-0 z-[9999] flex items-center justify-center">
    <div class="absolute inset-0 bg-black/50" @click="ui.closeIdleWarning()" />
    <div class="bg-white rounded-lg shadow-lg p-5 z-10 w-full max-w-sm">
      <h3 class="text-lg font-semibold mb-2">Bạn sắp bị đăng xuất</h3>
      <p class="text-sm text-gray-600 mb-4">
        Không có hoạt động trong một thời gian, hệ thống sẽ tự động đăng xuất.
      </p>
      <div class="text-center mb-4">
        <span class="text-2xl font-medium">{{ secondsLeft }}</span>
        <span class="text-sm text-gray-500"> giây</span>
      </div>
      <div class="flex justify-end gap-3">
        <button @click="ui.closeIdleWarning()" class="px-4 py-2 rounded bg-gray-100">Hủy</button>
        <button @click="stay" class="px-4 py-2 rounded bg-green-600 text-white">Ở lại</button>
        <button @click="logoutNow" class="px-4 py-2 rounded bg-red-600 text-white">
          Đăng xuất
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onBeforeUnmount } from 'vue'
import { useUiStore } from '@/stores/ui.store'
import { useAuthStore } from '@/store/auth.store'
import router from '@/router'

const ui = useUiStore()
const auth = useAuthStore()

const secondsLeft = computed(() => Math.max(0, Math.ceil((ui.idleRemaining ?? 0) / 1000)))

let countdown: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  countdown = setInterval(() => {
    if (ui.showIdleWarning && ui.idleRemaining > 0) {
      ui.idleRemaining = Math.max(0, ui.idleRemaining - 1000)
    }
  }, 1000)
})

onBeforeUnmount(() => {
  if (countdown) clearInterval(countdown)
})

function stay() {
  ui.keepAlive() // gọi reset function thiết lập trong store
}

async function logoutNow() {
  ui.closeIdleWarning()
  try {
    if (typeof auth.logout === 'function') {
      await auth.logout()
    } else {
      localStorage.removeItem('access')
      localStorage.removeItem('accessToken')
      localStorage.removeItem('refresh')
    }
  } finally {
    router.push({ name: 'Login' }).catch(() => {})
  }
}
</script>

<style scoped>
/* tuỳ chỉnh nếu cần */
</style>
