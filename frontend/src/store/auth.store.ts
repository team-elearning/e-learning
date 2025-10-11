// src/store/auth.store.ts
import { defineStore } from 'pinia'
import router from '@/router'
// [REMOVE] , type AuthPayload
import { authService, type Role, type AuthUser } from '@/services/auth.service'

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
        // this.persist()
      }
      this.redirectByRole(user.role)
    },

    async loginWithGoogle() {
      const { token, user } = await authService.loginWithGoogle()
      this.token = token
      this.user = user
      localStorage.setItem('auth', JSON.stringify({ token, user }))
      // this.persist() // [ADD-OPTIONAL] có thể dùng helper thay vì setItem trực tiếp
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
      router.push('/')
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

    // Helper lưu/clear localStorage khi cập nhật user/token ngoài luồng login
    persist() {
      if (this.token && this.user) {
        localStorage.setItem('auth', JSON.stringify({ token: this.token, user: this.user }))
      } else {
        localStorage.removeItem('auth')
      }
    },

    // Dùng cho trang Profile để cập nhật hồ sơ người dùng
    async updateProfile(payload: Partial<AuthUser & { avatar?: string }>) {
      // Nếu service đã có API thật → gọi; nếu chưa có → merge local
      if (typeof authService.updateProfile === 'function') {
        const res = await authService.updateProfile(payload as any)
        this.user = res?.user ?? { ...(this.user as AuthUser), ...payload }
      } else {
        this.user = { ...(this.user as AuthUser), ...payload }
      }
      this.persist() // ADD
    },

    // [ADD] Dùng cho trang Đổi mật khẩu
    async changePassword(oldPassword: string, newPassword: string) {
      if (typeof authService.changePassword === 'function') {
        await authService.changePassword(oldPassword, newPassword)
      } else {
        return // mock local nếu chưa có API
      }
    },
  },
})
