// src/router/routes/teacher.routes.ts
import type { RouteRecordRaw } from 'vue-router'
import { Role } from '@/shared/constants/roles'

export const teacherRoutes: RouteRecordRaw[] = [
    {
        path: '/teacher',
        component: () => import('@/app/layouts/TeacherLayout.vue'),
        meta: { requiresAuth: true, roles: [Role.TEACHER] },
        children: [
            {
                meta: { title: 'Teacher Dashboard' },
                path: 'dashboard',
                name: 'teacher-dashboard',
                component: () => import('@/modules/dashboard/views/teacher/TeacherDashboard.vue'),
            },
            {
                meta: { title: 'Tạo khóa học mới' },
                path: 'courses/create',
                name: 'teacher-course-create',
                component: () => import('@/modules/courses/views/teacher/create/TeacherCourseCreate.vue'),
            },
            {
                meta: { title: 'Chỉnh sửa khóa học' },
                path: 'courses/:id/edit',
                name: 'teacher-course-edit',
                component: () => import('@/modules/courses/views/teacher/create/TeacherCourseEditor.vue'),
            },
            {
                meta: { title: 'Teacher Courses' },
                path: 'courses',
                name: 'teacher-courses',
                component: () => import('@/modules/courses/views/teacher/TeacherCourses.vue'),
            },
            {
                meta: { title: 'Teacher Course Detail' },
                path: 'courses/:id',
                name: 'teacher-course-detail',
                component: () => import('@/modules/courses/views/teacher/TeacherCourseDetail.vue'),
            },
            {
                meta: { title: 'Hồ sơ cá nhân' },
                path: 'profile',
                name: 'teacher-profile',
                component: () => import('@/pages/common/Profile.vue'),
            },
            {
                meta: { title: 'Đổi mật khẩu' },
                path: 'change-password',
                name: 'teacher-change-password',
                component: () => import('@/pages/auth/ChangePassword.vue'),
            },
        ],
    },
]
