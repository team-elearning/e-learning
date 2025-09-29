// src/services/payment.service.ts
import api from '@/config/axios'

export type ID = string | number
export type Gateway = 'Momo' | 'VNPay' | 'QR' | 'Bank'
export type TxStatus =
    | 'Pending'
    | 'Processing'
    | 'Succeeded'
    | 'Failed'
    | 'Refunded'
    | 'Disputed'

export interface TxSummary {
    id: string
    userId: ID
    buyerName: string
    buyerEmail: string
    courseId: ID
    courseTitle: string
    amount: number
    currency: 'VND'
    gateway: Gateway
    status: TxStatus
    createdAt: string
    settledAt?: string
}

export interface TxEvent {
    time: string
    type:
    | 'created'
    | 'authorized'
    | 'captured'
    | 'succeeded'
    | 'failed'
    | 'refunded'
    | 'dispute_opened'
    | 'dispute_won'
    | 'dispute_lost'
    description: string
    meta?: Record<string, any>
}

export interface TxDetail extends TxSummary {
    fees: number
    net: number
    reference?: string
    cardBrand?: string
    cardLast4?: string
    bankCode?: string
    events: TxEvent[]
    tags?: string[]
}

export interface TxMetrics {
    count: number
    gross: number
    net: number
    refunds: number
    disputed: number
}

export interface PageParams {
    q?: string
    status?: TxStatus
    gateway?: Gateway
    userId?: ID
    courseId?: ID
    from?: string
    to?: string
    page?: number
    pageSize?: number
    sortBy?: 'createdAt' | 'amount' | 'status'
    sortDir?: 'ascending' | 'descending'
}
export interface PageResult<T> {
    items: T[]
    total: number
}

const USE_MOCK = true // ← bật dữ liệu giả để dev trước

function seededRand(n: number) {
    // deterministic a bit
    const x = Math.sin(n) * 10000
    return x - Math.floor(x)
}

const gateways: Gateway[] = ['VNPay', 'Momo', 'QR', 'Bank']
const statuses: TxStatus[] = [
    'Pending',
    'Processing',
    'Succeeded',
    'Failed',
    'Refunded',
    'Disputed',
]

