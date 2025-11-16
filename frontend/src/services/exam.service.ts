// src/services/exam.service.ts
// NOTE: MOCK 100%. Khi nối API thật, chỉ cần đổi USE_MOCK=false và map endpoints.

export type ID = string | number
export type Level = 'Khối 1–2' | 'Khối 3–5'
export type ExamStatus = 'draft' | 'published' | 'archived'

export type QType = 'single' | 'multi' | 'boolean' | 'fill' | 'match' | 'order'

export interface Choice {
  id: string
  text: string
}
export interface MatchPair {
  left: string
  right: string
} // cho 'match'
export interface QuestionBase {
  id: ID
  type: QType
  text: string
  score: number
  // hiển thị phụ
  image?: string
  hint?: string
}

export type Question =
  | (QuestionBase & { type: 'single' | 'multi'; choices: Choice[]; answer: string[] })
  | (QuestionBase & { type: 'boolean'; answer: boolean })
  | (QuestionBase & { type: 'fill'; blanks: number; answer: string[] })
  | (QuestionBase & { type: 'match'; pairs: MatchPair[] }) // chấm điểm theo đúng mapping
  | (QuestionBase & { type: 'order'; items: string[]; answer: string[] })

export interface ExamSummary {
  id: ID
  title: string
  level: Level
  durationSec: number
  passScore: number // điểm đạt tối thiểu
  questionsCount: number
  status: ExamStatus
  updatedAt: string
}

export interface ExamDetail extends ExamSummary {
  description?: string
  shuffleQuestions?: boolean
  shuffleChoices?: boolean
  questions: Question[]
}

export interface AttemptQuestion {
  id: ID
  type: QType
  text: string
  score: number
  choices?: Choice[]
  blanks?: number
  pairs?: MatchPair[]
  items?: string[]
}

export interface Attempt {
  id: string
  examId: ID
  startedAt: string
  deadlineAt: string // = started + duration
  questions: AttemptQuestion[]
  // bài làm (tối giản)
  answers: Record<string, any>
}

export interface AttemptResult {
  attemptId: string
  examId: ID
  totalScore: number
  maxScore: number
  correctCount: number
  totalCount: number
  passed: boolean
  detail: Array<{ qid: ID; score: number; max: number }>
}

const USE_MOCK = true

// ========= MOCK BANK GENERATOR =========
function randPick<T>(arr: T[], n: number): T[] {
  const a = arr.slice()
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[a[i], a[j]] = [a[j], a[i]]
  }
  return a.slice(0, n)
}

function makeId(prefix: string, i: number) {
  return `${prefix}_${i}_${Math.random().toString(36).slice(2, 7)}`
}

function makeSingle(i: number): Question {
  const choices = Array.from({ length: 4 }, (_, k) => ({
    id: `c${k + 1}`,
    text: `Phương án ${k + 1}`,
  }))
  const ans = [choices[i % 4].id]
  return {
    id: makeId('qS', i),
    type: 'single',
    text: `Câu đơn #${i}`,
    score: 1,
    choices,
    answer: ans,
  }
}

function makeMulti(i: number): Question {
  const choices = Array.from({ length: 5 }, (_, k) => ({
    id: `c${k + 1}`,
    text: `Đáp án ${k + 1}`,
  }))
  const answer = choices.filter((_, idx) => (i + idx) % 2 === 0).map((c) => c.id) // vài đáp án đúng
  return { id: makeId('qM', i), type: 'multi', text: `Chọn nhiều #${i}`, score: 2, choices, answer }
}

function makeBoolean(i: number): Question {
  return {
    id: makeId('qB', i),
    type: 'boolean',
    text: `Đúng / Sai #${i}`,
    score: 1,
    answer: i % 2 === 0,
  }
}

function makeFill(i: number): Question {
  const blanks = 2
  const answer = [`kw${i}`, `ans${i}`]
  return { id: makeId('qF', i), type: 'fill', text: `Điền từ #${i}`, score: 2, blanks, answer }
}

