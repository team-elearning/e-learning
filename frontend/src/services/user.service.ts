// src/services/user.service.ts
import api from '@/config/axios'

export type ID = string | number
export type Role = 'admin' | 'instructor' | 'student'
export type UserStatus = 'active' | 'locked' | 'banned' | 'inactive'

export interface User {
    id: ID
    username: string
    name?: string
    email: string
    phone?: string | null
    avatar?: string
    role: Role
    // backend có "is_active" -> map sang status
    status: UserStatus // 'active' | 'locked' | 'banned' | 'inactive'
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

    updatedAt?: string

    // security / extra
    mfaEnabled?: boolean
    providers?: ('password' | 'google')[]
    // role-specific optional fields:
    subjects?: string[]
    grades?: number[]
    totalCourses?: number
    rating?: number
    // other optional fields
    isStaff?: boolean
    isActive?: boolean
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

export interface LoginEvent { time: string; result: 'success' | 'fail'; ip: string; device?: string; reason?: string; userAgent?: string }
export interface ActivityLog { time: string; action: string; entity?: string; by?: string; status: 'ok' | 'error'; meta?: Record<string, any> }
export interface Transaction { id: string; courseTitle: string; amount: number; gateway: 'Momo' | 'VNPay' | 'QR' | 'Bank'; status: 'Pending' | 'Processing' | 'Succeeded' | 'Failed' | 'Refunded' | 'Disputed'; time: string }
export interface NoteItem { id: string; author?: string; note: string; time: string }

const USE_MOCK = false // chuyển sang dùng API thật

function mapServerToUser(s: any): User {
    // server sample fields: id, username, email, created_on, updated_on, phone, role, is_active
    const status: User['status'] = s.is_active === false ? 'inactive' : 'active'
    return {
        id: s.id,
        username: s.username,
        name: s.username ?? s.name ?? undefined, // giữ username làm name nếu backend không trả name
        email: s.email ?? '',
        phone: s.phone ?? null,
        avatar: s.avatar ?? undefined,
        role: (s.role as Role) ?? 'student',
        status,
        lastLoginAt: s.last_login_at ?? s.lastLoginAt ?? undefined,
        createdAt: s.created_on ?? s.createdAt ?? '',
    }
}

export const userService = {
    // LIST: call /api/account/admin/users/
    async list(params: PageParams): Promise<PageResult<User>> {
        if (!USE_MOCK) {
            const { data } = await api.get('/account/admin/users/', { params })
            // backend may return array or paginated object { results, count }
            let itemsRaw: any[] = []
            let total = 0
            if (Array.isArray(data)) {
                itemsRaw = data
                total = data.length
            } else if (Array.isArray(data.results)) {
                itemsRaw = data.results
                total = Number(data.count ?? data.total ?? itemsRaw.length)
            } else if (Array.isArray(data.items)) {
                itemsRaw = data.items
                total = Number(data.total ?? itemsRaw.length)
            } else {
                // fallback try to treat data as array-like
                itemsRaw = []
                total = 0
            }
            const items = itemsRaw.map(mapServerToUser)
            return { items, total }
        }

        // MOCK (unchanged)
        const total = 128
        const size = params.pageSize ?? 20
        const page = params.page ?? 1
        const roles: Role[] = ['admin', 'instructor', 'student']
        const statuses: UserStatus[] = ['active', 'locked', 'banned', 'inactive']
        const items: User[] = Array.from({ length: size }).map((_, i) => {
            const id = (page - 1) * size + i + 1
            return {
                id,
                username: `user${id}`,
                name: `User ${id}`,
                email: `user${id}@example.com`,
                role: roles[id % 3],
                status: statuses[id % 4] as any,
                lastLoginAt: new Date(Date.now() - id * 36e5).toISOString(),
                createdAt: new Date(Date.now() - id * 864e5).toISOString(),
            }
        })
        return { items, total }
    },

    // DETAIL: call /api/account/admin/users/:id/
    async detail(id: ID): Promise<UserDetail> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/account/admin/users/${id}/`)
            const base = mapServerToUser(data)
            const detail: UserDetail = {
                ...base,
                emailVerified: data.email_verified ?? undefined,
                phoneVerified: data.phone_verified ?? undefined,
                bio: data.bio ?? undefined,
                tags: data.tags ?? undefined,
                notes: data.notes ?? undefined,
                language: data.language ?? undefined,
                timezone: data.timezone ?? undefined,
                address: data.address ?? undefined,
                updatedAt: data.updated_on ?? data.updatedAt ?? undefined,
                mfaEnabled: data.mfa_enabled ?? undefined,
                providers: data.providers ?? undefined,
                isStaff: data.is_staff ?? undefined,
                isActive: data.is_active ?? undefined,
            }
            return detail
        }

        // MOCK fallback
        const now = new Date()
        return {
            id,
            username: `user${id}`,
            name: `User ${id}`,
            email: `user${id}@example.com`,
            emailVerified: Number(id) % 2 === 0,
            phone: '0901234567',
            role: (['admin', 'instructor', 'student'] as Role[])[Number(id) % 3],
            status: (['active', 'locked', 'banned', 'pending_approval'] as UserStatus[])[Number(id) % 4],
            createdAt: new Date(now.getTime() - 30 * 864e5).toISOString(),
            updatedAt: now.toISOString(),
            lastLoginAt: new Date(now.getTime() - 5 * 36e5).toISOString(),
            language: 'vi',
            timezone: 'Asia/Bangkok',
            bio: 'Đây là bio mẫu.',
            mfaEnabled: Number(id) % 2 === 0,
            providers: ['password', 'google'],
            address: { city: 'Hà Nội', country: 'VN' },
        }
    },

    // CRUD
    create(payload: { username: string; email: string; password: string; role: Role }) {
        return api.post('/account/admin/users/', payload)
    },
    update(id: ID, payload: { username: string; email: string; phone?: string | null; name?: string }) {
        return api.patch(`/account/admin/users/${id}/`, payload)
    },

    delete(id: ID) {
        return api.delete(`/account/admin/users/${id}/`)
    },
    async deleteAccount(id: ID): Promise<void> {
        await api.delete(`/account/admin/users/${id}/`)
    },

    // PASSWORD MANAGEMENT
    setPassword(id: ID, payload: { new_password: string }) {
        return api.post(`/account/admin/password/set/${id}/`, payload)
    },

    // ROLE & SECURITY (adjust endpoints if backend different)
    // changeRole(id: ID, role: Role) { return api.post(`/account/admin/users/${id}/role/`, { role }) },
    // resetPassword(id: ID) { return api.post(`/account/admin/users/${id}/reset-password/`) },
    // lock(id: ID) { return api.post(`/account/admin/users/${id}/lock/`) },
    // unlock(id: ID) { return api.post(`/account/admin/users/${id}/unlock/`) },
    // ban(id: ID) { return api.post(`/account/admin/users/${id}/ban/`) },

    // SESSIONS
    async sessions(id: ID): Promise<SessionRow[]> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/account/admin/users/${id}/sessions/`)
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
    revokeSession(id: ID, sid: string) { return api.delete(`/account/admin/users/${id}/sessions/${sid}/`) },
    revokeAll(id: ID) { return api.delete(`/account/admin/users/${id}/sessions/`) },

