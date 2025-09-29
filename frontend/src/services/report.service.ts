// src/services/report.service.ts
import api from '@/config/axios'

export type ID = string | number
type Granularity = 'day' | 'week' | 'month'

const USE_MOCK = true

// ===== Types =====
export interface DateRange { from?: string; to?: string; granularity?: Granularity }

export interface RevenuePoint { date: string; gross: number; net: number; refunds: number }
export interface RevenueByGateway { gateway: 'VNPay' | 'Momo' | 'QR' | 'Bank'; amount: number }
export interface RevenueTopCourse { courseId: ID; title: string; teacher: string; gross: number; net: number; orders: number }

export interface UserKPIs { dau: number; mau: number; newUsers: number; activeUsers: number }
export interface UserSeriesPoint { date: string; dau: number; newUsers: number }
export interface UserByRole { role: 'admin' | 'teacher' | 'student'; count: number }

export interface LearningKPIs { avgCompletion: number; avgScore: number; avgTimeSpentMin: number }
export interface CompletionPoint { date: string; completion: number }
export interface ScoreBySubject { subject: string; avgScore: number }
export interface AtRiskRow { userId: ID; name: string; className?: string; progress: number; lastActiveAt?: string }

export interface ContentKPIs { totalPublished: number; totalEnrollments: number; avgRating: number }
export interface ViewsBySubject { subject: string; views: number }
export interface TopContentRow { courseId: ID; title: string; views: number; enrollments: number; rating: number }

// ===== Helpers (mock) =====
function daysBetween(from: Date, to: Date) {
    const result: Date[] = []
    const cur = new Date(from)
    while (cur <= to) { result.push(new Date(cur)); cur.setDate(cur.getDate() + 1) }
    return result
}
function fmt(d: Date) {
    return d.toISOString().slice(0, 10)
}
function seed(n: number) { const x = Math.sin(n) * 10000; return x - Math.floor(x) }

