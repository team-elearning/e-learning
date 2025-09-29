// src/services/security.service.ts
import api from '@/config/axios'

export type ID = string | number
const USE_MOCK = true

export interface SecurityPolicy {
    twoFA: { enforceAdmin: boolean; enforceTeacher: boolean }
    rateLimit: { loginFailures: number; windowMin: number }
    lockout: { attempts: number; lockMinutes: number; banStrikes: number }
    rbacNote?: string // mô tả ma trận quyền (server giữ thật)
}

export interface IpAllowItem {
    id: string
    cidr: string
    note?: string
    active: boolean
    createdBy: string
    createdAt: string
}

export interface SessionItem {
    jti: string
    userId: ID
    userName: string
    role: 'admin' | 'teacher' | 'student'
    ip: string
    userAgent: string
    device?: string
    location?: string
    createdAt: string
    lastActiveAt: string
}

export interface CertStatus {
    issuer: string
    validFrom: string
    validTo: string
    daysRemaining: number
    autoRenew: boolean
    grade?: 'A+' | 'A' | 'B' | 'C'
}

export interface AlertPolicy {
    cpuThreshold: number
    errorRateThreshold: number
    channels: { email: boolean; sms: boolean }
    onCall: string
}

export const securityService = {
    async getPolicy(): Promise<SecurityPolicy> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/security/policy')
            return data
        }
        return {
            twoFA: { enforceAdmin: true, enforceTeacher: false },
            rateLimit: { loginFailures: 5, windowMin: 10 },
            lockout: { attempts: 5, lockMinutes: 30, banStrikes: 5 },
            rbacNote: 'RBAC được quản trị ở backend; FE chỉ hiển thị.',
        }
    },
    async updatePolicy(payload: Partial<SecurityPolicy>) {
        if (!USE_MOCK) return api.put('/admin/security/policy', payload)
        return Promise.resolve({ ok: true })
    },

    async listIpAllow(): Promise<IpAllowItem[]> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/security/ip-allowlist')
            return data
        }
        return [
            { id: 'ip1', cidr: '203.0.113.0/24', note: 'Văn phòng', active: true, createdBy: 'admin', createdAt: new Date().toISOString() },
            { id: 'ip2', cidr: '198.51.100.10/32', note: 'VPN lead', active: true, createdBy: 'secops', createdAt: new Date(Date.now() - 864e5).toISOString() },
        ]
    },
    async addIpAllow(cidr: string, note?: string) {
        if (!USE_MOCK) return api.post('/admin/security/ip-allowlist', { cidr, note })
        return Promise.resolve({ ok: true, id: `ip-${Math.random()}` })
    },
    async removeIpAllow(id: string) {
        if (!USE_MOCK) return api.delete(`/admin/security/ip-allowlist/${id}`)
        return Promise.resolve({ ok: true })
    },

    async listSessions(userId?: ID): Promise<SessionItem[]> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/security/sessions', { params: { userId } })
            return data
        }
        return Array.from({ length: 12 }).map((_, i) => ({
            jti: `jti-${i}`,
            userId: (i % 8) + 1,
            userName: `User ${(i % 8) + 1}`,
            role: (['admin', 'teacher', 'student'] as const)[i % 3],
            ip: `203.0.113.${50 + i}`,
            userAgent: 'Chrome on Windows',
            device: 'PC',
            location: 'VN',
            createdAt: new Date(Date.now() - i * 36e5).toISOString(),
            lastActiveAt: new Date(Date.now() - i * 12e5).toISOString(),
        }))
    },
    async revokeSession(jti: string) {
        if (!USE_MOCK) return api.delete(`/admin/security/sessions/${jti}`)
        return Promise.resolve({ ok: true })
    },

    async getCertStatus(): Promise<CertStatus> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/security/cert')
            return data
        }
        return {
            issuer: "Let's Encrypt",
            validFrom: new Date(Date.now() - 20 * 864e5).toISOString(),
            validTo: new Date(Date.now() + 40 * 864e5).toISOString(),
            daysRemaining: 40,
            autoRenew: true,
            grade: 'A',
        }
    },
    async renewCert() {
        if (!USE_MOCK) return api.post('/admin/security/cert/renew')
        return Promise.resolve({ ok: true })
    },

    async getAlertPolicy(): Promise<AlertPolicy> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/security/alerts')
            return data
        }
        return { cpuThreshold: 90, errorRateThreshold: 2, channels: { email: true, sms: true }, onCall: 'SecOps' }
    },
    async updateAlertPolicy(payload: Partial<AlertPolicy>) {
        if (!USE_MOCK) return api.put('/admin/security/alerts', payload)
        return Promise.resolve({ ok: true })
    },
    async alertTest() {
        if (!USE_MOCK) return api.post('/admin/security/alert-test')
        return Promise.resolve({ ok: true })
    },
}
