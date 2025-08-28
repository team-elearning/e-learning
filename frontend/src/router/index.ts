
import { createRouter, createWebHistory } from 'vue-router';
import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
	
	{
		path: '/login',
		name: 'Login',
		component: () => import('../views/auth/LoginPage.vue'),
	},
	{
		path: '/register',
		name: 'Register',
		component: () => import('../views/auth/RegisterPage.vue'),
	},
	{
		path: '/student/dashboard',
		name: 'StudentDashboard',
		component: () => import('../views/student/Dashboard.vue'),
	},
	{
		path: '/student/lesson/:id',
		name: 'LessonDetail',
		component: () => import('../views/student/LessonDetail.vue'),
		props: true,
	},
	{
		path: '/parent/reports',
		name: 'ParentReports',
		component: () => import('../views/parent/Reports.vue'),
	},
	{
		path: '/admin/content',
		name: 'ContentManager',
		component: () => import('../views/admin/ContentManager.vue'),
	},
	{
		path: '/admin/users',
		name: 'AdminUsers',
		component: () => import('../views/admin/Users.vue'),
	},
];

console.log('Router routes:', routes);
const router = createRouter({
	history: createWebHistory(),
	routes,
});
console.log('Router instance:', router);
export default router;
