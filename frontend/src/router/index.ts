// src/router/index.ts
import { createRouter, createWebHistory, type RouteRecordRaw } from "vue-router"

// Layouts (import tĩnh cho ổn định)
import AdminLayout from "@/layouts/AdminLayout.vue"
import TeacherLayout from "@/layouts/TeacherLayout.vue"
import StudentLayout from "@/layouts/StudentLayout.vue"
import AuthLayout from "@/layouts/AuthLayout.vue"

// Pinia store (dùng trong guard)
import { useAuthStore } from "@/store/auth.store"

const routes: RouteRecordRaw[] = [
  // Landing (tuỳ chọn: nếu muốn vào thẳng /auth/login thì đổi route "/" thành redirect)
  { path: "/", component: () => import("@/pages/common/Landing.vue") },

  // Auth
  {
    path: "/auth",
    component: AuthLayout,
    children: [
      { path: "", redirect: "/auth/login" },
      { path: "login", component: () => import("@/pages/auth/Login.vue") },
      { path: "register", component: () => import("@/pages/auth/Register.vue") },
      { path: "forgot-password", component: () => import("@/pages/auth/ForgotPassword.vue") },
      { path: "reset-password", component: () => import("@/pages/auth/ResetPassword.vue") },
    ],
  },

  // Admin
  {
    path: "/admin",
    component: AdminLayout,
    meta: { role: "admin" },
    children: [
      { path: "", redirect: "/admin/dashboard" },

      { path: "dashboard", component: () => import("@/pages/admin/dashboard/Dashboard.vue"), meta: { title: "Trang chủ" } },

      // Users
      { path: "users", component: () => import("@/pages/admin/users/Users.vue"), meta: { title: "Quản lý người dùng" } },
      { path: "users/:id", component: () => import("@/pages/admin/users/UserDetail.vue"), meta: { title: "Chi tiết người dùng" } },

      // Courses
      { path: "courses", component: () => import("@/pages/admin/courses/Courses.vue"), meta: { title: "Quản lý khóa học" } },
      { path: "courses/approval", component: () => import("@/pages/admin/courses/CourseApproval.vue"), meta: { title: "Duyệt khóa học" } },
      { path: "courses/:id", component: () => import("@/pages/admin/courses/CourseDetail.vue"), meta: { title: "Chi tiết khóa học" } },

      // System
      { path: "system", component: () => import("@/pages/admin/system/SystemConfig.vue"), meta: { title: "Cấu hình hệ thống" } },
      { path: "system/activity", component: () => import("@/pages/admin/system/ActivityLogs.vue"), meta: { title: "Log hoạt động" } },
      { path: "system/security", component: () => import("@/pages/admin/system/SecuritySettings.vue"), meta: { title: "Bảo mật hệ thống" } },

      // Reports
      { path: "reports/revenue", component: () => import("@/pages/admin/reports/RevenueReports.vue"), meta: { title: "Báo cáo doanh thu" } },
      { path: "reports/users", component: () => import("@/pages/admin/reports/UserAnalytics.vue"), meta: { title: "Phân tích người dùng" } },
      { path: "reports/learning", component: () => import("@/pages/admin/reports/LearningAnalytics.vue"), meta: { title: "Phân tích học tập" } },
      { path: "reports/content", component: () => import("@/pages/admin/reports/ContentAnalytics.vue"), meta: { title: "Phân tích nội dung" } },
      { path: "reports/export", component: () => import("@/pages/admin/reports/ReportsExport.vue"), meta: { title: "Xuất báo cáo" } },

      // Transactions
      { path: "transactions", component: () => import("@/pages/admin/transactions/Transactions.vue"), meta: { title: "Giao dịch" } },
      { path: "transactions/:id", component: () => import("@/pages/admin/transactions/TransactionDetail.vue"), meta: { title: "Chi tiết giao dịch" } },
    ],
  },


  // Teacher
  {
    path: "/teacher",
    component: TeacherLayout,
    meta: { role: "teacher" },
    children: [
      { path: "", redirect: "/teacher/dashboard" },
      { path: "dashboard", component: () => import("@/pages/teacher/dashboard/dashboard.vue") },
      { path: "courses", component: () => import("@/pages/teacher/courses/Courses.vue") },
      { path: "classes", component: () => import("@/pages/teacher/classes/Classes.vue") },
      { path: "exams", component: () => import("@/pages/teacher/exams/Exams.vue") },
      { path: "students", component: () => import("@/pages/teacher/students/StudentProgress.vue") },
      { path: "reports", component: () => import("@/pages/teacher/exams/ExamReports.vue") },
    ],
  },

  // Student (không sidebar, menu trên navbar)
  {
    path: "/student",
    component: StudentLayout,
    meta: { role: "student" },
    children: [
      { path: "", redirect: "/student/dashboard" },
      { path: "dashboard", component: () => import("@/pages/student/dashboard/dashboard.vue") },
      { path: "courses", component: () => import("@/pages/student/courses/MyCourses.vue") },
      { path: "exams", component: () => import("@/pages/student/exams/PracticeExams.vue") },
      { path: "payments", component: () => import("@/pages/student/payments/Payments.vue") },
      { path: "account/profile", component: () => import("@/pages/student/account/Profile.vue") },
    ],
  },

  // Common
  { path: "/notifications", component: () => import("@/pages/common/Notifications.vue") },
  { path: "/:pathMatch(.*)*", component: () => import("@/pages/common/NotFound.vue") },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Guard đơn giản theo role + tự hydrate từ localStorage
router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (!auth.user) auth.hydrateFromStorage()

  // Đã đăng nhập mà vào /auth → đẩy về khu đúng role
  if (to.path.startsWith("/auth") && auth.user) {
    auth.redirectByRole(auth.user.role)
    return
  }

  // Chưa đăng nhập mà vào khu riêng → đẩy về login
  const needRole = to.meta.role as "admin" | "teacher" | "student" | undefined
  if (needRole && !auth.user) {
    next("/auth/login")
    return
  }

  // Sai role → đẩy về khu đúng
  if (needRole && auth.user && auth.user.role !== needRole) {
    auth.redirectByRole(auth.user.role)
    return
  }

  // Nếu đang ở "/" mà đã login → về dashboard theo role
  if (to.path === "/" && auth.user) {
    auth.redirectByRole(auth.user.role)
    return
  }

  next()
})

export default router
