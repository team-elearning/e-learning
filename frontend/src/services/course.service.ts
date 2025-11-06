import api from '@/config/axios'

export type ID = string | number
export type Grade = 1 | 2 | 3 | 4 | 5
export type Subject = 'math' | 'vietnamese' | 'english' | 'science' | 'history'
export type Level = 'basic' | 'advanced'
export type CourseStatus = 'draft' | 'pending_review' | 'published' | 'rejected' | 'archived'

export interface CourseSummary {
  id: ID
  title: string
  grade: Grade
  subject: Subject
  teacherId: ID
  teacherName: string
  lessonsCount: number
  enrollments: number
  status: CourseStatus
  createdAt: string
  updatedAt: string
  thumbnail?: string
}

export interface Lesson {
  id: ID
  title: string
  type: 'video' | 'pdf' | 'quiz'
  durationMinutes?: number
  isPreview?: boolean
}

export interface Section {
  id: ID
  title: string
  order: number
  lessons: Lesson[]
}

export interface CourseDetail extends CourseSummary {
  description?: string
  level?: Level
  durationMinutes?: number
  sections: Section[]
  // nếu cần: prerequisites?: ID[]
}

export interface PageParams {
  q?: string
  grade?: Grade
  subject?: Subject
  teacherId?: ID
  status?: CourseStatus
  from?: string
  to?: string
  page?: number
  pageSize?: number
  sortBy?: 'createdAt' | 'updatedAt' | 'title' | 'enrollments'
  sortDir?: 'ascending' | 'descending'
}
export interface PageResult<T> { items: T[]; total: number }

const USE_MOCK = true

const SUBJECTS: Subject[] = ['math', 'vietnamese', 'english', 'science', 'history']
function subjectLabel(s: Subject) {
  return s === 'math' ? 'Toán'
    : s === 'vietnamese' ? 'Tiếng Việt'
    : s === 'english' ? 'Tiếng Anh'
    : s === 'science' ? 'Khoa học'
    : 'Lịch sử'
}

