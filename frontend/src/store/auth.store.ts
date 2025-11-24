// src/store/auth.store.ts
import { defineStore } from 'pinia'
import router from '@/router'
import { authService, type Role, type AuthUser } from '@/services/auth.service'
import { ElMessage } from 'element-plus'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: null as string | null,
    user: null as AuthUser | null,
  }),

  // Getters phục vụ Navbar/Profile
  getters: {
    // [ADD]
    isAuthenticated: (state) => !!state.token, // [ADD]
    role: (state): Role | undefined => state.user?.role, // [ADD]
    // ADDluôn có ảnh fallback để Navbar không bị null
    avatar: (state): string => state.user?.avatar || 'https://i.pravatar.cc/80?img=10',
  }, // [ADD]

  actions: {
    async login(identifier: string, password: string, remember = true) {
      try {
        const { token, user } = await authService.login(identifier, password)

        this.token = token
        this.user = user

        const data = JSON.stringify({ token, user })

        if (remember) {
          localStorage.setItem('auth', data)
          localStorage.setItem('accessToken', token)
        } else {
          sessionStorage.setItem('accessToken', token)
        }

        this.redirectByRole(user.role)
        return { token, user }
      } catch (err: any) {
        ElMessage.error(err?.message || 'Đăng nhập thất bại')
        throw err
      }
    },


    // async loginWithGoogle() {
    //   const { token, user } = await authService.loginWithGoogle()
    //   this.token = token
    //   this.user = user
    //   localStorage.setItem('auth', JSON.stringify({ token, user }))
    //   // this.persist() // [ADD-OPTIONAL]
    //   this.redirectByRole(user.role)
    // },

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
      localStorage.removeItem('accessToken')
      sessionStorage.removeItem('accessToken')

      router.push('/')
    },

    redirectByRole(role: Role) {
      if (role === 'admin') {
        router.push('/admin/dashboard')
      } else if (role === 'instructor') {
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
      const prev = this.user // [SAFE] giữ lại user cũ
      if (typeof authService.updateProfile === 'function') {
        const res = await authService.updateProfile(payload as any)
        // [SAFE] Không cho mock service ghi đè id/role cũ
        const next = res?.user ?? { ...(prev as AuthUser), ...payload }
        this.user = {
          ...(prev as AuthUser),
          ...next,
          id: prev?.id ?? next.id, // [SAFE]
          role: prev?.role ?? next.role, // [SAFE]
        }
      } else {
        this.user = { ...(prev as AuthUser), ...payload } // giữ nguyên cách cũ
      }
      this.persist() // [ADD]
    },

    // trang quên đổi mật khẩu
    async forgotPassword(email: string) {
      await authService.forgotPassword(email)
    },
    // trang reset mật khẩu
    async resetPassword(uid: string, token: string, newPassword: string) {
      await authService.resetPassword(uid, token, newPassword)
    },

    // [ADD] Dùng cho trang Đổi mật khẩu
    async changePassword(oldPassword: string, newPassword: string) {
      if (typeof authService.changePassword === 'function') {
        await authService.changePassword(oldPassword, newPassword)
      } else {
        return // mock local nếu chưa có API
      }
    },

    // Khởi tạo nhanh khi app load
    async init() {
      this.hydrateFromStorage()

      if (!this.token) {
        router.push('/auth/login')
        return
      }

      // đồng bộ hồ sơ mới nhất
      try {
        const profile = await authService.getProfile()
        this.user = {
          ...(this.user as AuthUser),
          ...profile,
          id: this.user?.id ?? profile.id,
          role: this.user?.role ?? profile.role,
        }
        this.persist()
      } catch (error) {
        // nếu token hết hạn, logout sẽ được interceptor xử lý
        console.error('Failed to fetch profile', error)
      }
    },

    // (Tùy chọn) Cập nhật avatar ngay để UI mượt hơn (optimistic)
    setAvatar(url: string) {
      // [ADD]
      if (this.user) {
        this.user = { ...this.user, avatar: url }
        this.persist()
      }
    },

    // Đồng bộ hồ sơ (dùng ở navbar)
    async refreshProfile() {
      if (!this.token) return
      try {
        const profile = await authService.getProfile()
        this.user = {
          ...(this.user as AuthUser),
          ...profile,
          id: this.user?.id ?? profile.id,
          role: this.user?.role ?? profile.role,
        }
        this.persist()
      } catch (error) {
        console.warn('Không thể đồng bộ hồ sơ', error)
      }
    },
  },
})