// ===== Service =====
export const reportService = {

    // ---------- Revenue ----------
    async revenueTimeseries(params: DateRange): Promise<RevenuePoint[]> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/reports/revenue/timeseries', { params })
            return data
        }
        const now = new Date()
        const from = params.from ? new Date(params.from) : new Date(now.getTime() - 29 * 864e5)
        const to = params.to ? new Date(params.to) : now
        const gran = params.granularity || 'day'

        // build daily then rollup
        const base = daysBetween(from, to).map((d, i) => {
            const r = seed(i + 1)
            const gross = Math.round(800000 + r * 1200000) // 0.8–2.0m
            const refunds = Math.round(gross * (r > .85 ? .12 : .04))
            const net = gross - Math.round(gross * 0.06) - refunds
            return { date: fmt(d), gross, net, refunds }
        })

        if (gran === 'day') return base
        // rollup week/month
        const groupKey = (s: string) => {
            const d = new Date(s)
            if (gran === 'week') {
                const first = new Date(d)
                first.setDate(d.getDate() - ((d.getDay() + 6) % 7)) // ISO week
                return `W${fmt(first)}`
            }
            return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}`
        }
        const map = new Map<string, RevenuePoint>()
        base.forEach(p => {
            const k = groupKey(p.date)
            const cur = map.get(k) || { date: k, gross: 0, net: 0, refunds: 0 }
            cur.gross += p.gross; cur.net += p.net; cur.refunds += p.refunds
            map.set(k, cur)
        })
        return Array.from(map.values())
    },

    async revenueByGateway(params: DateRange): Promise<RevenueByGateway[]> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/reports/revenue/by-gateway', { params })
            return data
        }
        const base = ['VNPay', 'Momo', 'QR', 'Bank'] as RevenueByGateway['gateway'][]
        return base.map((g, i) => ({ gateway: g, amount: 3000000 + Math.round(seed(i + 2) * 5000000) }))
    },

    async revenueTopCourses(params: DateRange): Promise<RevenueTopCourse[]> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/reports/revenue/top-courses', { params })
            return data
        }
        return Array.from({ length: 10 }).map((_, i) => ({
            courseId: 100 + i, title: `Khoá học #${100 + i}`,
            teacher: `GV ${(i % 7) + 1}`,
            gross: 4_000_000 + i * 120_000,
            net: 3_650_000 + i * 95_000,
            orders: 50 + i * 3
        }))
    },

    async exportRevenueCsv(params: DateRange): Promise<Blob> {
        if (!USE_MOCK) {
            const { data } = await api.get('/admin/reports/revenue/export', { params, responseType: 'blob' })
            return data
        }
        const rows = await this.revenueTimeseries(params)
        const header = 'date,gross,net,refunds'
        const csv = [header, ...rows.map(r => `${r.date},${r.gross},${r.net},${r.refunds}`)].join('\n')
        return new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    },

    // ---------- Users ----------
    async userKpis(params: DateRange): Promise<UserKPIs> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/users/kpis', { params }); return data }
        return { dau: 812, mau: 4321, newUsers: 213, activeUsers: 2760 }
    },
    async userSeries(params: DateRange): Promise<UserSeriesPoint[]> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/users/timeseries', { params }); return data }
        const now = new Date()
        const from = params.from ? new Date(params.from) : new Date(now.getTime() - 29 * 864e5)
        const to = params.to ? new Date(params.to) : now
        return daysBetween(from, to).map((d, i) => ({
            date: fmt(d),
            dau: Math.round(500 + seed(i + 9) * 500),
            newUsers: Math.round(30 + seed(i + 19) * 50),
        }))
    },
    async userByRole(params: DateRange): Promise<UserByRole[]> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/users/by-role', { params }); return data }
        return [
            { role: 'admin', count: 8 },
            { role: 'teacher', count: 134 },
            { role: 'student', count: 3890 },
        ]
    },
    async exportUsersCsv(params: DateRange): Promise<Blob> {
        const series = await this.userSeries(params)
        const header = 'date,dau,newUsers'
        const csv = [header, ...series.map(r => `${r.date},${r.dau},${r.newUsers}`)].join('\n')
        return new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    },

    // ---------- Learning ----------
    async learningKpis(params: DateRange): Promise<LearningKPIs> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/learning/kpis', { params }); return data }
        return { avgCompletion: 62, avgScore: 74, avgTimeSpentMin: 38 }
    },
    async completionSeries(params: DateRange): Promise<CompletionPoint[]> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/learning/completion', { params }); return data }
        const now = new Date()
        const from = params.from ? new Date(params.from) : new Date(now.getTime() - 29 * 864e5)
        const to = params.to ? new Date(params.to) : now
        return daysBetween(from, to).map((d, i) => ({ date: fmt(d), completion: Math.round(45 + seed(i + 99) * 35) }))
    },
    async scoreBySubject(params: DateRange): Promise<ScoreBySubject[]> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/learning/score-by-subject', { params }); return data }
        return [
            { subject: 'Toán', avgScore: 78 },
            { subject: 'Tiếng Việt', avgScore: 74 },
            { subject: 'Tiếng Anh', avgScore: 71 },
            { subject: 'Khoa học', avgScore: 69 },
            { subject: 'Lịch sử', avgScore: 67 },
        ]
    },
    async atRiskStudents(params: DateRange): Promise<AtRiskRow[]> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/learning/at-risk', { params }); return data }
        return Array.from({ length: 12 }).map((_, i) => ({
            userId: 500 + i, name: `HS ${500 + i}`, className: `Lớp ${(i % 5) + 1}${String.fromCharCode(65 + (i % 3))}`,
            progress: 15 + i * 3, lastActiveAt: new Date(Date.now() - (i + 1) * 864e5).toISOString()
        }))
    },
    async exportLearningCsv(params: DateRange): Promise<Blob> {
        const series = await this.completionSeries(params)
        const header = 'date,completion'
        const csv = [header, ...series.map(r => `${r.date},${r.completion}`)].join('\n')
        return new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    },

    // ---------- Content ----------
    async contentKpis(params: DateRange): Promise<ContentKPIs> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/content/kpis', { params }); return data }
        return { totalPublished: 182, totalEnrollments: 7630, avgRating: 4.3 }
    },
    async viewsBySubject(params: DateRange): Promise<ViewsBySubject[]> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/content/views-by-subject', { params }); return data }
        return [
            { subject: 'Toán', views: 18230 },
            { subject: 'Tiếng Việt', views: 13210 },
            { subject: 'Tiếng Anh', views: 15320 },
            { subject: 'Khoa học', views: 9210 },
            { subject: 'Lịch sử', views: 7110 },
        ]
    },
    async topContents(params: DateRange): Promise<TopContentRow[]> {
        if (!USE_MOCK) { const { data } = await api.get('/admin/reports/content/top', { params }); return data }
        return Array.from({ length: 10 }).map((_, i) => ({
            courseId: 300 + i, title: `Khoá học hot #${300 + i}`,
            views: 10000 + i * 900, enrollments: 400 + i * 30, rating: +(4 + (i % 5) * 0.1).toFixed(1)
        }))
    },
    async exportContentCsv(params: DateRange): Promise<Blob> {
        const list = await this.topContents(params)
        const header = 'courseId,title,views,enrollments,rating'
        const csv = [header, ...list.map(r => `${r.courseId},"${r.title}",${r.views},${r.enrollments},${r.rating}`)].join('\n')
        return new Blob([csv], { type: 'text/csv;charset=utf-8;' })
    },
}