function makeMatch(i: number): Question {
  const pairs: MatchPair[] = [
    { left: 'Hà Nội', right: 'Việt Nam' },
    { left: 'Tokyo', right: 'Nhật Bản' },
    { left: 'Bangkok', right: 'Thái Lan' },
  ]
  return { id: makeId('qX', i), type: 'match', text: `Nối cặp #${i}`, score: 3, pairs }
}

function makeOrder(i: number): Question {
  const items = ['B1', 'B2', 'B3', 'B4']
  const answer = items.slice() // đúng thứ tự
  return { id: makeId('qO', i), type: 'order', text: `Sắp xếp #${i}`, score: 2, items, answer }
}

function buildMockExam(id: number, level: Level): ExamDetail {
  const bank: Question[] = [
    ...Array.from({ length: 10 }, (_, i) => makeSingle(i)),
    ...Array.from({ length: 6 }, (_, i) => makeMulti(i)),
    ...Array.from({ length: 6 }, (_, i) => makeBoolean(i)),
    ...Array.from({ length: 4 }, (_, i) => makeFill(i)),
    ...Array.from({ length: 3 }, (_, i) => makeMatch(i)),
    ...Array.from({ length: 3 }, (_, i) => makeOrder(i)),
  ]
  const questions = randPick(bank, 18)
  const durationSec = level === 'Khối 1–2' ? 20 * 60 : 30 * 60

  return {
    id,
    title: `Đề thi #${id} – ${level}`,
    level,
    durationSec,
    passScore: 12, // ví dụ
    questionsCount: questions.length,
    status: 'published',
    updatedAt: new Date().toISOString(),
    description: 'Đề thi chính thức do giáo viên tạo.',
    shuffleQuestions: true,
    shuffleChoices: true,
    questions,
  }
}

const MOCK_EXAMS: ExamDetail[] = [
  // Đề ôn luyện (ID 1-10)
  buildMockExam(1, 'Khối 1–2'),
  buildMockExam(2, 'Khối 1–2'),
  buildMockExam(3, 'Khối 3–5'),
  buildMockExam(4, 'Khối 3–5'),
  buildMockExam(5, 'Khối 1–2'),
  buildMockExam(6, 'Khối 3–5'),
  // Đề thi chính thức (ID 101+)
  buildMockExam(101, 'Khối 1–2'),
  buildMockExam(102, 'Khối 1–2'),
  buildMockExam(201, 'Khối 3–5'),
  buildMockExam(202, 'Khối 3–5'),
]

// ---- Mock submissions cho trang chấm bài ----
export type SubmissionStatus = 'pending' | 'graded'
export interface SubmissionRow {
  id: number
  examId: ID
  studentName: string
  classCode: string
  submittedAt: string
  score: number | null
  status: SubmissionStatus
}

function makeExamSubmissions(examId: number): SubmissionRow[] {
  const total = (Number(examId) % 7) + 9
  return Array.from({ length: total }).map((_, i) => {
    const sid = Number(examId) * 1000 + i + 1
    const graded = (i + Number(examId)) % 3 !== 0
    const score = graded ? Math.round((6 + ((i + Number(examId)) % 5) + 0.1) * 10) / 10 : null
    const cls = `L${(Number(examId) % 4) + 1}${String((i % 3) + 1).padStart(2, '0')}`
    const name = `HS ${(Number(examId) % 9) + 1}${String(i + 1).padStart(2, '0')}`
    const submittedAt = new Date(Date.now() - (i + 1) * 36e5).toLocaleString()
    return {
      id: sid,
      examId: Number(examId),
      studentName: name,
      classCode: cls,
      submittedAt,
      score,
      status: graded ? 'graded' : 'pending',
    }
  })
}

// ========= HELPERS =========
function toSummary(d: ExamDetail): ExamSummary {
  return {
    id: d.id,
    title: d.title,
    level: d.level,
    durationSec: d.durationSec,
    passScore: d.passScore,
    questionsCount: d.questionsCount,
    status: d.status,
    updatedAt: d.updatedAt,
  }
}