    // other helpers same as before...
    async loginHistory(id: ID, params: { page?: number; pageSize?: number; from?: string; to?: string; result?: 'success' | 'fail' }): Promise<PageResult<LoginEvent>> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/account/admin/users/${id}/logins/`, { params })
            if (Array.isArray(data)) return { items: data, total: data.length }
            if (Array.isArray(data.results)) return { items: data.results, total: data.count ?? data.total ?? data.results.length }
            return { items: [], total: 0 }
        }
        // MOCK...
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

    // ...keep other mock implementations for transactions/notes/exportCsv if needed...
    async transactionsByUser(id: ID, params: { page?: number; pageSize?: number }): Promise<PageResult<Transaction>> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/account/admin/users/${id}/transactions/`, { params })
            if (Array.isArray(data)) return { items: data, total: data.length }
            return { items: data.items ?? [], total: data.total ?? 0 }
        }
        // MOCK fallback...
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

    async listNotes(id: ID): Promise<NoteItem[]> {
        if (!USE_MOCK) { const { data } = await api.get(`/account/admin/users/${id}/notes/`); return data }
        return [
            { id: 'n1', author: 'Admin', note: 'HS học chăm, tiến bộ tốt.', time: new Date(Date.now() - 864e5).toISOString() },
            { id: 'n2', author: 'QA', note: 'Yêu cầu xác minh số điện thoại.', time: new Date(Date.now() - 2 * 864e5).toISOString() },
        ]
    },
    async addNote(id: ID, note: string) {
        if (!USE_MOCK) { return api.post(`/account/admin/users/${id}/notes/`, { note }) }
        return { ok: true }
    },

    // bulk actions
    bulkChangeRole(ids: ID[], role: Role) { return api.post('/account/admin/users/bulk/role/', { ids, role }) },
    bulkLock(ids: ID[]) { return api.post('/account/admin/users/bulk/lock/', { ids }) },
    bulkUnlock(ids: ID[]) { return api.post('/account/admin/users/bulk/unlock/', { ids }) },
    bulkBan(ids: ID[]) { return api.post('/account/admin/users/bulk/ban/', { ids }) },

    async exportCsv(params: PageParams): Promise<Blob> {
        if (!USE_MOCK) {
            const { data } = await api.get('/account/admin/users/export/', { params, responseType: 'blob' })
            return data
        }
        // MOCK CSV...
        const headers = ['id', 'name', 'username', 'email', 'role', 'status', 'createdAt', 'lastLoginAt']
        const size = params.pageSize ?? 50
        const page = params.page ?? 1
        const roles: Role[] = ['admin', 'instructor', 'student']
        const statuses: UserStatus[] = ['active', 'locked', 'banned', 'inactive']
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
