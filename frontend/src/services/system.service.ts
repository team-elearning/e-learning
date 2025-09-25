// src/services/system.service.ts
import api from '@/config/axios'

export type ID = string | number
const USE_MOCK = true

export type LogLevel = 'info' | 'warn' | 'error'
export type Schedule = 'hourly' | 'daily' | 'weekly'

export interface BrandConfig {
    siteName: string
    logoUrl?: string
    language: string
    timezone: string
    currency: 'VND'
}

export interface DomainEmailConfig {
    domain: string
    forceHttps: boolean
    hsts: boolean
    smtp: {
        host: string
        port: number
        username: string
        // password không trả xuống FE, chỉ báo đang được mask
        passwordMasked: boolean
        senderName: string
        fromEmail: string
    }
    dmarc?: { status: 'pass' | 'fail' | 'unknown' }
    spf?: { status: 'pass' | 'fail' | 'unknown' }
    dkim?: { status: 'pass' | 'fail' | 'unknown' }
}

export interface AuthSessionConfig {
    idleTimeoutMin: number
    maxSessionHours: number
    rememberMeDays: number
    ssoGoogleEnabled: boolean
    googleClientId?: string
    twoFAEnforce: {
        admin: boolean
        teacher: boolean
    }
    passwordPolicy: {
        minLength: number
        requireNumbers: boolean
        requireSymbols: boolean
    }
    singleDeviceOnly: boolean
}

export interface BackupConfig {
    schedule: Schedule
    retentionDays: number
    rpoMinutes: number
    rtoMinutes: number
    encrypted: boolean
}

export interface MaintenanceConfig {
    enabled: boolean
    window: {
        dayOfWeek: number | null // 0..6 (Mon..Sun) tuỳ chuẩn bạn chọn
        start: string | null // "HH:mm"
        end: string | null   // "HH:mm"
    }
}

export interface IntegrationsConfig {
    payments: { momo: boolean; vnpay: boolean; qr: boolean; bank: boolean }
    analytics: { ga4MeasurementId?: string }
    zoom: { enabled: boolean }
    storage: { provider: 'local' | 's3'; bucket?: string; region?: string }
}

export interface LoggingConfig {
    level: LogLevel
    retentionDays: number
    traceIdEnabled: boolean
}

export interface SystemConfig {
    brand: BrandConfig
    domainEmail: DomainEmailConfig
    authSession: AuthSessionConfig
    backup: BackupConfig
    maintenance: MaintenanceConfig
    integrations: IntegrationsConfig
    logging: LoggingConfig
    version: number
    updatedBy: string
    updatedAt: string
}

export interface BackupItem {
    id: string
    createdAt: string
    sizeMB: number
    notes?: string
}

export interface ConfigAuditItem {
    id: string
    version: number
    key: string
    actor: string
    at: string
    note?: string
}

export const systemService = {
    async getConfig(): Promise<SystemConfig> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/system/config')
            return data
        }
        return {
            brand: {
                siteName: 'School LMS',
                language: 'vi',
                timezone: 'Asia/Bangkok',
                currency: 'VND',
                logoUrl: '',
            },
            domainEmail: {
                domain: 'lms.example.com',
                forceHttps: true,
                hsts: true,
                smtp: {
                    host: 'smtp.example.com',
                    port: 587,
                    username: 'no-reply@example.com',
                    passwordMasked: true,
                    senderName: 'School LMS',
                    fromEmail: 'no-reply@example.com',
                },
                dmarc: { status: 'pass' },
                spf: { status: 'pass' },
                dkim: { status: 'pass' },
            },
            authSession: {
                idleTimeoutMin: 30,
                maxSessionHours: 24,
                rememberMeDays: 14,
                ssoGoogleEnabled: true,
                googleClientId: 'GOOGLE_CLIENT_ID',
                twoFAEnforce: { admin: true, teacher: false },
                passwordPolicy: { minLength: 8, requireNumbers: true, requireSymbols: true },
                singleDeviceOnly: true,
            },
            backup: {
                schedule: 'daily',
                retentionDays: 30,
                rpoMinutes: 15,
                rtoMinutes: 120,
                encrypted: true,
            },
            maintenance: {
                enabled: false,
                window: { dayOfWeek: 0, start: '01:00', end: '03:00' },
            },
            integrations: {
                payments: { momo: true, vnpay: true, qr: true, bank: true },
                analytics: { ga4MeasurementId: 'G-XXXXXXX' },
                zoom: { enabled: true },
                storage: { provider: 's3', bucket: 'lms-bucket', region: 'ap-southeast-1' },
            },
            logging: {
                level: 'info',
                retentionDays: 90,
                traceIdEnabled: true,
            },
            version: 12,
            updatedBy: 'admin@yourorg',
            updatedAt: new Date().toISOString(),
        }
    },

    async updateConfig(payload: Partial<SystemConfig>) {
        if (!USE_MOCK) return api.put('/admin/system/config', payload)
        return Promise.resolve({ ok: true, version: (payload as any)?.version ?? 13 })
    },

    async sendTestEmail(to: string) {
        if (!USE_MOCK) return api.post('/admin/system/email/test', { to })
        return Promise.resolve({ ok: true, message: `Đã gửi test tới ${to} (mock)` })
    },

    async listBackups(): Promise<BackupItem[]> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/system/backup')
            return data
        }
        return Array.from({ length: 8 }).map((_, i) => ({
            id: `bk-${1000 + i}`,
            createdAt: new Date(Date.now() - i * 864e5).toISOString(),
            sizeMB: 320 + i * 12,
            notes: i === 0 ? 'pre-patch v1.12' : undefined,
        }))
    },

    async createBackup(notes?: string) {
        if (!USE_MOCK) return api.post('/admin/system/backup', { notes })
        return Promise.resolve({ ok: true, id: `bk-${Math.floor(Math.random() * 99999)}` })
    },

    async restoreBackup(id: string) {
        if (!USE_MOCK) return api.post(`/admin/system/restore`, { id })
        return Promise.resolve({ ok: true })
    },

    async listConfigAudit(): Promise<ConfigAuditItem[]> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/system/config/audits')
            return data
        }
        return Array.from({ length: 10 }).map((_, i) => ({
            id: `ca-${i + 1}`,
            version: 12 - i,
            key: ['brand', 'domainEmail', 'authSession', 'backup', 'integrations', 'logging'][i % 6],
            actor: i % 2 ? 'ops@yourorg' : 'admin@yourorg',
            at: new Date(Date.now() - i * 36e5).toISOString(),
            note: i === 0 ? 'Change idle timeout 30→60' : undefined,
        }))
    },
}
