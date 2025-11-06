import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
    state: () => ({
        isAuthenticated: !!localStorage.getItem('accessToken'),
        user: null,
    }),
    actions: {
        login(token: string, user: any) {
            localStorage.setItem('accessToken', token)
            this.isAuthenticated = true
            this.user = user
        },
        logout() {
            localStorage.removeItem('accessToken')
            this.isAuthenticated = false
            this.user = null
            window.location.href = '/login'
        },
    },
})