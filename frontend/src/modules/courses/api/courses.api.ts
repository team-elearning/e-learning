import http from '@/shared/api/http'
import type { Course, BlockDetail, Quiz } from '../types/course.types'

export const coursesApi = {
    getInstructorCourses() {
        return http.get<Course[]>('/api/content/instructor/courses/')
    },
    getCourseDetail(id: string) {
        return http.get<Course>(`/api/content/instructor/courses/${id}/`)
    },
    getBlockDetail(id: string) {
        return http.get<BlockDetail>(`/api/content/instructor/blocks/${id}/`)
    },
    getQuizDetail(id: string) {
        return http.get<Quiz>(`/api/quiz/instructor/quizzes/${id}/`)
    },
}
