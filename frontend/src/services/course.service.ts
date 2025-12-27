import api from '@/config/axios'

export type ID = string | number
export type Grade = 1 | 2 | 3 | 4 | 5
export type Subject =
  | 'math'
  | 'vietnamese'
  | 'english'
  | 'science'
  | 'history'
  | string
export type Level = 'basic' | 'advanced'
export type CourseStatus = 'draft' | 'pending_review' | 'published' | 'rejected' | 'archived'

export interface CourseSummary {
  id: ID
  title: string
  grade: Grade
  subject: Subject
  subjectName?: string | null
  teacherId: ID
  teacherName: string
  lessonsCount: number
  moduleCount?: number
  enrollments: number
  status: CourseStatus
  createdAt: string
  updatedAt: string
  thumbnail?: string
  price?: number
  categories?: { name: string }[]
  my_progress?: MyProgress

}

export interface Lesson {
  id: ID
  title: string
  type: 'video' | 'pdf' | 'quiz'
  durationMinutes?: number
  isPreview?: boolean
  contentBlocks?: LessonContentBlock[]
  videoUrl?: string | null
}

export interface LessonContentBlock {
  id: ID
  type: string
  position?: number
  payload?: Record<string, any> | null
}

export interface Section {
  id: ID
  title: string
  order: number
  lessons: Lesson[]
}

