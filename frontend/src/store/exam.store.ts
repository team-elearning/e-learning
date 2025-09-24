// src/store/exam.store.ts
import { defineStore } from 'pinia'

/** ========= Types ========= */
export type ExamLevel = 'basic' | 'advanced'

export interface Exam {
  id: number
  title: string
  level: ExamLevel
  durationSec: number
  passCount: number
  questionsCount: number
}

/** ========= MOCK POOL (ổn định) =========
 *  Bạn có thể thay thế bằng call API sau này
 */
const SUBJECTS = ['Toán', 'Tiếng Việt', 'Tiếng Anh', 'Khoa học', 'Lịch sử'] as const
const POOL: Exam[] = Array.from({ length: 120 }).map((_, i) => {
  const id = i + 1
  const subject = SUBJECTS[i % SUBJECTS.length]
  const level: ExamLevel = i % 2 ? 'basic' : 'advanced'
  const durationSec = 20 * 60 + (i % 5) * 60 // 20–24 phút
  const passCount = 12 + (i % 5) // 12–16
  const questionsCount = 20 + (i % 3) * 10 // 20 / 30 / 40

  return {
    id,
    title: `Đề #${id} – ${subject} (${level === 'basic' ? 'Cơ bản' : 'Mở rộng'})`,
    level,
    durationSec,
    passCount,
    questionsCount,
  }
})

/** ========= Store ========= */
export const useExamStore = defineStore('exam', {
  state: () => ({
    // list/paging
    exams: [] as Exam[],
    total: 0,
    page: 1,
    pageSize: 12,

    // filters
    q: '' as string,
    level: '' as '' | ExamLevel,

    // ui
    loading: false,
    error: '' as string,
  }),

  getters: {
    pages(state): number {
      return Math.max(1, Math.ceil(state.total / state.pageSize))
    },
  },

  actions: {
    /** Lấy 1 trang dữ liệu (mock) – KHÔNG dùng default param với this */
    async fetchExamsPage(page?: number, pageSize?: number) {
      // gán mặc định bên trong để tránh lỗi this chưa bind
      page = page ?? this.page
      pageSize = pageSize ?? this.pageSize

      this.loading = true
      this.error = ''
      try {
        // filter trong mock
        let list = POOL.slice()
        if (this.q) {
          const key = this.q.toLowerCase()
          list = list.filter((e) => e.title.toLowerCase().includes(key))
        }
        if (this.level) {
          list = list.filter((e) => e.level === this.level)
        }

        // tính phân trang
        this.total = list.length
        const start = (page - 1) * pageSize
        const pageItems = list.slice(start, start + pageSize)

        // set state
        this.exams = pageItems
        this.page = page
        this.pageSize = pageSize
      } catch (e: any) {
        this.error = e?.message || String(e)
      } finally {
        this.loading = false
      }
    },

    /** Tiện ích tải theo state hiện tại */
    async fetchExams() {
      await this.fetchExamsPage()
    },

    /** Lấy exam trong pool theo id (không phụ thuộc trang hiện tại) */
    getById(id: number): Exam | undefined {
      return POOL.find((x) => x.id === Number(id))
    },

    /** Đảm bảo exam có trong danh sách hiện tại (tiện cho trang detail vào trực tiếp) */
    ensureExam(id: number) {
      const item = this.getById(id)
      if (!item) return
      if (!this.exams.find((x) => x.id === item.id)) {
        // chèn lên đầu list để UI có dữ liệu ngay
        this.exams = [item, ...this.exams]
      }
    },

    /** Thay đổi filter rồi nạp lại trang 1 */
    async applyFilters({ q, level }: { q?: string; level?: '' | ExamLevel }) {
      if (typeof q === 'string') this.q = q
      if (typeof level !== 'undefined') this.level = level
      await this.fetchExamsPage(1, this.pageSize)
    },

    /** Chuyển trang */
    async goTo(page: number) {
      const target = Math.min(Math.max(1, page), this.pages)
      await this.fetchExamsPage(target, this.pageSize)
    },
  },
})
