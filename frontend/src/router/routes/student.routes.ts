// src/router/routes/student.routes.ts
import type { RouteRecordRaw } from 'vue-router'
import { Role } from '@/shared/constants/roles'

export const studentRoutes: RouteRecordRaw[] = [
    {
        path: '/student',
        component: () => import('@/app/layouts/StudentLayout.vue'),
        meta: { requiresAuth: true, roles: [Role.STUDENT] },
        children: [
            {
                meta: { title: 'Student Dashboard' },
                path: 'dashboard',
                name: 'student-dashboard',
                component: () => import('@/modules/dashboard/views/student/StudentDashboard.vue'),
            },
            {
                meta: { title: 'Hồ sơ cá nhân' },
                path: 'profile',
                name: 'student-profile',
                component: () => import('@/pages/common/Profile.vue'),
            },
            {
                meta: { title: 'Đổi mật khẩu' },
                path: 'change-password',
                name: 'student-change-password',
                component: () => import('@/pages/auth/ChangePassword.vue'),
            },
            {
                meta: { title: 'Khóa học của tôi' },
                path: 'courses',
                name: 'student-courses',
                component: () => import('@/modules/courses/views/student/StudentMyCourses.vue'),
            },
            {
                meta: { title: 'Chi tiết khóa học' },
                path: 'courses/:id',
                name: 'student-course-detail',
                component: () => import('@/modules/courses/views/student/StudentCourseDetail.vue'),
            },
        ],
    },
]


