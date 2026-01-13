export interface Subject {
    id: string
    title: string
    slug: string
}

export interface Category {
    id: string
    name: string
    slug: string
}

export interface Tag {
    id: string
    name: string
    slug: string
}

export interface CourseStats {
    total_modules: number
    total_lessons: number
    total_videos: number
    total_quizzes: number
    total_seconds: number
    duration_display: string
    students_count: number
}

export interface BlockPayloadRichText {
    html_content: string
}

export interface BlockPayloadVideo {
    file_path: string
    file_name: string
    file_size: number
    storage_type: string
    duration: number
    staging_video_id?: string
    url?: string
    video_url?: string
}

export interface BlockPayloadFile {
    file_path: string
    file_name: string
    file_size?: number
    storage_type?: string
    staging_file_id?: string
}

export interface BlockPayloadQuiz {
    title?: string
    quiz_id?: string // Placeholder
}

export interface ContentBlock {
    id: string
    title: string
    type: 'rich_text' | 'video' | 'pdf' | 'docx' | 'quiz'
    position: number
    payload: BlockPayloadRichText | BlockPayloadVideo | BlockPayloadFile | BlockPayloadQuiz | any
    updated_at?: string
}

export interface BlockDetailResponse {
    instance: ContentBlock
}

export interface Lesson {
    id: string
    module_id: string
    title: string
    position: number
    content_blocks: ContentBlock[]
}

export interface CourseModule {
    id: string
    title: string
    position: number
    lessons: Lesson[]
}

export interface BlockDetail {
    id: string
    title: string
    type: 'rich_text' | 'video' | 'pdf' | 'docx' | 'quiz'
    position: number
    payload: {
        file_id?: string
        file_url?: string
        video_id?: string
        video_url?: string
        url?: string // Direct URL
        content?: string
        html_content?: string
        quiz_id?: string
        // metadata
        file_name?: string
        duration?: number
        file_size?: number
    }
    icon_key?: string
    instance?: any // handling heartbeat wrapper
}

export interface QuizOption {
    id: string
    text: string
}

export interface QuizPrompt {
    content: string
    options?: QuizOption[]
    media?: any[]
}

export interface QuizAnswerPayload {
    correct_id?: string
    correct_ids?: string[]
    correct_value?: boolean
    accepted_texts?: string[]
    explanation?: string
    case_sensitive?: boolean
    allow_partial?: boolean
}

export interface Question {
    id: string
    type: 'multiple_choice_single' | 'multiple_choice_multi' | 'true_false' | 'short_answer' | string
    prompt: QuizPrompt
    position: number
    answer_payload: QuizAnswerPayload
    hint: any
}

export interface Quiz {
    id: string
    title: string
    description?: string
    questions: Question[]
    owner_id: string
    owner_name: string
}

export interface Course {
    id: string
    title: string
    slug: string
    description: string
    short_description: string
    price: string
    currency: string
    is_free: boolean
    published: boolean
    grade: string
    owner_id: string
    owner_name: string
    subject: Subject
    categories: Category[]
    tags: Tag[]
    thumbnail_url: string
    stats: CourseStats
    published_at: string | null
    created_at: string
    updated_at: string
    modules?: CourseModule[] // Added optional modules
}

// Student-specific types
export interface MyProgress {
    enrollment_id: string
    course_id: string
    user_id: string
    percent_completed: number
    is_completed: boolean
    completed_at: string | null
    last_accessed_at: string
    enrolled_at: string
    completed_lessons_count: number
    total_lessons_count: number
    status_label: 'not_started' | 'in_progress' | 'completed'
}

export interface StudentCourse extends Course {
    my_progress?: MyProgress
    percent_completed?: number
}

// Tracking & Heartbeat Types
export interface HeartbeatRequest {
    time_spent_add: number // seconds
    interaction_data: {
        video_timestamp?: number
        playback_rate?: number
        scroll_position?: number
        read_complete?: boolean
        [k: string]: any
    }
}

export interface BlockProgressResponse {
    status?: 'synced'
    is_completed: boolean
    progress: number
    instance?: {
        id: string | null
        block_id: string
        status: 'not_started' | 'in_progress' | 'completed'
        interaction_data: any
        last_accessed_at: string
    }
}

export interface CourseResumeResponse {
    block_id: string | null // null if course is empty? or just standard behavior
    next_block_id?: string // logical next
}

export interface CourseProgressResponse {
    enrollment_id: string
    course_id: string
    percent_completed: number
    is_completed: boolean
    status_label: 'not_started' | 'in_progress' | 'completed'
    last_accessed_at?: string
}

// Quiz Types
export interface QuizAttempt {
    attempt_id: string
    quiz_title?: string
    status: 'in_progress' | 'completed' | 'graded' | string
    score?: number
    max_score?: number
    time_start: string
    end_time?: string | null
    questions_order: string[] // List of question IDs
    time_limit_seconds?: number | null
    current_index?: number
}

export interface StudentQuizQuestion {
    id: string
    type: 'multiple_choice_single' | 'multiple_choice_multi' | 'true_false' | 'short_answer' | string
    prompt: QuizPrompt // Contains content, options need handling
    shuffled_options?: QuizOption[] // Pre-shuffled from backend
    current_answer?: any // Draft answer
    submission_result?: {
        is_correct: boolean
        score: number
        feedback?: string
        correct_answer_data?: any
    }
}

export interface QuizAttemptResult {
    score: number
    max_score: number
    percentage: number
    is_passed: boolean
    items: QuizResultItem[]
}

export interface QuizResultItem {
    question_id: string
    question_text: string
    question_type: string
    options: QuizOption[]
    user_answer_text: string
    correct_answer_text: string
    is_correct: boolean
    score: number
    max_score: number
    feedback?: string
}

