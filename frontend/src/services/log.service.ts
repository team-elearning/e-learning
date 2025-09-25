// src/services/log.service.ts
import api from '@/config/axios'

export type ID = string | number
const USE_MOCK = true

export type LogResult = 'success' | 'failed'
export type TargetType = 'user' | 'course' | 'exam' | 'payment' | 'config' | 'system' | 'security'

export interface LogItem {
    id: string
    ts: string
    actorId?: ID
    actorName?: string
    actorRole?: 'admin' | 'teacher' | 'student' | 'system'
    action: string // ví dụ: user.create, course.publish, payment.refund, config.update...
    targetType?: TargetType
    targetId?: ID
    result: LogResult
    ip?: string
    userAgent?: string
    traceId?: string
    message?: string
    meta?: Record<string, any>
}

export interface LogQuery {
    q?: string
    role?: 'admin' | 'teacher' | 'student' | 'system'
    action?: string
    targetType?: TargetType
    targetId?: ID
    result?: LogResult
    ip?: string
    from?: string
    to?: string
    page?: number
    pageSize?: number
}

export interface PageResult<T> {
    items: T[]
    total: number
}

export const logService = {
    async list(params: LogQuery): Promise<PageResult<LogItem>> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/logs', { params })
            return data
        }
        const size = params.pageSize ?? 20
        const page = params.page ?? 1
        const total = 320

        const actions = [
            'auth.login', 'auth.logout',
            'user.create', 'user.update', 'user.lock', 'user.unlock',
            'course.create', 'course.publish', 'course.approve',
            'payment.refund', 'payment.dispute',
            'config.update', 'security.ip.add', 'security.session.revoke'
        ]

        const items: LogItem[] = Array.from({ length: size }).map((_, i) => {
            const idx = (page - 1) * size + i + 1
            const act = actions[idx % actions.length]
            const res: LogResult = (idx % 7 === 0) ? 'failed' : 'success'
            return {
                id: `log-${idx}`,
                ts: new Date(Date.now() - idx * 18e5).toISOString(),
                actorId: (idx % 8) + 1,
                actorName: `User ${(idx % 8) + 1}`,
                actorRole: (['admin', 'teacher', 'student'] as const)[idx % 3],
                action: act,
                targetType: (['user', 'course', 'payment', 'config', 'security'] as const)[idx % 5],
                targetId: (idx % 50) + 1,
                result: res,
                ip: `203.0.113.${(idx % 200) + 1}`,
                userAgent: 'Chrome on Windows',
                traceId: `trace-${100000 + idx}`,
                message: res === 'failed' ? 'Permission denied' : 'OK',
                meta: { note: 'mock' },
            }
        })
        return { items, total }
    },

    async detail(id: string): Promise<LogItem> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/admin/logs/${id}`)
            return data
        }
        const base = (await this.list({ page: 1, pageSize: 1 })).items[0]
        return { ...base, id }
    },

    async exportCsv(params: LogQuery): Promise<Blob> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/logs/export', { params, responseType: 'blob' })
            return data
        }
        const { items } = await this.list({ ...params, page: 1, pageSize: 1000 })
        const headers = 'id,ts,actorName,actorRole,action,targetType,targetId,result,ip,traceId,message'
        const rows = items.map(i =>
            [i.id, i.ts, i.actorName, i.actorRole, i.action, i.targetType, i.targetId, i.result, i.ip, i.traceId, (i.message || '').replace(/,/g, ' ')].join(',')
        )
        const csv = [headers, ...rows].join('\n')
        return new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    },
}