// ====== SERVICE ======
export const courseService = {
  // LIST
  async list(params: PageParams): Promise<PageResult<CourseSummary>> {
    if (!USE_MOCK) {
      const { data } = await api.get('/admin/courses', { params })
      return data
    }
    const size = params.pageSize ?? 20
    const page = params.page ?? 1
    const total = 173

    const items: CourseSummary[] = Array.from({ length: size }).map((_, i) => {
      const id = (page - 1) * size + i + 1
      const grade = ((id % 5) + 1) as Grade
      const subject = SUBJECTS[id % SUBJECTS.length]
      const teacherId = (id % 15) + 1

      // const statuses: CourseStatus[] = ['draft', 'pending_review', 'published', 'rejected', 'archived']
      // const status = statuses[id % statuses.length]
      // [SỬA] Không dùng status ngẫu nhiên theo id nữa để tránh thiếu published ở khối 1–2

      const isPublished = (id % 2 === 0) || grade <= 2
      // [THÊM] Bảo đảm: khối 1–2 (grade <= 2) luôn có published,
      // và thêm id chẵn cũng published để dữ liệu phong phú hơn
      const status: CourseStatus = isPublished ? 'published' : 'draft' // [SỬA]

      return {
        id,
        title: `Khoá học #${id} - ${subjectLabel(subject)} lớp ${grade}`,
        grade,
        subject,
        teacherId,
        teacherName: `GV ${teacherId}`,
        lessonsCount: (id % 10) + 12,
        enrollments: (id * 7) % 320,
        status, // [SỬA] dùng status mới ở trên
        createdAt: new Date(Date.now() - id * 864e5).toISOString(),
        updatedAt: new Date(Date.now() - id * 36e5).toISOString(),
        thumbnail: `https://picsum.photos/seed/course-${id}/320/180`,
      }
    })

    // lọc đơn giản phía client (mock)
    let list = items
    if (params.q) {
      const q = params.q.toLowerCase()
      list = list.filter(c =>
        c.title.toLowerCase().includes(q) ||
        String(c.id).includes(q) ||
        c.teacherName.toLowerCase().includes(q)
      )
    }
    if (params.grade) list = list.filter(c => c.grade === params.grade)
    if (params.subject) list = list.filter(c => c.subject === params.subject)
    if (params.teacherId) list = list.filter(c => c.teacherId == params.teacherId)
    if (params.status) list = list.filter(c => c.status === params.status)

    return { items: list, total }
  },

  // DETAIL
  async detail(id: ID): Promise<CourseDetail> {
    if (!USE_MOCK) {
      const { data } = await api.get(`/admin/courses/${id}`)
      return data
    }
    const grade = (((Number(id) || 1) % 5) + 1) as Grade
    const subject = SUBJECTS[(Number(id) || 1) % SUBJECTS.length]
    const sections: Section[] = Array.from({ length: 4 }).map((_, sIdx) => ({
      id: `S${id}-${sIdx + 1}`,
      title: `Chương ${sIdx + 1}`,
      order: sIdx + 1,
      lessons: Array.from({ length: 4 + (sIdx % 2) }).map((__, lIdx) => ({
        id: `L${id}-${sIdx + 1}-${lIdx + 1}`,
        title: `Bài ${sIdx + 1}.${lIdx + 1} – ${subjectLabel(subject)}`,
        type: (['video', 'pdf', 'quiz'] as Lesson['type'][])[(lIdx + sIdx) % 3],
        durationMinutes: 8 + ((lIdx + sIdx) % 5) * 5,
        isPreview: lIdx === 0
      }))
    }))

    // const status = (['draft', 'pending_review', 'published', 'rejected', 'archived'] as CourseStatus[])[Number(id) % 5]
    // [SỬA] Không dùng random status nữa để đồng bộ với list()

    const isPublished = (Number(id) % 2 === 0) || grade <= 2 // [THÊM] đồng bộ logic với list()
    const status: CourseStatus = isPublished ? 'published' : 'draft' // [SỬA]

    return {
      id,
      title: `Khoá học #${id} - ${subjectLabel(subject)} lớp ${grade}`,
      grade,
      subject,
      teacherId: 3,
      teacherName: 'GV 3',
      lessonsCount: sections.reduce((a, s) => a + s.lessons.length, 0),
      enrollments: (Number(id) * 7) % 320,
      status, // [SỬA]
      createdAt: new Date(Date.now() - Number(id) * 864e5).toISOString(),
      updatedAt: new Date().toISOString(),
      thumbnail: `https://picsum.photos/seed/course-${id}/800/360`,
      description: 'Mô tả ngắn gọn về khoá học. Nội dung thiết kế theo từng chương/bài, có video, tài liệu và quiz.',
      level: (Number(id) % 2 ? 'basic' : 'advanced'),
      durationMinutes: sections.reduce(
        (a, s) => a + s.lessons.reduce((b, l) => b + (l.durationMinutes || 0), 0),
        0
      ),
      sections
    }
  },

  // CREATE / UPDATE
  create(payload: Partial<CourseDetail>) {
    if (!USE_MOCK) return api.post('/admin/courses', payload)
    return Promise.resolve({ ok: true })
  },
  update(id: ID, payload: Partial<CourseDetail>) {
    if (!USE_MOCK) return api.put(`/admin/courses/${id}`, payload)
    return Promise.resolve({ ok: true })
  },

  // STATUS / ACTIONS
  approve(id: ID) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/approve`) },
  reject(id: ID, reason?: string) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/reject`, { reason }) },
  publish(id: ID) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/publish`) },
  unpublish(id: ID) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/unpublish`) },
  archive(id: ID) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/archive`) },
  restore(id: ID) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/restore`) },

  // BULK (tuỳ chọn dùng ở trang duyệt)
  bulkApprove(ids: ID[]) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post('/admin/courses/bulk/approve', { ids }) },
  bulkReject(ids: ID[], reason?: string) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post('/admin/courses/bulk/reject', { ids, reason }) },
  bulkPublish(ids: ID[]) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post('/admin/courses/bulk/publish', { ids }) },
  bulkArchive(ids: ID[]) { return USE_MOCK ? Promise.resolve({ ok: true }) : api.post('/admin/courses/bulk/archive', { ids }) },

  // FILTER OPTIONS
  async listTeachers(): Promise<{ id: ID; name: string }[]> {
    if (!USE_MOCK) { const { data } = await api.get('/admin/teachers'); return data }
    return Array.from({ length: 15 }).map((_, i) => ({ id: i + 1, name: `GV ${i + 1}` }))
  },
  subjects(): { label: string; value: Subject }[] {
    return SUBJECTS.map(s => ({ value: s, label: subjectLabel(s) }))
  }
}