export interface CourseDetail extends CourseSummary {
  description?: string
  introduction?: string
  level?: Level
  durationMinutes?: number
  sections: Section[]
  video_url?: string
  video_file?: string
  price?: number
  thumbnail?: string
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

export interface StudentMyCourse extends Partial<Omit<CourseSummary, 'grade' | 'subject'>> {
  grade: Grade | string | number
  subject?: string
  subjectSlug?: string
  gradeLabel?: string
  gradeNumber?: number | null
  price?: number
  progress?: number
  done?: boolean
  isEnrolled?: boolean
}

export interface StudentMyCoursesResponse {
  base: StudentMyCourse[]
  supp: StudentMyCourse[]
  all: StudentMyCourse[]
}

export interface StudentMyCoursesFilters {
  q?: string
  grade?: string
  level?: 'main' | 'supp'
}

const COURSE_USE_MOCK = false
const mediaCache = new Map<string, string>()
const SUBJECTS: Subject[] = ['math', 'vietnamese', 'english', 'science', 'history']
function subjectLabel(s: Subject) {
  return s === 'math'
    ? 'Toán'
    : s === 'vietnamese'
      ? 'Tiếng Việt'
      : s === 'english'
        ? 'Tiếng Anh'
        : s === 'science'
          ? 'Khoa học'
          : 'Lịch sử'
}

function buildMockList(params: PageParams = {}): PageResult<CourseSummary> {
  const size = params.pageSize ?? 20
  const page = params.page ?? 1
  const total = 173

  const items: CourseSummary[] = Array.from({ length: size }).map((_, i) => {
    const id = (page - 1) * size + i + 1
    const grade = ((id % 5) + 1) as Grade
    const subject = SUBJECTS[id % SUBJECTS.length]
    const teacherId = (id % 15) + 1
    const isPublished = id % 2 === 0 || grade <= 2
    const status: CourseStatus = isPublished ? 'published' : 'draft'

    return {
      id,
      title: `Khoá học #${id} - ${subjectLabel(subject)} lớp ${grade}`,
      grade,
      subject,
      teacherId,
      teacherName: `GV ${teacherId}`,
      lessonsCount: (id % 10) + 12,
      enrollments: (id * 7) % 320,
      status,
      createdAt: new Date(Date.now() - id * 864e5).toISOString(),
      updatedAt: new Date(Date.now() - id * 36e5).toISOString(),
      thumbnail: `https://picsum.photos/seed/course-${id}/320/180`,
    }
  })

  let list = items
  if (params.q) {
    const q = params.q.toLowerCase()
    list = list.filter(
      (c) =>
        c.title.toLowerCase().includes(q) ||
        String(c.id).includes(q) ||
        c.teacherName.toLowerCase().includes(q),
    )
  }
  if (params.grade) list = list.filter((c) => c.grade === params.grade)
  if (params.subject) list = list.filter((c) => c.subject === params.subject)
  if (params.teacherId) list = list.filter((c) => String(c.teacherId) === String(params.teacherId))
  if (params.status) list = list.filter((c) => c.status === params.status)

  return { items: list, total }
}

function buildMockDetail(id: ID): CourseDetail {
  const numericId = Number(id) || 1
  const grade = ((numericId % 5) + 1) as Grade
  const subject = SUBJECTS[numericId % SUBJECTS.length]
  const sections: Section[] = Array.from({ length: 4 }).map((_, sIdx) => ({
    id: `S${numericId}-${sIdx + 1}`,
    title: `Chương ${sIdx + 1}`,
    order: sIdx + 1,
    lessons: Array.from({ length: 4 + (sIdx % 2) }).map((__, lIdx) => ({
      id: `L${numericId}-${sIdx + 1}-${lIdx + 1}`,
      title: `Bài ${sIdx + 1}.${lIdx + 1} – ${subjectLabel(subject)}`,
      type: (['video', 'pdf', 'quiz'] as Lesson['type'][])[(lIdx + sIdx) % 3],
      durationMinutes: 8 + ((lIdx + sIdx) % 5) * 5,
      isPreview: lIdx === 0,
    })),
  }))

  const isPublished = numericId % 2 === 0 || grade <= 2
  const status: CourseStatus = isPublished ? 'published' : 'draft'

  return {
    id: numericId,
    title: `Khoá học #${numericId} - ${subjectLabel(subject)} lớp ${grade}`,
    grade,
    subject,
    teacherId: 3,
    teacherName: 'GV 3',
    lessonsCount: sections.reduce((a, s) => a + s.lessons.length, 0),
    enrollments: (numericId * 7) % 320,
    status,
    createdAt: new Date(Date.now() - numericId * 864e5).toISOString(),
    updatedAt: new Date().toISOString(),
    thumbnail: `https://picsum.photos/seed/course-${numericId}/800/360`,
    description:
      'Mô tả ngắn gọn về khoá học. Nội dung thiết kế theo từng chương/bài, có video, tài liệu và quiz.',
    level: numericId % 2 ? 'basic' : 'advanced',
    durationMinutes: sections.reduce(
      (a, s) => a + s.lessons.reduce((b, l) => b + (l.durationMinutes || 0), 0),
      0,
    ),
    sections,
  }
}

type RawSubject = { id?: ID; title?: string; slug?: string } | string | null | undefined
type RawContentBlock = { id?: ID; type?: string; position?: number; payload?: Record<string, any> | null }
type RawLesson = {
  id?: ID
  title?: string
  content_type?: string
  type?: string
  durationMinutes?: number
  duration?: number
  duration_minutes?: number
  is_preview?: boolean
  isPreview?: boolean
  content_blocks?: RawContentBlock[]
  contentBlocks?: RawContentBlock[]
  blocks?: RawContentBlock[]
  content?: { content_blocks?: RawContentBlock[] }
}
type RawModule = { id?: ID; title?: string; position?: number; order?: number; lessons?: RawLesson[] }

const DEFAULT_THUMBNAIL =
  'https://images.unsplash.com/photo-1523580846011-d3a5bc25702b?auto=format&fit=crop&w=960&q=60'

const COURSE_STATUSES: CourseStatus[] = ['draft', 'pending_review', 'published', 'rejected', 'archived']

function normalizeStatus(rawStatus?: string, published?: boolean): CourseStatus {
  if (rawStatus && COURSE_STATUSES.includes(rawStatus as CourseStatus)) return rawStatus as CourseStatus
  return published ? 'published' : 'draft'
}

function normalizeSubject(raw: RawSubject): { slug: Subject | null; title?: string | null } {
  if (!raw) return { slug: null, title: null }
  if (typeof raw === 'string') return { slug: raw, title: raw }
  return {
    slug: (raw.slug || raw.title || null) as Subject | null,
    title: raw.title || raw.slug || null,
  }
}

function normalizeGrade(value: any): Grade {
  const num = Number(value)
  if (!Number.isNaN(num) && num >= 1 && num <= 5) return num as Grade
  return 1
}

function normalizeSubjectSlug(slug?: string | null): Subject | null {
  if (!slug) return null;

  const key = slug.toLowerCase().trim();

  const MAP: Record<string, Subject> = {
    'toan': 'math',
    'tieng-viet': 'vietnamese',
    'tieng-anh': 'english',
    'khoa-hoc': 'science',
    'lich-su': 'history',

    // fallback theo name
    'toán': 'math',
    'tiếng việt': 'vietnamese',
    'tiếng-việt': 'vietnamese',
    'tiếng anh': 'english',
    'tiếng-anh': 'english',
  };

  return MAP[key] || null;
}


function normalizeLessonType(contentType?: string, fallback?: string): Lesson['type'] {
  const type = (contentType || fallback || '').toLowerCase()
  if (type === 'video') return 'video'
  if (type === 'exercise' || type === 'quiz' || type === 'exploration') return 'quiz'
  return 'pdf'
}

function normalizeContentBlocks(rawBlocks?: RawContentBlock[]): LessonContentBlock[] {
  if (!Array.isArray(rawBlocks)) return []
  return rawBlocks.map((block, idx): LessonContentBlock => ({
    id: block.id ?? `block-${idx}`,
    type: block.type || 'text',
    position: typeof block.position === 'number' ? block.position : idx,
    payload: block.payload ?? null,
  }))
}

function extractVideoUrl(blocks: LessonContentBlock[]): string | null {
  for (const block of blocks) {
    if (block.type !== 'video') continue
    const payload = block.payload || {}
    const url =
      (payload as any).video_url ||
      (payload as any).videoUrl ||
      (payload as any).file_url ||
      (payload as any).url
    if (typeof url === 'string' && url) return url
  }
  return null
}

function normalizeLessons(rawLessons?: RawLesson[]): Lesson[] {
  if (!Array.isArray(rawLessons)) return []
  return rawLessons
    .map((lesson, idx): Lesson => {
      const duration =
        lesson.durationMinutes ??
        lesson.duration ??
        lesson.duration_minutes
      const contentBlocks = normalizeContentBlocks(
        lesson.content_blocks ??
        lesson.contentBlocks ??
        lesson.blocks ??
        lesson.content?.content_blocks,
      )
      return {
        id: lesson.id ?? `lesson-${idx}`,
        title: lesson.title || `Bài học ${idx + 1}`,
        type: normalizeLessonType(lesson.content_type, lesson.type),
        durationMinutes: typeof duration === 'number' ? duration : undefined,
        isPreview: Boolean(lesson.is_preview ?? lesson.isPreview),
        contentBlocks,
        videoUrl: extractVideoUrl(contentBlocks),
      }
    })
    .filter(Boolean)
}

function normalizeSections(payload: any): Section[] {
  if (Array.isArray(payload?.sections)) return payload.sections
  if (!Array.isArray(payload?.modules)) return []
  return payload.modules
    .slice()
    .sort((a: RawModule, b: RawModule) => (a?.position ?? a?.order ?? 0) - (b?.position ?? b?.order ?? 0))
    .map((module: RawModule, idx: number): Section => ({
      id: module.id ?? `section-${idx}`,
      title: module.title || `Chương ${idx + 1}`,
      order: module.position ?? module.order ?? idx,
      lessons: normalizeLessons(module.lessons),
    }))
}

function normalizeCourseSummary(payload: any): CourseSummary {
  if (!payload) return buildMockDetail(1)

  const { slug: subjectSlug, title: subjectTitle } = normalizeSubject(
    payload.subject ?? payload.subject_obj ?? payload.subjectInfo,
  )

  const teacherId =
    payload.teacherId ??
    payload.teacher_id ??
    payload.owner_id ??
    payload.owner?.id ??
    'unknown'

  const teacherName =
    payload.teacherName ??
    payload.owner_name ??
    payload.owner?.full_name ??
    payload.owner?.username ??
    payload.owner?.email ??
    'Đang cập nhật'

  const createdAt = payload.createdAt ?? payload.created_at
  const updatedAt = payload.updatedAt ?? payload.updated_at ?? createdAt

  const thumbnail =
    payload.thumbnail ??
    payload.thumbnail_url ??
    payload.image_url ??
    undefined

  const moduleCount =
    payload.module_count ??
    payload.modules?.length ??
    0

  const lessonsFromModules = Array.isArray(payload.modules)
    ? payload.modules.reduce((total: number, m: any) => total + (m.lessons?.length || 0), 0)
    : 0

  const lessonsCount =
    payload.lessonsCount ??
    payload.lessons_count ??
    lessonsFromModules

  const enrollments = payload.enrollments ?? payload.enrollment_count ?? 0

  const price = payload.price ?? payload.price_amount ?? payload.tuition

  return {
    id: payload.id ?? '',
    title: payload.title ?? 'Khoá học',
    grade: normalizeGrade(payload.grade),
    subject: normalizeSubjectSlug(subjectSlug) ?? '',
    subjectName: subjectTitle,
    categories: payload.categories ?? [],
    teacherId,
    teacherName,
    lessonsCount,
    moduleCount,
    enrollments,
    status: normalizeStatus(payload.status, payload.published),
    createdAt,
    updatedAt,
    thumbnail,
    price,

    // 🔥 GIỮ NGUYÊN DATA TỪ API
    my_progress: payload.my_progress ?? undefined,
  }

}

function normalizeCourseDetail(payload: any): CourseDetail {
  if (!payload) return buildMockDetail(1)

  const base = normalizeCourseSummary(payload)
  const sections = normalizeSections(payload)

  const lessonsCount =
    base.lessonsCount ||
    sections.reduce((a, s) => a + (s.lessons?.length || 0), 0) ||
    0

  const duration =
    payload.durationMinutes ??
    payload.duration_minutes ??
    payload.duration ??
    sections.reduce(
      (a, s) => a + (s.lessons || []).reduce((b, l) => b + (l.durationMinutes || 0), 0),
      0,
    )

  const rawLevel = String(payload.level || '').toLowerCase()
  const level: Level | undefined =
    rawLevel === 'advanced' ? 'advanced' : rawLevel === 'basic' ? 'basic' : undefined

  const thumbnail =
    payload.thumbnail ??
    payload.thumbnail_url ??
    payload.image_url ??
    base.thumbnail ??
    DEFAULT_THUMBNAIL

  return {
    ...base,
    description:
      payload.description ??
      payload.short_description ??
      payload.overview ??
      payload.introduction ??
      '',
    introduction: payload.introduction ?? payload.description ?? '',
    level,
    durationMinutes: typeof duration === 'number' ? duration : undefined,
    sections,
    video_url: payload.video_url ?? payload.videoUrl ?? null,
    video_file: payload.video_file ?? payload.videoFile ?? null,
    thumbnail,
    lessonsCount,
  }
}

// ====== SERVICE ======
export const courseService = {
  // LIST - Support both admin and student endpoints
  async list(params: PageParams, useAdminEndpoint = false): Promise<PageResult<CourseSummary>> {
    if (COURSE_USE_MOCK) return buildMockList(params)
    try {
      const endpoint = useAdminEndpoint ? '/admin/courses/' : '/content/courses/'
      console.log('[courseService.list]', endpoint)
      const { data } = await api.get(endpoint, { params })
      const rawItems = Array.isArray(data) ? data : data.results || data.items || data.instance || []
      const items = Array.isArray(rawItems) ? rawItems.map((item: any) => normalizeCourseSummary(item)) : []
      return {
        items,
        total: data.count ?? data.total ?? rawItems.length ?? items.length,
      }
    } catch (error) {
      console.error('courseService.list fallback to mock data:', error)
      return buildMockList(params)
    }

  },

  async listPublicCatalog(): Promise<PageResult<CourseSummary>> {
    if (COURSE_USE_MOCK) return buildMockList({})
    try {
      const { data } = await api.get('/content/courses/')
      const items = (Array.isArray(data) ? data : data.results || data.items || []).map((item: any) =>
        normalizeCourseSummary(item),
      )
      return { items, total: data.count ?? data.total ?? items.length }
    } catch (error) {
      console.error('courseService.listPublicCatalog fallback to mock:', error)
      return buildMockList({})
    }
  },

  async listMyEnrolled(): Promise<CourseSummary[]> {
    if (COURSE_USE_MOCK) return buildMockList({}).items
    try {
      const { data } = await api.get('/content/my-courses/')
      const rawItems = Array.isArray(data) ? data : data.results || data.items || data.instance || []
      return rawItems.map((item: any) => normalizeCourseSummary(item))
    } catch (error) {
      console.error('courseService.listMyEnrolled fallback to mock:', error)
      return buildMockList({}).items
    }
  },

  // DETAIL - Support both admin and student endpoints
  async detail(id: ID, useAdminEndpoint = false): Promise<CourseDetail> {
    if (COURSE_USE_MOCK) return buildMockDetail(id)
    try {
      const endpoint = useAdminEndpoint ? `/admin/courses/${id}/` : `/content/courses/${id}/`
      console.log('[courseService.detail]', endpoint)
      const { data } = await api.get(endpoint)
      return normalizeCourseDetail(data)
    } catch (error) {
      console.error('courseService.detail error:', error)
      throw error
    }
  },

  async myCourses(params: StudentMyCoursesFilters = {}): Promise<StudentMyCoursesResponse> {
    if (COURSE_USE_MOCK) {
      return { base: [], supp: [], all: [] }
    }
    const { data } = await api.get('/student/courses/', { params })
    return {
      base: data.base || [],
      supp: data.supp || [],
      all: data.all || [],
    }
  },

  // CREATE / UPDATE
  create(payload: Partial<CourseDetail> | FormData, useAdminEndpoint = false) {
    if (COURSE_USE_MOCK) return Promise.resolve({ ok: true, id: Date.now() })
    const endpoint = useAdminEndpoint ? '/admin/courses/' : '/content/courses/'
    const config = payload instanceof FormData ? { headers: { 'Content-Type': 'multipart/form-data' } } : {}
    return api.post(endpoint, (payload), config).then((res) => res.data)
  },
  update(id: ID, payload: Partial<CourseDetail> | FormData, useAdminEndpoint = false) {
    if (COURSE_USE_MOCK) return Promise.resolve({ ok: true })
    const endpoint = useAdminEndpoint ? `/admin/courses/${id}/` : `/content/courses/${id}`
    return api.patch(endpoint, payload)
  },

  // DELETE
  async delete(id: ID, useAdminEndpoint = false): Promise<void> {
    if (COURSE_USE_MOCK) return
    const endpoint = useAdminEndpoint ? `/admin/courses/${id}/` : `/content/courses/${id}`
    await api.delete(endpoint)
  },

  // ENROLL (student only)
  async enroll(courseId: ID): Promise<{ success: boolean }> {
    if (COURSE_USE_MOCK) return Promise.resolve({ success: true })
    const { data } = await api.post(`/content/courses/${courseId}/enroll/`)
    return data
  },
  async unenroll(courseId: ID): Promise<{ success: boolean }> {
    if (COURSE_USE_MOCK) return Promise.resolve({ success: true })
    const { data } = await api.delete(`/content/courses/${courseId}/enroll/`)
    return data
  },

  // STATUS / ACTIONS (Admin)
  approve(id: ID) { return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/approve/`) },
  reject(id: ID, reason?: string) {
    return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/reject/`, { reason })
  },
  publish(id: ID) { return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/publish/`) },
  unpublish(id: ID) { return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/unpublish/`) },
  archive(id: ID) { return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/archive/`) },
  restore(id: ID) { return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post(`/admin/courses/${id}/restore/`) },

  // STATUS / ACTIONS (Teacher - use content endpoint)
  async publishCourse(id: ID): Promise<any> {
    if (COURSE_USE_MOCK) return Promise.resolve({ ok: true })
    const { data } = await api.post(`/content/courses/${id}/publish/`, { published: true })
    return data
  },
  async unpublishCourse(id: ID): Promise<any> {
    if (COURSE_USE_MOCK) return Promise.resolve({ ok: true })
    const { data } = await api.patch(`/content/courses/${id}/`, { published: false })
    return data
  },
  async archiveCourse(id: ID): Promise<any> {
    if (COURSE_USE_MOCK) return Promise.resolve({ ok: true })
    const { data } = await api.patch(`/content/courses/${id}/`, { published: false })
    return data
  },
  async restoreCourse(id: ID): Promise<any> {
    if (COURSE_USE_MOCK) return Promise.resolve({ ok: true })
    const { data } = await api.post(`/content/courses/${id}/publish/`, { published: true })
    return data
  },

  // BULK (tuỳ chọn dùng ở trang duyệt)
  bulkApprove(ids: ID[]) {
    return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post('/admin/courses/bulk/', { action: 'approve', ids })
  },
  bulkReject(ids: ID[], reason?: string) {
    return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post('/admin/courses/bulk/', { action: 'reject', ids, reason })
  },
  bulkPublish(ids: ID[]) {
    return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post('/admin/courses/bulk/', { action: 'publish', ids })
  },
  bulkArchive(ids: ID[]) {
    return COURSE_USE_MOCK ? Promise.resolve({ ok: true }) : api.post('/admin/courses/bulk/', { action: 'archive', ids })
  },

  // FILTER OPTIONS
  async listTeachers(): Promise<{ id: ID; name: string }[]> {
    const { data } = await api.get('/account/admin/users/', { params: { role: 'instructor', pageSize: 50 } })
    const users = data.results || data || []
    return users.map((u: any) => ({
      id: u.id,
      name: u.username || u.email
    }))
  },
  subjects(): { label: string; value: Subject }[] {
    return SUBJECTS.map((s) => ({ value: s, label: subjectLabel(s) }))
  },
}

// export async function resolveMediaUrl(url?: string | null): Promise<string | null> {
//   if (!url) return null
//   if (typeof window === 'undefined') return url
//   if (!url.startsWith('/api/media/')) return url
//   if (mediaCache.has(url)) return mediaCache.get(url)!
//   const token = window.localStorage?.getItem('accessToken') || window.sessionStorage?.getItem('accessToken')
//   const headers: Record<string, string> = {}
//   if (token) headers.Authorization = `Bearer ${token}`
//   const res = await fetch(url, {
//     headers,
//     credentials: 'include',
//   })
//   if (!res.ok) throw new Error(`resolveMediaUrl failed: ${res.status}`)
//   const blob = await res.blob()
//   const objectUrl = URL.createObjectURL(blob)
//   mediaCache.set(url, objectUrl)
//   return objectUrl
// }



export async function resolveMediaUrl(url?: string | null): Promise<string | null> {
  if (!url) return null
  if (typeof window === 'undefined') return url
  if (!url.startsWith('/api/media/')) return url

  if (mediaCache.has(url)) return mediaCache.get(url)!

  // 🔥 SỬA Ở ĐÂY: ưu tiên 'access', fallback 'accessToken'
  const token =
    window.localStorage?.getItem('access') ||
    window.sessionStorage?.getItem('access') ||
    window.localStorage?.getItem('accessToken') ||
    window.sessionStorage?.getItem('accessToken')

  const headers: Record<string, string> = {}
  if (token) headers.Authorization = `Bearer ${token}`

  const res = await fetch(url, {
    headers,
    credentials: 'include',
  })
  if (!res.ok) throw new Error(`resolveMediaUrl failed: ${res.status}`)
  const blob = await res.blob()
  const objectUrl = URL.createObjectURL(blob)
  mediaCache.set(url, objectUrl)
  return objectUrl
}
