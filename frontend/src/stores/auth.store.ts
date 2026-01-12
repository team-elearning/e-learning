import { defineStore } from 'pinia'
import { Role } from '@/shared/constants/roles'
import { loginApi, googleLoginApi } from '@/modules/auth/api/auth.api'
import { normalizeRole } from '@/modules/auth/api/role-map'
import { registerApi, type RegisterBody } from '@/modules/auth/api/register.api'


const USER_KEY = 'auth_user'
const TOKEN_KEY = 'access_token'

type AuthUser = {
    username: string
    email: string
    fullName: string
    role: Role
}

function loadUser(): AuthUser | null {
    const raw = localStorage.getItem(USER_KEY)
    if (!raw) return null
    try { return JSON.parse(raw) as AuthUser } catch { return null }
}

export const useAuthStore = defineStore('auth', {
    state: () => {
        const user = loadUser()
        return {
            token: localStorage.getItem(TOKEN_KEY) as string | null,
            user,
            roles: user ? [user.role] : ([] as Role[]),
        }
    },
    getters: {
        isLoggedIn: (s) => !!s.token,
    },
    actions: {
        async login(identifier: string, password: string) {
            const res = await loginApi(identifier, password)
            const role = normalizeRole(res.user.role)

            const user: AuthUser = {
                username: res.user.username,
                email: res.user.email,
                fullName: res.user.full_name,
                role,
            }

            this.token = res.access
            this.user = user
            this.roles = [role]

            localStorage.setItem(TOKEN_KEY, res.access)
            localStorage.setItem(USER_KEY, JSON.stringify(user))

            return role
        },
        async loginWithGoogle(token: string) {
            const res = await googleLoginApi(token)
            const role = normalizeRole(res.user.role)

            const user: AuthUser = {
                username: res.user.username,
                email: res.user.email,
                fullName: res.user.full_name,
                role,
            }

            this.token = res.access
            this.user = user
            this.roles = [role]

            localStorage.setItem(TOKEN_KEY, res.access)
            localStorage.setItem(USER_KEY, JSON.stringify(user))

            return role
        },
        // ... (rest of actions)
        async register(payload: RegisterBody) {
            // API register thường không auto-login, nên chỉ gọi và return
            return await registerApi(payload)
        },
        logout() {
            this.token = null
            this.user = null
            this.roles = []
            localStorage.removeItem(TOKEN_KEY)
            localStorage.removeItem(USER_KEY)
        },
    },
})
