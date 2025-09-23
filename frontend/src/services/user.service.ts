// src/services/user.service.ts
import api from '@/config/axios'

export type ID = string | number
export type Role = 'admin' | 'teacher' | 'student'
export type UserStatus = 'active' | 'locked' | 'banned' | 'pending_approval'

export interface User {
    id: ID
    name: string
    username: string
    email: string
    phone?: string
    avatar?: string
    role: Role
    status: UserStatus
    lastLoginAt?: string
    createdAt: string
}

export interface UserDetail extends User {
    emailVerified?: boolean
    phoneVerified?: boolean
    bio?: string
    tags?: string[]
    notes?: string
    language?: 'vi' | 'en'
    timezone?: string
    address?: { country?: string; city?: string }

    updatedAt: string

    // security
    mfaEnabled?: boolean
    backupCodesLeft?: number
    passwordUpdatedAt?: string
    failedAttempts?: number
    lockedUntil?: string | null
    banReason?: string | null
    providers?: ('password' | 'google')[]
    ipAllowlist?: string[]

    // role-specific (optional)
    subjects?: string[]
    grades?: number[]
    totalCourses?: number
    pendingApprovalsCount?: number
    rating?: number

    grade?: number
    classCode?: string
    enrolledCount?: number
    certificatesCount?: number
    parentConsent?: boolean
    guardians?: { name: string; phone?: string; email?: string }[]
}

export interface PageParams {
    q?: string
    role?: Role
    status?: UserStatus
    from?: string
    to?: string
    page?: number
    pageSize?: number
    sortBy?: string
    sortDir?: 'ascending' | 'descending'
}
export interface PageResult<T> { items: T[]; total: number }

export interface SessionRow {
    sessionId: string
    device: string
    ip: string
    location?: string
    createdAt: string
    lastActiveAt: string
}

export interface LoginEvent {
    time: string
    result: 'success' | 'fail'
    ip: string
    device?: string
    reason?: string
    userAgent?: string
}

export interface ActivityLog {
    time: string
    action: string
    entity?: string
    by?: string
    status: 'ok' | 'error'
    meta?: Record<string, any>
}

export interface Transaction {
    id: string
    courseTitle: string
    amount: number
    gateway: 'Momo' | 'VNPay' | 'QR' | 'Bank'
    status: 'Pending' | 'Processing' | 'Succeeded' | 'Failed' | 'Refunded' | 'Disputed'
    time: string
}

export interface NoteItem {
    id: string
    author?: string
    note: string
    time: string
}

const USE_MOCK = true

