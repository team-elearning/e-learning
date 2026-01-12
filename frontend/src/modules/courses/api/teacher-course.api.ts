import http from '@/shared/api/http'
import type { Course, BlockDetailResponse } from '../types/course.types'

// Types for request payloads
export interface CreateCourseDto {
    title: string
    slug?: string
    description?: string
    grade?: number
    subject?: string
    price?: number
    categories?: string[]
    tags?: string[]
    image_id?: string
    published?: boolean
}

export interface UpdateCourseDto extends Partial<CreateCourseDto> { }

export interface CreateModuleDto {
    title?: string
}

export interface CreateLessonDto {
    title?: string
}

export interface CreateBlockDto {
    type: 'rich_text' | 'video' | 'quiz' | 'file' | 'pdf' | 'docx' | 'audio'
    title?: string
    content?: string
    url?: string
    position?: number
    file_id?: string
    payload?: any
}

export interface ReorderDto {
    ids: string[] // generic for modules, blocks
}

export interface ReorderLessonDto {
    lesson_ids: string[]
}

export interface UploadInitResponse {
    file_id: string
    upload_url: string
    upload_fields: Record<string, string>
}

export interface UploadInitDto {
    filename: string
    file_type: string
    file_size: number
    component: 'course_thumbnail' | 'lesson_material' | 'user_avatar' | 'site_logo' | 'quiz_attachment' | 'public_attachment'
}

// Instructor Course API
export const teacherCourseApi = {
    // --- MEDIA ---
    uploadInit: (data: UploadInitDto) => http.post<UploadInitResponse>('/api/media/upload/init/', data),
    uploadConfirm: (fileId: string) => http.post(`/api/media/upload/confirm/${fileId}/`, {}),
    getMediaCookies: () => http.post('/api/media/cookies/'),

    // --- COURSE METADATA ---
    createCourse: (data: CreateCourseDto) => http.post<{ id: string }>('/api/content/instructor/courses/', data),
    updateCourse: (id: string, data: UpdateCourseDto) => http.patch(`/api/content/instructor/courses/${id}/`, data),
    deleteCourse: (id: string) => http.delete(`/api/content/instructor/courses/${id}/`),
    getCourseDetail: (id: string) => http.get<Course>(`/api/content/instructor/courses/${id}/`), // Assuming this exists or using public

    // --- MODULES ---
    createModule: (courseId: string, data: CreateModuleDto) => http.post(`/api/content/instructor/courses/${courseId}/modules/`, data),
    getModules: (courseId: string) => http.get(`/api/content/instructor/courses/${courseId}/modules/`),
    updateModule: (moduleId: string, data: { title: string }) => http.patch(`/api/content/instructor/modules/${moduleId}/`, data),
    deleteModule: (moduleId: string) => http.delete(`/api/content/instructor/modules/${moduleId}/`),
    reorderModules: (courseId: string, moduleIds: string[]) => http.put(`/api/content/instructor/courses/${courseId}/modules/reorder/`, { module_ids: moduleIds }), // Prompt said "danh sách TẤT CẢ module_id"
    // --- LESSONS ---
    createLesson: (moduleId: string, data: CreateLessonDto) => http.post(`/api/content/instructor/modules/${moduleId}/lessons/`, data),
    getLessons: (moduleId: string) => http.get(`/api/content/instructor/modules/${moduleId}/lessons/`),
    updateLesson: (lessonId: string, data: { title: string }) => http.patch(`/api/content/instructor/lessons/${lessonId}/`, data),
    deleteLesson: (lessonId: string) => http.delete(`/api/content/instructor/lessons/${lessonId}/`),
    reorderLessons: (courseId: string, targetModuleId: string, lessonIds: string[]) =>
        http.put(`/api/content/instructor/courses/${courseId}/modules/${targetModuleId}/lessons/reorder/`, { lesson_ids: lessonIds }),

    // --- CONTENT BLOCKS ---
    getBlocks: (lessonId: string) => http.get(`/api/content/instructor/lessons/${lessonId}/blocks/`),
    getBlockDetail: (blockId: string) => http.get<BlockDetailResponse>(`/api/content/instructor/blocks/${blockId}/`),
    createBlock: (lessonId: string, data: CreateBlockDto) => http.post<{ id: string; quiz_id?: string }>(`/api/content/instructor/lessons/${lessonId}/blocks/`, data),
    updateBlock: (blockId: string, data: any) => http.patch(`/api/content/instructor/blocks/${blockId}/`, data),
    deleteBlock: (blockId: string) => http.delete(`/api/content/instructor/blocks/${blockId}/`),
    reorderBlocks: (lessonId: string, blockIds: string[]) => http.put(`/api/content/lessons/${lessonId}/blocks/reorder/`, { block_ids: blockIds }),
}
