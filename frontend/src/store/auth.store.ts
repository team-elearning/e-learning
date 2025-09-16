// src/store/auth.store.ts
import { defineStore } from 'pinia'
import router from '@/router'
import { authService, type Role, type AuthUser, type AuthPayload } from '@/services/auth.service'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        token: null as string | null,
        user: null as AuthUser | null,
    }),

    actions: {
        async login(email: string, password: string, remember = true) {
            const { token, user } = await authService.login(email, password)
            this.token = token
            this.user = user
            if (remember) {
                localStorage.setItem('auth', JSON.stringify({ token, user }))
            }
            this.redirectByRole(user.role)
        },

        async loginWithGoogle() {
            const { token, user } = await authService.loginWithGoogle()
            this.token = token
            this.user = user
            localStorage.setItem('auth', JSON.stringify({ token, user }))
            this.redirectByRole(user.role)
        },

        hydrateFromStorage() {
            const raw = localStorage.getItem('auth')
            if (raw) {
                const parsed = JSON.parse(raw) as { token: string; user: AuthUser }
                this.token = parsed.token
                this.user = parsed.user
            }
        },

        logout() {
            this.token = null
            this.user = null
            localStorage.removeItem('auth')
            router.push('/auth/login')
        },

        redirectByRole(role: Role) {
            if (role === 'admin') {
                router.push('/admin/dashboard')
            } else if (role === 'teacher') {
                router.push('/teacher/dashboard')
            } else {
                router.push('/student/dashboard')
            }
        },
    },
})
