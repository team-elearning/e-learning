import { createRouter, createWebHistory } from 'vue-router'
import { publicRoutes } from './routes/public.routes'
import { adminRoutes } from './routes/admin.routes'
import { teacherRoutes } from './routes/teacher.routes'
import { studentRoutes } from './routes/student.routes'
import { authGuard } from './guards/auth.guard'
import { roleGuard } from './guards/role.guard'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    ...publicRoutes,
    ...adminRoutes,
    ...teacherRoutes,
    ...studentRoutes,
  ],
})

router.beforeEach(authGuard)
router.beforeEach(roleGuard)
