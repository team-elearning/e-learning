import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'

export function roleGuard(to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) {
    const auth = useAuthStore()
    const roles = to.meta.roles as string[] | undefined
    if (!roles?.length) return next()

    const ok = roles.some(r => auth.roles.includes(r as any))
    return ok ? next() : next({ name: 'forbidden' })
}
