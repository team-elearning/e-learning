export type Grade = 1 | 2 | 3 | 4 | 5
export type Subject =
  | 'math'
  | 'vietnamese'
  | 'english'
  | 'science'
  | 'history'
  | 'geography'
  | 'art'
  | 'music'
export type DocumentType = 'pdf' | 'video' | 'slide' | 'doc' | 'exercise' | 'exam'

interface Document {
  id: number | string
  title: string
  description: string
  grade: Grade
  subject: Subject
  type: DocumentType
  fileSize: string
  downloads: number
  url?: string
  createdAt?: string
}

interface ListParams {
  q?: string
  grade?: Grade
  subject?: Subject
  type?: DocumentType
  page?: number
  pageSize?: number
}

interface ListResult {
  items: Document[]
  totalPages: number
  currentPage: number
  totalItems: number
}

// Mock data
const mockDocuments: Document[] = [
  {
    id: 1,
    title: 'Bài giảng Toán lớp 1 - Phép cộng trong phạm vi 20',
    description: 'Tài liệu hướng dẫn chi tiết về phép cộng cho học sinh lớp 1',
    grade: 1,
    subject: 'math',
    type: 'pdf',
    fileSize: '2.5 MB',
    downloads: 156,
    url: '/documents/math-grade1-addition.pdf',
  },
  {
    id: 2,
    title: 'Video bài giảng Tiếng Việt lớp 2 - Tập đọc',
    description: 'Video hướng dẫn kỹ năng đọc và phát âm chuẩn',
    grade: 2,
    subject: 'vietnamese',
    type: 'video',
    fileSize: '45.2 MB',
    downloads: 234,
    url: '/videos/vietnamese-grade2-reading.mp4',
  },
  {
    id: 3,
    title: 'Slide Tiếng Anh lớp 3 - Family & Friends',
    description: 'Bài học về gia đình và bạn bè',
    grade: 3,
    subject: 'english',
    type: 'slide',
    fileSize: '8.1 MB',
    downloads: 189,
    url: '/slides/english-grade3-family.pptx',
  },
  {
    id: 4,
    title: 'Bài tập Khoa học lớp 4 - Động vật',
    description: 'Bộ bài tập về phân loại và đặc điểm động vật',
    grade: 4,
    subject: 'science',
    type: 'exercise',
    fileSize: '1.8 MB',
    downloads: 312,
    url: '/exercises/science-grade4-animals.pdf',
  },
  {
    id: 5,
    title: 'Đề thi Toán học kỳ 1 lớp 5',
    description: 'Đề thi mẫu học kỳ 1 môn Toán lớp 5',
    grade: 5,
    subject: 'math',
    type: 'exam',
    fileSize: '1.2 MB',
    downloads: 567,
    url: '/exams/math-grade5-midterm.pdf',
  },
  {
    id: 6,
    title: 'Tài liệu Lịch sử lớp 5 - Văn hóa Việt Nam',
    description: 'Tìm hiểu về văn hóa truyền thống Việt Nam',
    grade: 5,
    subject: 'history',
    type: 'doc',
    fileSize: '3.4 MB',
    downloads: 145,
    url: '/documents/history-grade5-culture.docx',
  },
  {
    id: 7,
    title: 'Bài giảng Toán lớp 2 - Phép trừ',
    description: 'Hướng dẫn phép trừ trong phạm vi 100',
    grade: 2,
    subject: 'math',
    type: 'pdf',
    fileSize: '2.1 MB',
    downloads: 198,
    url: '/documents/math-grade2-subtraction.pdf',
  },
  {
    id: 8,
    title: 'Video Âm nhạc lớp 3 - Học hát dân ca',
    description: 'Bài học hát các bài dân ca truyền thống',
    grade: 3,
    subject: 'music',
    type: 'video',
    fileSize: '62.5 MB',
    downloads: 89,
    url: '/videos/music-grade3-folk-songs.mp4',
  },
  {
    id: 9,
    title: 'Slide Mỹ thuật lớp 4 - Vẽ phong cảnh',
    description: 'Hướng dẫn kỹ thuật vẽ phong cảnh cơ bản',
    grade: 4,
    subject: 'art',
    type: 'slide',
    fileSize: '15.8 MB',
    downloads: 123,
    url: '/slides/art-grade4-landscape.pptx',
  },
  {
    id: 10,
    title: 'Bài tập Tiếng Việt lớp 1 - Tập viết',
    description: 'Bộ bài tập luyện viết chữ cái',
    grade: 1,
    subject: 'vietnamese',
    type: 'exercise',
    fileSize: '1.5 MB',
    downloads: 423,
    url: '/exercises/vietnamese-grade1-writing.pdf',
  },
]

async function list(params: ListParams): Promise<ListResult> {
  // Simulate API delay
  await new Promise((resolve) => setTimeout(resolve, 500))

  let filtered = [...mockDocuments]

  // Filter by search query
  if (params.q) {
    const query = params.q.toLowerCase()
    filtered = filtered.filter(
      (doc) =>
        doc.title.toLowerCase().includes(query) || doc.description.toLowerCase().includes(query),
    )
  }

  // Filter by grade
  if (params.grade) {
    filtered = filtered.filter((doc) => doc.grade === params.grade)
  }

  // Filter by subject
  if (params.subject) {
    filtered = filtered.filter((doc) => doc.subject === params.subject)
  }

  // Filter by type
  if (params.type) {
    filtered = filtered.filter((doc) => doc.type === params.type)
  }

  // Pagination
  const page = params.page || 1
  const pageSize = params.pageSize || 10
  const totalItems = filtered.length
  const totalPages = Math.ceil(totalItems / pageSize)
  const startIndex = (page - 1) * pageSize
  const endIndex = startIndex + pageSize
  const items = filtered.slice(startIndex, endIndex)

  return {
    items,
    totalPages,
    currentPage: page,
    totalItems,
  }
}

async function detail(id: string | number): Promise<Document> {
  await new Promise((resolve) => setTimeout(resolve, 300))
  const doc = mockDocuments.find((d) => String(d.id) === String(id))
  if (!doc) throw new Error('Document not found')
  return doc
}

async function download(id: string | number): Promise<{ url: string }> {
  const doc = await detail(id)
  return { url: doc.url || '#' }
}

function subjects() {
  return [
    { value: 'math' as Subject, label: 'Toán' },
    { value: 'vietnamese' as Subject, label: 'Tiếng Việt' },
    { value: 'english' as Subject, label: 'Tiếng Anh' },
    { value: 'science' as Subject, label: 'Khoa học' },
    { value: 'history' as Subject, label: 'Lịch sử' },
    { value: 'geography' as Subject, label: 'Địa lý' },
    { value: 'art' as Subject, label: 'Mỹ thuật' },
    { value: 'music' as Subject, label: 'Âm nhạc' },
  ]
}

export const documentService = {
  list,
  detail,
  download,
  subjects,
}