export const paymentService = {
    // ===== LIST =====
    async list(params: PageParams): Promise<PageResult<TxSummary>> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/transactions', { params })
            return data
        }

        const size = params.pageSize ?? 20
        const page = params.page ?? 1
        const total = 240

        let items: TxSummary[] = Array.from({ length: size }).map((_, i) => {
            const idx = (page - 1) * size + i + 1
            const gw = gateways[idx % gateways.length]
            const st = statuses[idx % statuses.length]
            const amount = (idx % 5 + 1) * 99000
            const courseId = (idx % 40) + 1
            const userId = (idx % 150) + 1
            return {
                id: `TX-${String(idx).padStart(6, '0')}`,
                userId,
                buyerName: `User ${userId}`,
                buyerEmail: `user${userId}@example.com`,
                courseId,
                courseTitle: `Khoá học #${courseId}`,
                amount,
                currency: 'VND',
                gateway: gw,
                status: st,
                createdAt: new Date(Date.now() - idx * 36e5).toISOString(),
                settledAt:
                    st === 'Succeeded' || st === 'Refunded'
                        ? new Date(Date.now() - (idx - 1) * 36e5).toISOString()
                        : undefined,
            }
        })

        // lọc đơn giản mock
        if (params.q) {
            const q = params.q.toLowerCase()
            items = items.filter(
                (t) =>
                    t.id.toLowerCase().includes(q) ||
                    t.buyerEmail.toLowerCase().includes(q) ||
                    t.courseTitle.toLowerCase().includes(q)
            )
        }
        if (params.status) items = items.filter((t) => t.status === params.status)
        if (params.gateway) items = items.filter((t) => t.gateway === params.gateway)
        if (params.userId) items = items.filter((t) => t.userId == params.userId)
        if (params.courseId) items = items.filter((t) => t.courseId == params.courseId)
        if (params.from) items = items.filter((t) => t.createdAt >= params.from!)
        if (params.to) items = items.filter((t) => t.createdAt <= params.to!)

        return { items, total: Math.max(items.length, total) }
    },

    // ===== METRICS (kpis) =====
    async metrics(params: PageParams): Promise<TxMetrics> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/transactions/metrics', { params })
            return data
        }
        const { items } = await this.list({ ...params, page: 1, pageSize: 200 })
        const gross = items.reduce((a, b) => a + b.amount, 0)
        const refunds = Math.round(gross * 0.06)
        const net = Math.round(gross * 0.92) - refunds
        const disputed = Math.round(items.length * 0.03)
        return { count: items.length, gross, net, refunds, disputed }
    },

    // ===== DETAIL =====
    async detail(id: ID): Promise<TxDetail> {
        if (!USE_MOCK) {
            const { data } = await api.get(`/admin/transactions/${id}`)
            return data
        }

        const num = Number(String(id).replace(/\D/g, '')) || 1
        const gw = gateways[num % gateways.length]
        const st = statuses[num % statuses.length]
        const amount = (num % 5 + 1) * 99000
        const fees = Math.round(amount * 0.03 + 2200)
        const net = amount - fees - (st === 'Refunded' ? amount : 0)
        const buyerId = (num % 150) + 1
        const courseId = (num % 40) + 1

        const base = Date.now() - num * 36e5
        const events: TxEvent[] = [
            { time: new Date(base).toISOString(), type: 'created', description: 'Tạo giao dịch' },
            { time: new Date(base + 5 * 60 * 1000).toISOString(), type: 'authorized', description: 'Uỷ quyền thanh toán' },
        ]
        if (st === 'Succeeded' || st === 'Refunded') {
            events.push({
                time: new Date(base + 10 * 60 * 1000).toISOString(),
                type: 'captured',
                description: 'Thu tiền',
            })
            events.push({
                time: new Date(base + 12 * 60 * 1000).toISOString(),
                type: 'succeeded',
                description: 'Thanh toán thành công',
            })
        }
        if (st === 'Refunded') {
            events.push({
                time: new Date(base + 36 * 60 * 1000).toISOString(),
                type: 'refunded',
                description: 'Hoàn tiền toàn phần',
            })
        }
        if (st === 'Disputed') {
            events.push({
                time: new Date(base + 60 * 60 * 1000).toISOString(),
                type: 'dispute_opened',
                description: 'Mở tranh chấp',
            })
        }

        return {
            id: String(id),
            userId: buyerId,
            buyerName: `User ${buyerId}`,
            buyerEmail: `user${buyerId}@example.com`,
            courseId,
            courseTitle: `Khoá học #${courseId}`,
            amount,
            currency: 'VND',
            gateway: gw,
            status: st,
            createdAt: new Date(base).toISOString(),
            settledAt:
                st === 'Succeeded' || st === 'Refunded'
                    ? new Date(base + 12 * 60 * 1000).toISOString()
                    : undefined,
            fees,
            net,
            reference: `REF-${String(num).padStart(6, '0')}`,
            cardBrand: gw === 'Bank' ? undefined : (['Visa', 'Mastercard'][num % 2] as any),
            cardLast4: gw === 'Bank' ? undefined : String(1000 + (num % 9000)),
            bankCode: gw === 'Bank' ? (['VCB', 'TCB', 'ACB', 'VTB'][num % 4] as any) : undefined,
            events,
            tags: seededRand(num) > 0.7 ? ['high_value'] : [],
        }
    },

    // ===== ACTIONS =====
    async refund(id: ID, amount?: number, reason?: string) {
        if (!USE_MOCK) return api.post(`/admin/transactions/${id}/refund`, { amount, reason })
        return Promise.resolve({ ok: true })
    },
    async markDispute(id: ID, note?: string) {
        if (!USE_MOCK) return api.post(`/admin/transactions/${id}/dispute`, { note })
        return Promise.resolve({ ok: true })
    },
    async resolveDispute(id: ID, result: 'won' | 'lost') {
        if (!USE_MOCK) return api.post(`/admin/transactions/${id}/dispute/resolve`, { result })
        return Promise.resolve({ ok: true })
    },

    // ===== EXPORT =====
    async exportCsv(params: PageParams): Promise<Blob> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/transactions/export', {
                params,
                responseType: 'blob',
            })
            return data
        }
        const { items } = await this.list({ ...params, page: 1, pageSize: 1000 })
        const headers = [
            'id',
            'buyerName',
            'buyerEmail',
            'courseTitle',
            'amount',
            'currency',
            'gateway',
            'status',
            'createdAt',
            'settledAt',
        ]
        const csv = [
            headers.join(','),
            ...items.map((t) =>
                [
                    t.id,
                    t.buyerName,
                    t.buyerEmail,
                    t.courseTitle,
                    t.amount,
                    t.currency,
                    t.gateway,
                    t.status,
                    t.createdAt,
                    t.settledAt || '',
                ].join(',')
            ),
        ].join('\n')
        return new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    },
}
