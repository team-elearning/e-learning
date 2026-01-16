import http from '@/shared/api/http'
import type {
    StudentCourse,
    Course,
    BlockDetail,
    QuizAttempt,
    StudentQuizQuestion,
    QuizAttemptResult,
    HeartbeatRequest,
    BlockProgressResponse,
    CourseResumeResponse,
    CourseProgressResponse
} from '../types/course.types'

export const studentCoursesApi = {
    getMediaCookies: () => http.post('/api/media/cookies/', undefined, { withCredentials: true }),
    getMyCourses: () => http.get<StudentCourse[]>('/api/content/my-courses/'),
    getAllCourses: () => http.get<Course[]>('/api/content/courses/'),
    enrollCourse: (id: string) => http.post(`/api/content/courses/${id}/enroll/`),
    unenrollCourse: (id: string) => http.delete(`/api/content/courses/${id}/unenroll/`),
    getCourseDetail: (id: string) => http.get<Course>(`/api/content/courses/${id}/`),
    getBlockDetail: (id: string) => http.get<BlockDetail>(`/api/content/blocks/${id}/`),

    // Tracking APIs
    getBlockHeartbeat: (blockId: string) => http.get<BlockProgressResponse>(`/api/progress/tracking/heartbeat/blocks/${blockId}/`),
    sendBlockHeartbeat: (blockId: string, data: HeartbeatRequest) => http.post<BlockProgressResponse>(`/api/progress/tracking/heartbeat/blocks/${blockId}/`, data),
    getCourseResume: (courseId: string) => http.get<CourseResumeResponse>(`/api/progress/courses/${courseId}/resume/`),
    getCourseProgress: (courseId: string) => http.get<CourseProgressResponse>(`/api/progress/courses/${courseId}/progress/`),
    resetCourseProgress: (enrollmentId: string) => http.post(`/api/enrollments/${enrollmentId}/reset/`),

    // Quiz APIs
    startQuizAttempt: (quizId: string) => http.get<QuizAttempt>(`/api/progress/quizzes/${quizId}/attempt/`),
    getQuizQuestion: (attemptId: string, questionId: string) => http.get<StudentQuizQuestion>(`/api/progress/attempts/${attemptId}/questions/${questionId}/`),
    saveQuestionDraft: (attemptId: string, questionId: string, data: any) => http.put(`/api/progress/attempts/${attemptId}/questions/${questionId}/draft/`, data),
    submitQuestion: (attemptId: string, questionId: string) => http.post(`/api/progress/attempts/${attemptId}/questions/${questionId}/submit/`),
    finishQuizAttempt: (attemptId: string) => http.post<QuizAttemptResult>(`/api/progress/quizzes/attempts/${attemptId}/finish/`),
}
