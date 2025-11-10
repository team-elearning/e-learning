// src/composables/useIdleLogout.ts
import { onMounted, onUnmounted } from 'vue'
import { useAuthStore } from '@/store/auth.store'
import { ElMessage } from 'element-plus'

export function useIdleLogout(minutes = 10) {
    const auth = useAuthStore()

    const MAX_IDLE = minutes * 60 * 1000
    let idleTimer: number

    const resetIdleTimer = () => {
        clearTimeout(idleTimer)

        idleTimer = window.setTimeout(() => {
            if (auth.isAuthenticated) {
                ElMessage.info('Phiên đăng nhập đã hết hạn')
                auth.logout()
            }
        }, MAX_IDLE)
    }

    const activityEvents = ['mousemove', 'keydown', 'click', 'scroll', 'touchstart']

    onMounted(() => {
        if (!auth.isAuthenticated) return

        resetIdleTimer()
        activityEvents.forEach((event) => window.addEventListener(event, resetIdleTimer))
    })

    onUnmounted(() => {
        activityEvents.forEach((event) => window.removeEventListener(event, resetIdleTimer))
        clearTimeout(idleTimer)
    })
}