function scoreQuestion(q: Question, ans: any): number {
  switch (q.type) {
    case 'single': {
      const ok = Array.isArray(ans) ? ans[0] : ans
      return q.answer.includes(String(ok)) ? q.score : 0
    }
    case 'multi': {
      const a = new Set((ans as string[]) || [])
      const gold = new Set(q.answer)
      const correctAll = q.answer.every((x) => a.has(x)) && a.size === gold.size
      return correctAll ? q.score : 0
    }
    case 'boolean':
      return (ans === true || ans === false) && ans === q.answer ? q.score : 0
    case 'fill': {
      const given = (ans as string[]) || []
      let c = 0
      for (let i = 0; i < q.blanks; i++) {
        if ((given[i] || '').trim().toLowerCase() === (q.answer[i] || '').toLowerCase()) c++
      }
      return (c / q.blanks) * q.score
    }
    case 'match': {
      const given = (ans as string[]) || []
      const gold = q.pairs.map((p) => p.right)
      let c = 0
      for (let i = 0; i < gold.length; i++) if (given[i] === gold[i]) c++
      return (c / gold.length) * q.score
    }
    case 'order': {
      const given = (ans as string[]) || []
      const gold = q.answer
      let c = 0
      for (let i = 0; i < gold.length; i++) if (given[i] === gold[i]) c++
      return (c / gold.length) * q.score
    }
  }
}

// ========= SERVICE API (MOCK) =========
export const examService = {
  async list(params?: { level?: Level; q?: string }): Promise<ExamSummary[]> {
    let list = MOCK_EXAMS.slice()
    if (params?.level) list = list.filter((e) => e.level === params.level)
    if (params?.q) {
      const key = params.q.toLowerCase()
      list = list.filter((e) => e.title.toLowerCase().includes(key))
    }
    return list.map(toSummary)
  },

  async detail(id: ID): Promise<ExamDetail> {
    const found = MOCK_EXAMS.find((e) => String(e.id) === String(id))
    if (!found) throw new Error('Không tìm thấy đề thi')
    return JSON.parse(JSON.stringify(found))
  },

  // >>> API mock trả về danh sách bài nộp cho trang Xem điểm
  async submissions(examId: ID) {
    return makeExamSubmissions(Number(examId))
  },

  async startAttempt(examId: ID): Promise<Attempt> {
    const d = await this.detail(examId)
    let qs = d.questions.slice()
    if (d.shuffleQuestions) qs = randPick(qs, qs.length)
    if (d.shuffleChoices) {
      qs = qs.map((q) =>
        q.type === 'single' || q.type === 'multi'
          ? { ...q, choices: randPick(q.choices, q.choices.length) }
          : q,
      )
    }
    const att: Attempt = {
      id: 'att_' + Math.random().toString(36).slice(2, 9),
      examId,
      startedAt: new Date().toISOString(),
      deadlineAt: new Date(Date.now() + d.durationSec * 1000).toISOString(),
      questions: qs.map((q) => {
        const base: AttemptQuestion = {
          id: q.id,
          type: q.type,
          text: q.text,
          score: q.score,
        }
        if (q.type === 'single' || q.type === 'multi') base.choices = q.choices
        if (q.type === 'fill') base.blanks = q.blanks
        if (q.type === 'match') base.pairs = q.pairs
        if (q.type === 'order') base.items = q.answer
        return base
      }),
      answers: {},
    }
    localStorage.setItem(`attempt:${att.id}`, JSON.stringify(att))
    return att
  },

  async submit(
    examId: ID,
    attemptId: string,
    answers: Record<string, any>,
  ): Promise<AttemptResult> {
    const d = await this.detail(examId)
    let totalScore = 0
    let maxScore = 0
    let correctCount = 0
    const detail: AttemptResult['detail'] = []

    for (const q of d.questions) {
      const ans = answers[String(q.id)]
      const got = scoreQuestion(q, ans)
      totalScore += got
      maxScore += q.score
      if (Math.abs(got - q.score) < 1e-6) correctCount++
      detail.push({ qid: q.id, score: Number(got.toFixed(2)), max: q.score })
    }

    const passed = totalScore >= d.passScore
    const res: AttemptResult = {
      attemptId: attemptId,
      examId,
      totalScore: Number(totalScore.toFixed(2)),
      maxScore,
      correctCount,
      totalCount: d.questions.length,
      passed,
      detail,
    }
    localStorage.setItem(`attempt:${attemptId}:result`, JSON.stringify(res))
    return res
  },
}
