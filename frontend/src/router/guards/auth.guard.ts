import type { NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth.store'
import { homePathByRole } from '@/shared/utils/role-home'

export function authGuard(to: RouteLocationNormalized, _from: RouteLocationNormalized, next: NavigationGuardNext) {
    const auth = useAuthStore()

    // Đã login mà cố vào trang login -> chuyển về trang role tương ứng
    if (to.name === 'login' && auth.isLoggedIn) {
        const role = auth.roles[0]
        if (role) {
            return next(homePathByRole(role))
        }
    }

    if (to.meta.requiresAuth && !auth.isLoggedIn) {
        return next({ name: 'login' })
    }
    if (to.meta.requiresAuth && auth.isLoggedIn && auth.roles.length === 0) {
        return next({ name: 'login' })
    }


    next()
}
