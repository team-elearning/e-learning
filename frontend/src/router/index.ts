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
  // Landing
  { path: "/", component: () => import("@/pages/common/Landing.vue"), meta: { title: "Trang chủ" } },

  // Auth
  {
    path: "/auth",
    component: AuthLayout,
    children: [
      { path: "", redirect: "/auth/login" },
      { path: "login", component: () => import("@/pages/auth/Login.vue"), meta: { title: "Đăng nhập" } },
      { path: "register", component: () => import("@/pages/auth/Register.vue"), meta: { title: "Đăng ký" } },
      { path: "forgot-password", component: () => import("@/pages/auth/ForgotPassword.vue"), meta: { title: "Quên mật khẩu" } },
      { path: "reset-password", component: () => import("@/pages/auth/ResetPassword.vue"), meta: { title: "Đặt lại mật khẩu" } },
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
      { path: "users/:id", component: () => import("@/pages/admin/users/UserDetail.vue"), meta: { title: (to:any) => `Người dùng #${to.params.id}` } },

      // Courses
      { path: "courses", component: () => import("@/pages/admin/courses/Courses.vue"), meta: { title: "Quản lý khóa học" } },
      { path: "courses/approval", component: () => import("@/pages/admin/courses/CourseApproval.vue"), meta: { title: "Duyệt khóa học" } },
      { path: "courses/:id", component: () => import("@/pages/admin/courses/CourseDetail.vue"), meta: { title: (to:any) => `Chi tiết khóa học #${to.params.id}` } },

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
      { path: "transactions/:id", component: () => import("@/pages/admin/transactions/TransactionDetail.vue"), meta: { title: (to:any) => `Chi tiết giao dịch #${to.params.id}` } },
    ],
  },

  // Teacher
  {
    path: "/teacher",
    component: TeacherLayout,
    meta: { role: "teacher" },
    children: [
      { path: "", redirect: "/teacher/dashboard" },
      { path: "dashboard", component: () => import("@/pages/teacher/dashboard/dashboard.vue"), meta: { title: "Trang chủ giảng viên" } },

      // courses
      { path: "courses", component: () => import("@/pages/teacher/courses/Courses.vue"), meta: { title: "Khoá học của tôi" } },
      { path: "courses/new",           name: "teacher-course-new",        component: () => import("@/pages/teacher/courses/CourseCreate.vue"), meta: { title: "Tạo khoá học" } },
      { path: "courses/:id",           name: "teacher-course-detail",     component: () => import("@/pages/teacher/courses/CourseDetail.vue"), meta: { title: (to:any) => `Khoá học #${to.params.id}` } },
      { path: "courses/:id/edit",      name: "teacher-course-edit",       component: () => import("@/pages/teacher/courses/CourseEdit.vue"), meta: { title: (to:any) => `Sửa khoá học #${to.params.id}` } },
      { path: "courses/content-library", name: "teacher-content-library", component: () => import("@/pages/teacher/courses/ContentLibrary.vue"), meta: { title: "Thư viện nội dung" } },

      // class
      { path: "classes", component: () => import("@/pages/teacher/classes/Classes.vue"), meta: { title: "Lớp học" } },
      { path: "classes/:id",             name: "teacher-class-detail",  component: () => import("@/pages/teacher/classes/ClassDetail.vue"), meta: { title: (to:any) => `Lớp #${to.params.id}` } },
      { path: "classes/:id/assignments", name: "teacher-class-assign",  component: () => import("@/pages/teacher/classes/Assignments.vue"), meta: { title: "Giao bài tập" } },
      { path: "classes/:id/live",        name: "teacher-class-live",    component: () => import("@/pages/teacher/classes/OnlineClass.vue"), meta: { title: "Lớp trực tuyến" } },

      // exams
      { path: "exams", component: () => import("@/pages/teacher/exams/Exams.vue"), meta: { title: "Bài kiểm tra" } },
      { path: "exams/:id",              name: "teacher-exam-detail",  component: () => import("@/pages/teacher/exams/ExamDetail.vue"), meta: { title: (to:any) => `Đề #${to.params.id}` } },
      { path: "exams/:id/grading",      name: "teacher-exam-grading", component: () => import("@/pages/teacher/exams/ExamGrading.vue"), meta: { title: "Chấm bài" } },
      { path: "reports",                name: "teacher-reports",      component: () => import("@/pages/teacher/exams/ExamReports.vue"), meta: { title: "Báo cáo chấm thi" } },

      //students feedback
      { path: "students", component: () => import("@/pages/teacher/students/StudentProgress.vue"), meta: { title: "Tiến độ học viên" } },
      { path: "students/feedback", name: "teacher-students-feedback", component: () => import("@/pages/teacher/students/Feedback.vue"), meta: { title: "Phản hồi học viên" } },
    ],
  },

  // Student
  {
    path: "/student",
    component: StudentLayout,
    meta: { role: "student" },
    children: [
      { path: "", redirect: "/student/dashboard" },
      { path: "dashboard", name: "student-dashboard", component: () => import("@/pages/student/dashboard/dashboard.vue"), meta: { title: "Trang chủ" } },

      // MyCourses
      { path: "courses", name: "MyCourses", component: () => import("@/pages/student/courses/MyCourses.vue"), meta: { title: "Khoá học của tôi" } },

      // Catalog / Detail / Player / Learning Path
      { path: "catalog", name: "student-catalog", component: () => import("@/pages/student/courses/Catalog.vue"), meta: { title: "Danh mục khoá học" } },
      { path: "courses/:id", name: "student-course-detail", component: () => import("@/pages/student/courses/CourseDetail.vue"), props: true, meta: { title: (to:any) => `Khoá học #${to.params.id}` } },
      { path: "courses/:id/player/:lessonId?", name: "student-course-player", component: () => import("@/pages/student/courses/CoursePlayer.vue"), props: true, meta: { title: (to:any) => `Bài học #${to.params.lessonId ?? ''}` } },
      { path: "learning-path", name: "student-learning-path", component: () => import("@/pages/student/courses/LearningPath.vue"), meta: { title: "Lộ trình học" } },

      // Exams
      { path: "exams", name: "student-exams", component: () => import("@/pages/student/exams/PracticeExams.vue"), meta: { title: "Luyện đề" } },
      { path: "exams/:id", name: "student-exam-detail", component: () => import("@/pages/student/exams/ExamDetail.vue"), props: true, meta: { title: (to:any) => `Đề #${to.params.id}` } },
      { path: "exams/:id/result", name: "student-exam-result", component: () => import("@/pages/student/exams/ExamResult.vue"), props: true, meta: { title: "Kết quả bài thi" } },
      { path: "exams/certificates", name: "student-certificates", component: () => import("@/pages/student/exams/Certificates.vue"), meta: { title: "Chứng chỉ" } },
      { path: "exams/ranking", name: "student-exams-ranking", component: () => import("@/pages/student/exams/Ranking.vue"), meta: { title: "Bảng xếp hạng" } },

      // Payments & Account
      { path: "payments", name: "student-payments", component: () => import("@/pages/student/payments/Payments.vue"), meta: { title: "Thanh toán" } },
      { path: "account/profile", name: "student-profile", component: () => import("@/pages/student/account/Profile.vue"), meta: { title: "Hồ sơ cá nhân" } },
      { path: "account/change-password", name: "student-change-password", component: () => import("@/pages/student/account/ChangePassword.vue"), meta: { title: "Đổi mật khẩu" } },
      { path: "account/parent",  name: "student-parent", component: () => import("@/pages/student/account/ParentView.vue"), meta: { title: "Thông tin phụ huynh" } },
      { path: "payments/cart",         name: "student-payments-cart", component: () => import("@/pages/student/payments/Cart.vue"), meta: { title: "Giỏ hàng" } },
      { path: "payments/checkout",     name: "student-payments-checkout", component: () => import("@/pages/student/payments/Checkout.vue"), meta: { title: "Thanh toán" } },
    ],
  },

  // Common
  { path: "/notifications", component: () => import("@/pages/common/Notifications.vue"), meta: { title: "Thông báo" } },
  { path: "/:pathMatch(.*)*", component: () => import("@/pages/common/NotFound.vue"), meta: { title: "Không tìm thấy trang" } },
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
router.afterEach((to) => {
  // tìm route con có meta.title gần nhất
  const r = [...to.matched].reverse().find(r => (r.meta as any)?.title !== undefined)
  if (!r) return
  const raw = (r.meta as any).title
  const title = typeof raw === 'function' ? raw(to) : raw
  if (title) document.title = String(title)
})
export default router
