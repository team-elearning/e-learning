// src/router/routes/admin.routes.ts
import type { RouteRecordRaw } from 'vue-router'
import { Role } from '@/shared/constants/roles'

export const adminRoutes: RouteRecordRaw[] = [
    {
        path: '/admin',
        component: () => import('@/app/layouts/AdminLayout.vue'),
        meta: { requiresAuth: true, roles: [Role.ADMIN] },
        children: [
            {
                meta: { title: 'Admin Dashboard' },
                path: 'dashboard',
                name: 'admin-dashboard',
                component: () => import('@/modules/dashboard/views/admin/AdminDashboard.vue'),
            },
            {
                meta: { title: 'Quản lý người dùng' },
                path: 'users',
                name: 'admin-users',
                component: () => import('@/modules/dashboard/views/admin/AdminUsers.vue'),
            },
            {
                meta: { title: 'Hồ sơ cá nhân' },
                path: 'profile',
                name: 'admin-profile',
                component: () => import('@/pages/common/Profile.vue'),
            },
            {
                meta: { title: 'Đổi mật khẩu' },
                path: 'change-password',
                name: 'admin-change-password',
                component: () => import('@/pages/auth/ChangePassword.vue'),
            },
        ],
    },
]
