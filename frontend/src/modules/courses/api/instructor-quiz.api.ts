import http from '@/shared/api/http'
import type { QuizSettings, QuizQuestion, QuestionType, AnswerPayload, QuestionPrompt } from '../types/quiz.types'

export const instructorQuizApi = {
    // 1. GET - Lấy chi tiết Quiz (Settings + Questions list potentially)
    getQuizDetail(quizId: string) {
        return http.get<QuizSettings & { questions?: QuizQuestion[] }>(`/api/quiz/instructor/quizzes/${quizId}/`)
    },

    // 🛠️ API Reference: Update Quiz Settings
    updateQuizSettings(quizId: string, data: Partial<QuizSettings>) {
        return http.patch<QuizSettings>(`/api/quiz/instructor/quizzes/${quizId}/`, data)
    },

    // 🗑️ API Reference: Delete Quiz
    deleteQuiz(quizId: string) {
        return http.delete(`/api/quiz/instructor/quizzes/${quizId}/`)
    },

    // --- Questions ---

    // API Documentation: Lấy Danh Sách Câu Hỏi (Instructor)
    getQuestions(quizId: string) {
        return http.get<{ instance: QuizQuestion[] }>(`/api/quiz/instructor/quizzes/${quizId}/questions/`)
    },

    // API Documentation: Tạo Câu Hỏi Mới (Instructor)
    createQuestion(quizId: string, payload: { type: QuestionType; prompt?: QuestionPrompt; answer_payload?: AnswerPayload; score?: number }) {
        return http.post<{ instance: QuizQuestion }>(`/api/quiz/instructor/quizzes/${quizId}/questions/`, payload)
    },

    // 1. GET Question Detail
    getQuestionDetail(questionId: string) {
        return http.get<{ instance: QuizQuestion }>(`/api/quiz/instructor/questions/${questionId}/`)
    },

    // API Document: Instructor Update Question
    updateQuestion(questionId: string, payload: Partial<QuizQuestion>) {
        return http.patch<{ instance: QuizQuestion }>(`/api/quiz/instructor/questions/${questionId}/`, payload)
    },

    // 3. DELETE Question
    deleteQuestion(questionId: string) {
        return http.delete(`/api/quiz/instructor/questions/${questionId}/`)
    }
}
