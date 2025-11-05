import { ref, onMounted, onBeforeUnmount } from 'vue'

type Options = {
    timeout?: number // ms
    warningTime?: number // ms before logout to show warning
    onLogout: () => void
    onWarn?: (remainingMs: number) => void
}

const STORAGE_KEY = 'app-last-activity'

export function useIdleLogout(opts: Options) {
    const timeout = opts.timeout ?? 10 * 60 * 1000 // default 10 minutes
    const warningTime = opts.warningTime ?? 60 * 1000 // default 1 minute
    const isWarning = ref(false)
    const remaining = ref<number>(timeout)

    let idleTimer: ReturnType<typeof setTimeout> | null = null
    let warnTimer: ReturnType<typeof setTimeout> | null = null

    function updateLastActivity() {
        const now = Date.now()
        try {
            localStorage.setItem(STORAGE_KEY, String(now))
        } catch {
            // ignore (privacy modes)
        }
        resetTimers()
    }

    function handleStorageEvent(e: StorageEvent) {
        if (e.key === STORAGE_KEY) {
            resetTimers()
        }
    }

    function clearTimers() {
        if (idleTimer) {
            clearTimeout(idleTimer)
            idleTimer = null
        }
        if (warnTimer) {
            clearTimeout(warnTimer)
            warnTimer = null
        }
        isWarning.value = false
    }

    function resetTimers() {
        clearTimers()
        const last = Number(localStorage.getItem(STORAGE_KEY) || Date.now())
        const elapsed = Date.now() - last
        const timeLeft = Math.max(0, timeout - elapsed)
        remaining.value = timeLeft

        if (timeLeft <= 0) {
            // already expired
            opts.onLogout()
            return
        }

        // schedule warning
        const warnIn = Math.max(0, timeLeft - warningTime)
        warnTimer = setTimeout(() => {
            isWarning.value = true
            opts.onWarn?.(warningTime)
        }, warnIn)

        // schedule logout
        idleTimer = setTimeout(() => {
            clearTimers()
            opts.onLogout()
        }, timeLeft)
    }

    function onActivity() {
        updateLastActivity()
    }

    function addListeners() {
        const events = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll']
        events.forEach((ev) => window.addEventListener(ev, onActivity, { passive: true }))
        document.addEventListener('visibilitychange', () => {
            if (!document.hidden) updateLastActivity()
        })
        window.addEventListener('storage', handleStorageEvent)
    }

    function removeListeners() {
        const events = ['mousemove', 'keydown', 'click', 'touchstart', 'scroll']
        events.forEach((ev) => window.removeEventListener(ev, onActivity))
        window.removeEventListener('storage', handleStorageEvent)
        document.removeEventListener('visibilitychange', () => { })
        clearTimers()
    }

    onMounted(() => {
        // init last activity if missing
        if (!localStorage.getItem(STORAGE_KEY)) {
            localStorage.setItem(STORAGE_KEY, String(Date.now()))
        }
        addListeners()
        resetTimers()
    })

    onBeforeUnmount(() => {
        removeListeners()
    })

    // Expose manual controls
    return {
        isWarning,
        remaining,
        reset: updateLastActivity,
        stop: removeListeners,
        start: () => {
            if (!localStorage.getItem(STORAGE_KEY)) localStorage.setItem(STORAGE_KEY, String(Date.now()))
            addListeners()
            resetTimers()
        },
    }
}