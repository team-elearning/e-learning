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
      // courses
      { path: "courses", component: () => import("@/pages/teacher/courses/Courses.vue") },
      { path: "courses/new",           name: "teacher-course-new",        component: () => import("@/pages/teacher/courses/CourseCreate.vue") },
      { path: "courses/:id",           name: "teacher-course-detail",     component: () => import("@/pages/teacher/courses/CourseDetail.vue") },
      { path: "courses/:id/edit",      name: "teacher-course-edit",       component: () => import("@/pages/teacher/courses/CourseEdit.vue") },
      { path: "courses/content-library", name: "teacher-content-library", component: () => import("@/pages/teacher/courses/ContentLibrary.vue") },
      // class
      { path: "classes", component: () => import("@/pages/teacher/classes/Classes.vue") },
      { path: "classes/:id",             name: "teacher-class-detail",  component: () => import("@/pages/teacher/classes/ClassDetail.vue") },
      { path: "classes/:id/assignments", name: "teacher-class-assign",  component: () => import("@/pages/teacher/classes/Assignments.vue") },
      { path: "classes/:id/live",        name: "teacher-class-live",    component: () => import("@/pages/teacher/classes/OnlineClass.vue") },
      // exams
      { path: "exams", component: () => import("@/pages/teacher/exams/Exams.vue") },
      { path: "exams/:id",              name: "teacher-exam-detail",  component: () => import("@/pages/teacher/exams/ExamDetail.vue") },
      { path: "exams/:id/grading",      name: "teacher-exam-grading", component: () => import("@/pages/teacher/exams/ExamGrading.vue") },
      { path: "reports",                name: "teacher-reports",      component: () => import("@/pages/teacher/exams/ExamReports.vue") },

      //students feedback
      { path: "students", component: () => import("@/pages/teacher/students/StudentProgress.vue") },
      { path: "students/feedback", name: "teacher-students-feedback", component: () => import("@/pages/teacher/students/Feedback.vue") },
    ],
  },

  // Student (không sidebar, menu trên navbar)
  {
    path: "/student",
    component: StudentLayout,
    meta: { role: "student" },
    children: [
      { path: "", redirect: "/student/dashboard" },
      { path: "dashboard", name: "student-dashboard", component: () => import("@/pages/student/dashboard/dashboard.vue") }, // [NOTE] đặt name để các nút/redirect có thể gọi bằng name

      // MyCourses
      { path: "courses", name: "MyCourses", component: () => import("@/pages/student/courses/MyCourses.vue") }, // [NOTE] thêm name để các link trong dashboard dùng { name: 'MyCourses' }

      // Catalog / Detail / Player / Learning Path
      { path: "catalog", name: "student-catalog", component: () => import("@/pages/student/courses/Catalog.vue") }, // [NOTE] route danh mục
      { path: "courses/:id", name: "student-course-detail", component: () => import("@/pages/student/courses/CourseDetail.vue"), props: true }, // [NOTE] chi tiết khóa học
      { path: "courses/:id/player/:lessonId?", name: "student-course-player", component: () => import("@/pages/student/courses/CoursePlayer.vue"), props: true }, // [NOTE] player (có lessonId tùy chọn)
      { path: "learning-path", name: "student-learning-path", component: () => import("@/pages/student/courses/LearningPath.vue") }, // [NOTE] lộ trình học

      // Exams
      { path: "exams", name: "student-exams", component: () => import("@/pages/student/exams/PracticeExams.vue") }, // [NOTE] LIST đề thi – những nút "Làm bài" trỏ sang student-exam-detail
      { path: "exams/:id", name: "student-exam-detail", component: () => import("@/pages/student/exams/ExamDetail.vue"), props: true }, // [NOTE] LÀM BÀI – dùng name khi push để tránh "No match for route"
      { path: "exams/:id/result", name: "student-exam-result", component: () => import("@/pages/student/exams/ExamResult.vue"), props: true }, // [NOTE] KẾT QUẢ – chuyển hướng sau khi nộp bài
      { path: "exams/certificates", name: "student-certificates", component: () => import("@/pages/student/exams/Certificates.vue") }, // [NOTE] chứng chỉ (nếu dùng)
      { path: "exams/ranking", name: "student-exams-ranking", component: () => import("@/pages/student/exams/Ranking.vue") }, // [NOTE] bảng xếp hạng (nếu dùng)

      // Payments & Account
      { path: "payments", name: "student-payments", component: () => import("@/pages/student/payments/Payments.vue") },
      { path: "account/profile", name: "student-profile", component: () => import("@/pages/student/account/Profile.vue") },
      { path: "account/change-password", name: "student-change-password", component: () => import("@/pages/student/account/ChangePassword.vue") }, // [THÊM]
      { path: "account/parent",  name: "student-parent", component: () => import("@/pages/student/account/ParentView.vue") }, 
      { path: "payments/cart",         name: "student-payments-cart", component: () => import("@/pages/student/payments/Cart.vue") },
      { path: "payments/checkout",     name: "student-payments-checkout", component: () => import("@/pages/student/payments/Checkout.vue") },
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
