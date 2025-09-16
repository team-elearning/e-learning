// src/services/auth.service.ts
export type Role = 'admin' | 'teacher' | 'student'

export interface AuthUser {
    id: number
    name: string
    email: string
    role: Role
}

export interface AuthPayload {
    token: string
    user: AuthUser
}

export const authService = {
    async login(email: string, password: string): Promise<AuthPayload> {
        if (!email || !password) throw new Error('Thiếu thông tin đăng nhập')

        const role: Role = email.includes('admin')
            ? 'admin'
            : email.includes('teacher')
                ? 'teacher'
                : 'student'

        return {
            token: 'mock-token-' + Date.now(),
            user: {
                id: 1,
                name: 'User ' + role,
                email,
                role,
            },
        }
    },

    async loginWithGoogle(): Promise<AuthPayload> {
        return {
            token: 'mock-google-' + Date.now(),
            user: {
                id: 2,
                name: 'Google User',
                email: 'googleuser@example.com',
                role: 'student',
            },
        }
    },

    async register(payload: any): Promise<{ ok: boolean }> {
        // call API thật ở đây nếu có
        return { ok: true }
    },
}
