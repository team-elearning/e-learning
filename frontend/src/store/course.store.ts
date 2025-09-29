// src/store/exam.store.ts
import { defineStore } from 'pinia'

export type ExamLevel = 'basic' | 'advanced'
export interface ExamSummary {
  id: number
  title: string
  level: ExamLevel
  durationSec: number
  passCount: number
  questions: number
  subject: 'math' | 'vietnamese' | 'english' | 'science'
}

function makeMockPool(total = 240): ExamSummary[] {
  const subs: ExamSummary['subject'][] = ['math', 'vietnamese', 'english', 'science']
  const pool: ExamSummary[] = []
  for (let i = 1; i <= total; i++) {
    const level: ExamLevel = i % 2 ? 'basic' : 'advanced'
    pool.push({
      id: i,
      title: `${level === 'basic' ? 'Ôn tập cơ bản' : 'Đề mở rộng'} #${i}`,
      level,
      durationSec: 20 * 60 + (i % 5) * 60,
      passCount: 12 + (i % 5),
      questions: 20 + (i % 15),
      subject: subs[i % subs.length],
    })
  }
  return pool
}

// ===== MOCK POOL (nguồn dữ liệu ảo) =====
const MOCK_POOL = makeMockPool()

export const useExamStore = defineStore('exam', {
  state: () => ({
    exams: [] as ExamSummary[],
    total: 0,
    page: 1,
    pageSize: 12,
    loading: false,
    q: '' as string,
    level: '' as '' | ExamLevel,
  }),
  actions: {
    /** Phân trang + lọc nhanh (mock) */
    async fetchExamsPage(page?: number, pageSize?: number) {
      this.loading = true
      try {
        const p = page ?? this.page
        const ps = pageSize ?? this.pageSize

        let data = MOCK_POOL.slice()
        const key = this.q.trim().toLowerCase()
        if (key) data = data.filter(d => d.title.toLowerCase().includes(key))
        if (this.level) data = data.filter(d => d.level === this.level)

        this.total = data.length
        const start = (p - 1) * ps
        this.exams = data.slice(start, start + ps)
        this.page = p
        this.pageSize = ps
      } finally {
        this.loading = false
      }
    },

    /** [THÊM] Tải trang đầu (giống fetchAll cũ) */
    async fetchExams() {
      await this.fetchExamsPage(1, this.pageSize)
    },

    /** [THÊM] Lấy đề theo id từ pool (không phụ thuộc trang hiện tại) */
    getById(id: number): ExamSummary | undefined {
      return MOCK_POOL.find(e => e.id === id)
    },

    /** [THÊM] Đảm bảo đề id có mặt trong `exams` (nếu không thì thêm vào đầu danh sách) */
    ensureExam(id: number) {
      const has = this.exams.find(e => e.id === id)
      if (!has) {
        const found = this.getById(id)
        if (found) this.exams = [found, ...this.exams]
      }
    },
  },
})