export const userService = {
    // ==== LIST (đã có ở trước) ====
    async list(params: PageParams): Promise<PageResult<User>> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/users', { params })
            return data
        }
        const total = 128
        const size = params.pageSize ?? 20
        const page = params.page ?? 1
        const roles: Role[] = ['admin', 'teacher', 'student']
        const statuses: UserStatus[] = ['active', 'locked', 'banned', 'pending_approval']
        const items: User[] = Array.from({ length: size }).map((_, i) => {
            const id = (page - 1) * size + i + 1
            return {
                id,
                name: `User ${id}`,
                username: `user${id}`,
                email: `user${id}@example.com`,
                role: roles[id % 3],
                status: statuses[id % 4],
                lastLoginAt: new Date(Date.now() - id * 36e5).toISOString(),
                createdAt: new Date(Date.now() - id * 864e5).toISOString(),
            }
        })
        return { items, total }
    },

    // ==== DETAIL ====
    async detail(id: ID): Promise<UserDetail> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/admin/users/${id}`)
            return data
        }
        const now = new Date()
        return {
            id,
            name: `User ${id}`,
            username: `user${id}`,
            email: `user${id}@example.com`,
            emailVerified: id % 2 === 0,
            phone: '0901234567',
            role: (['admin', 'teacher', 'student'] as Role[])[Number(id) % 3],
            status: (['active', 'locked', 'banned', 'pending_approval'] as UserStatus[])[Number(id) % 4],
            createdAt: new Date(now.getTime() - 30 * 864e5).toISOString(),
            updatedAt: now.toISOString(),
            lastLoginAt: new Date(now.getTime() - 5 * 36e5).toISOString(),
            language: 'vi',
            timezone: 'Asia/Bangkok',
            bio: 'Đây là bio mẫu.',
            mfaEnabled: Number(id) % 2 === 0,
            passwordUpdatedAt: new Date(now.getTime() - 10 * 864e5).toISOString(),
            failedAttempts: 1,
            providers: ['password', 'google'],
            address: { city: 'Hà Nội', country: 'VN' },
        }
    },

    // ==== CRUD ====
    create(payload: Partial<User>) { return api.post('/admin/users', payload) },
    update(id: ID, payload: Partial<UserDetail>) { return api.put(`/admin/users/${id}`, payload) },

    // ==== ROLE & SECURITY ====
    changeRole(id: ID, role: Role) { return api.post(`/admin/users/${id}/role`, { role }) },
    resetPassword(id: ID) { return api.post(`/admin/users/${id}/reset-password`) },
    lock(id: ID) { return api.post(`/admin/users/${id}/lock`) },
    unlock(id: ID) { return api.post(`/admin/users/${id}/unlock`) },
    ban(id: ID) { return api.post(`/admin/users/${id}/ban`) },

    // ==== SESSIONS ====
    async sessions(id: ID): Promise<SessionRow[]> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/admin/users/${id}/sessions`)
            return data
        }
        const now = Date.now()
        return Array.from({ length: 5 }).map((_, i) => ({
            sessionId: `S_${id}_${i}`,
            device: i % 2 ? 'Windows • Chrome' : 'Android • Chrome',
            ip: `192.168.1.${i + 2}`,
            location: 'VN',
            createdAt: new Date(now - (i + 3) * 864e5).toISOString(),
            lastActiveAt: new Date(now - i * 36e5).toISOString(),
        }))
    },
    revokeSession(id: ID, sid: string) { return api.delete(`/admin/users/${id}/sessions/${sid}`) },
    revokeAll(id: ID) { return api.delete(`/admin/users/${id}/sessions`) },

    // ==== LOGINS ====
    async loginHistory(id: ID, params: { page?: number; pageSize?: number; from?: string; to?: string; result?: 'success' | 'fail' }): Promise<PageResult<LoginEvent>> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/admin/users/${id}/logins`, { params })
            return data
        }
        const total = 42
        const size = params.pageSize ?? 20
        const page = params.page ?? 1
        const items: LoginEvent[] = Array.from({ length: size }).map((_, i) => {
            const idx = (page - 1) * size + i
            return {
                time: new Date(Date.now() - (idx + 2) * 36e5).toISOString(),
                result: (idx % 5 === 0 ? 'fail' : 'success'),
                ip: `10.0.0.${(idx % 200) + 1}`,
                device: idx % 2 ? 'iOS • Safari' : 'Windows • Chrome',
                reason: idx % 5 === 0 ? 'wrong_password' : undefined,
            }
        })
        return { items, total }
    },

    // ==== ACTIVITY ====
    async activity(id: ID, params: { page?: number; pageSize?: number }): Promise<PageResult<ActivityLog>> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/admin/users/${id}/activity`, { params })
            return data
        }
        const total = 35
        const size = params.pageSize ?? 20
        const page = params.page ?? 1
        const items: ActivityLog[] = Array.from({ length: size }).map((_, i) => {
            const idx = (page - 1) * size + i
            return {
                time: new Date(Date.now() - (idx + 1) * 6e5).toISOString(),
                action: idx % 2 ? 'course.update' : 'auth.login',
                entity: idx % 2 ? `course#${100 + idx}` : undefined,
                status: idx % 7 === 0 ? 'error' : 'ok',
                meta: { ip: `10.0.0.${idx % 200}` },
            }
        })
        return { items, total }
    },

    // ==== TRANSACTIONS (by user) ====
    async transactionsByUser(id: ID, params: { page?: number; pageSize?: number }): Promise<PageResult<Transaction>> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/admin/users/${id}/transactions`, { params })
            return data
        }
        const total = 18
        const size = params.pageSize ?? 20
        const page = params.page ?? 1
        const items: Transaction[] = Array.from({ length: size }).map((_, i) => {
            const idx = (page - 1) * size + i
            return {
                id: `TX${id}-${idx}`,
                courseTitle: `Khoá học #${200 + idx}`,
                amount: (idx % 5 + 1) * 99000,
                gateway: (['VNPay', 'Momo', 'QR', 'Bank'] as Transaction['gateway'][])[idx % 4],
                status: (['Succeeded', 'Refunded', 'Failed', 'Processing'] as Transaction['status'][])[idx % 4],
                time: new Date(Date.now() - (idx + 1) * 864e5).toISOString(),
            }
        })
        return { items, total }
    },

    // ==== NOTES ====
    async listNotes(id: ID): Promise<NoteItem[]> {
        if (!USE_MOCK) { const { data } = await api.get(`/admin/users/${id}/notes`); return data }
        return [
            { id: 'n1', author: 'Admin', note: 'HS học chăm, tiến bộ tốt.', time: new Date(Date.now() - 864e5).toISOString() },
            { id: 'n2', author: 'QA', note: 'Yêu cầu xác minh số điện thoại.', time: new Date(Date.now() - 2 * 864e5).toISOString() },
        ]
    },
    async addNote(id: ID, note: string) {
        if (!USE_MOCK) { return api.post(`/admin/users/${id}/notes`, { note }) }
        return { ok: true }
    },
    // ==== BULK ACTIONS ====
    bulkChangeRole(ids: ID[], role: Role) {
        if (!USE_MOCK) return api.post('/admin/users/bulk/role', { ids, role })
        return Promise.resolve({ ok: true })
    },
    bulkLock(ids: ID[]) {
        if (!USE_MOCK) return api.post('/admin/users/bulk/lock', { ids })
        return Promise.resolve({ ok: true })
    },
    bulkUnlock(ids: ID[]) {
        if (!USE_MOCK) return api.post('/admin/users/bulk/unlock', { ids })
        return Promise.resolve({ ok: true })
    },
    bulkBan(ids: ID[]) {
        if (!USE_MOCK) return api.post('/admin/users/bulk/ban', { ids })
        return Promise.resolve({ ok: true })
    },

    // ==== EXPORT CSV ====
    async exportCsv(params: PageParams): Promise<Blob> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/users/export', {
                params,
                responseType: 'blob',
            })
            return data
        }
        // MOCK CSV cho môi trường dev
        const headers = [
            'id', 'name', 'username', 'email', 'role', 'status', 'createdAt', 'lastLoginAt'
        ]
        const size = params.pageSize ?? 50
        const page = params.page ?? 1
        const roles: Role[] = ['admin', 'teacher', 'student']
        const statuses: UserStatus[] = ['active', 'locked', 'banned', 'pending_approval']

        const rows = Array.from({ length: size }).map((_, i) => {
            const id = (page - 1) * size + i + 1
            return [
                id,
                `User ${id}`,
                `user${id}`,
                `user${id}@example.com`,
                roles[id % 3],
                statuses[id % 4],
                new Date(Date.now() - id * 864e5).toISOString(),
                new Date(Date.now() - id * 36e5).toISOString(),
            ]
        })

        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n')
        return new Blob([csv], { type: 'text/csv;charset=utf-8' })
    },

}
