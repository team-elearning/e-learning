import type { RouteRecordRaw } from 'vue-router'

export const publicRoutes: RouteRecordRaw[] = [
    {
        path: '/',
        component: () => import('@/app/layouts/PublicLayout.vue'),
        children: [
            { path: '', name: 'landing', component: () => import('@/pages/common/Landing.vue') },
        ],
    },
    {
        path: '/login',
        component: () => import('@/app/layouts/AuthLayout.vue'),
        children: [{ path: '', name: 'login', component: () => import('@/pages/auth/Login.vue') }],
    },
    {
        path: '/register',
        component: () => import('@/app/layouts/AuthLayout.vue'),
        children: [
            { path: '', name: 'register', component: () => import('@/pages/auth/Register.vue') },
        ],
    },
    {
        path: '/forgot-password',
        component: () => import('@/app/layouts/AuthLayout.vue'),
        children: [{ path: '', name: 'forgot-password', component: () => import('@/pages/auth/ForgotPassword.vue') }],
    },
    {
        path: '/password/reset/confirm/:uid/:token',
        component: () => import('@/app/layouts/AuthLayout.vue'),
        children: [{ path: '', name: 'reset-password', component: () => import('@/pages/auth/ResetPassword.vue') }],
    },
    {
        path: '/forbidden',
        component: () => import('@/app/layouts/AuthLayout.vue'),
        children: [{ path: '', name: 'forbidden', component: () => import('@/pages/common/Forbidden.vue') }],
    },
    { path: '/', redirect: '/login' },
    { path: '/:pathMatch(.*)*', redirect: '/login' },
]
