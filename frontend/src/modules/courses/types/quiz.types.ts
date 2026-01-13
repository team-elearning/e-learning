export type QuizGradingMethod = 'highest' | 'average' | 'first' | 'last'

export interface QuizSettings {
    id: string
    title: string
    description: string
    thumbnail?: string
    time_limit: number | null // minutes
    time_open?: string
    time_close?: string
    pass_score: number
    max_attempts: number
    grading_method: QuizGradingMethod
    shuffle_questions: boolean
    show_correct_answer: boolean
    is_published: boolean
}

export type QuestionType =
    | 'multiple_choice_single'
    | 'multiple_choice_multi'
    | 'true_false'
    | 'short_answer'
    | 'essay'
    | 'fill_in_the_blank'
    | 'matching'
    | 'ordering'
    | 'numeric'

export interface QuestionPromptOption {
    id: string
    text: string
}

export interface QuestionMedia {
    type: 'image' | 'video' | 'audio'
    file_id?: string
    url?: string
    caption?: string
}

export interface QuestionPrompt {
    text?: string // or content html
    content?: string // HTML content
    options?: QuestionPromptOption[]
    media?: QuestionMedia[]
    banner_data?: {
        url: string
        file_name: string
        storage_type: string
    }
}

export interface AnswerPayload {
    correct_id?: string
    correct_ids?: string[]
    correct_value?: boolean
    accepted_texts?: string[]
    matches?: Record<string, string>
    grading_rubric?: string
    model_answer?: string
    explanation?: string
    allow_partial?: boolean
    case_sensitive?: boolean
}

export interface QuizQuestion {
    id: string
    quiz_id?: string
    position: number
    type: QuestionType
    score: number
    prompt: QuestionPrompt
    answer_payload?: AnswerPayload // Only for instructor
    hint?: {
        text: string
    }
}

export interface QuizDetailResponse extends QuizSettings {
    questions?: QuizQuestion[] // Assuming the first API returns questions too? The doc says "Backend trả về ... danh sách câu hỏi"
}
