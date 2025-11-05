import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useUiStore = defineStore('ui', () => {
    const showIdleWarning = ref(false)
    const idleRemaining = ref(0) // ms
    let _resetFn: (() => void) | null = null

    function openIdleWarning(ms = 0, resetFn?: () => void) {
        idleRemaining.value = ms
        _resetFn = resetFn ?? null
        showIdleWarning.value = true
    }

    function closeIdleWarning() {
        showIdleWarning.value = false
    }

    function keepAlive() {
        if (_resetFn) _resetFn()
        closeIdleWarning()
    }

    return { showIdleWarning, idleRemaining, openIdleWarning, closeIdleWarning, keepAlive }
})