<script setup lang="ts">
import { useRouter } from 'vue-router'
const router = useRouter()
</script>

<template>
  <div class="min-h-screen flex flex-col font-sans">
    <!-- Navbar -->
    <header class="sticky top-0 z-50 glass border-b border-gray-100">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        <div class="flex items-center gap-2">
          <div
            class="h-8 w-8 rounded-lg bg-gradient-to-br from-[rgb(var(--primary))] to-[rgb(var(--secondary))] flex items-center justify-center text-white font-bold text-lg"
          >
            E
          </div>
          <span class="font-bold text-xl tracking-tight text-[rgb(var(--text))]">EduRiot</span>
        </div>
        <div class="flex items-center gap-4">
          <button
            @click="router.push('/login')"
            class="text-sm font-semibold text-[rgb(var(--text-light))] hover:text-[rgb(var(--primary))] transition"
          >
            Đăng nhập
          </button>
          <button
            @click="router.push('/register')"
            class="px-4 py-2 rounded-full bg-[rgb(var(--text))] text-white text-sm font-semibold hover:bg-slate-800 transition shadow-lg"
          >
            Đăng ký miễn phí
          </button>
        </div>
      </div>
    </header>

    <!-- Hero -->
    <main class="flex-grow">
      <section class="relative pt-20 pb-32 overflow-hidden">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 relative z-10 text-center">
          <div
            class="inline-flex items-center justify-center p-1 px-3 mb-6 rounded-full bg-blue-50 border border-blue-100"
          >
            <span class="flex h-2 w-2 rounded-full bg-[rgb(var(--primary))] mr-2"></span>
            <span class="text-xs font-semibold uppercase tracking-wide text-[rgb(var(--primary))]"
              >Nền tảng học tập thế hệ mới</span
            >
          </div>

          <h1
            class="text-5xl md:text-7xl font-extrabold tracking-tight mb-6 leading-tight text-[rgb(var(--text))]"
          >
            Học tập không giới hạn <br />
            <span class="text-gradient">Kiến tạo tương lai</span>
          </h1>

          <p class="mt-4 max-w-2xl mx-auto text-xl text-[rgb(var(--text-light))] mb-10">
            Nền tảng quản lý học tập toàn diện dành cho Giáo viên và Học sinh. Trải nghiệm giao diện
            hiện đại, tối ưu hóa cho sự tập trung và hiệu quả.
          </p>

          <div class="flex flex-col sm:flex-row items-center justify-center gap-4">
            <button
              @click="router.push('/login')"
              class="h-12 px-8 rounded-full bg-[rgb(var(--primary))] text-white font-semibold shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition flex items-center gap-2"
            >
              Bắt đầu ngay
              <span class="text-lg">→</span>
            </button>
            <button
              class="h-12 px-8 rounded-full bg-white border border-gray-200 text-[rgb(var(--text))] font-semibold hover:bg-gray-50 transition shadow-sm"
            >
              Tìm hiểu thêm
            </button>
          </div>
        </div>

        <!-- Decoration -->
        <div
          class="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] bg-gradient-to-r from-blue-200/30 to-purple-200/30 rounded-full blur-3xl -z-10"
        ></div>
      </section>

      <!-- Feature Grid -->
      <section class="py-24 bg-white">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="grid md:grid-cols-3 gap-8">
            <!-- Feature 1 -->
            <div
              class="p-8 rounded-2xl bg-[rgb(var(--bg))] border border-[rgb(var(--border))] hover:shadow-lg transition duration-300"
            >
              <div
                class="h-12 w-12 rounded-xl bg-blue-100 flex items-center justify-center mb-6 text-2xl"
              >
                📚
              </div>
              <h3 class="text-xl font-bold mb-3 text-[rgb(var(--text))]">Quản lý khóa học</h3>
              <p class="text-[rgb(var(--text-light))]">
                Tổ chức bài giảng, tài liệu và lộ trình học tập một cách khoa học và dễ dàng truy
                cập.
              </p>
            </div>
            <!-- Feature 2 -->
            <div
              class="p-8 rounded-2xl bg-[rgb(var(--bg))] border border-[rgb(var(--border))] hover:shadow-lg transition duration-300"
            >
              <div
                class="h-12 w-12 rounded-xl bg-green-100 flex items-center justify-center mb-6 text-2xl"
              >
                📝
              </div>
              <h3 class="text-xl font-bold mb-3 text-[rgb(var(--text))]">
                Bài kiểm tra & Đánh giá
              </h3>
              <p class="text-[rgb(var(--text-light))]">
                Hệ thống thi trắc nghiệm online, tự động chấm điểm và báo cáo kết quả chi tiết.
              </p>
            </div>
            <!-- Feature 3 -->
            <div
              class="p-8 rounded-2xl bg-[rgb(var(--bg))] border border-[rgb(var(--border))] hover:shadow-lg transition duration-300"
            >
              <div
                class="h-12 w-12 rounded-xl bg-orange-100 flex items-center justify-center mb-6 text-2xl"
              >
                📊
              </div>
              <h3 class="text-xl font-bold mb-3 text-[rgb(var(--text))]">Báo cáo & Thống kê</h3>
              <p class="text-[rgb(var(--text-light))]">
                Theo dõi tiến độ học tập, chuyên cần và hiệu suất qua các biểu đồ trực quan.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Stats -->
      <!-- Stats -->
      <section class="py-16 bg-[rgb(var(--bg))]">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="grid sm:grid-cols-2 lg:grid-cols-4 gap-6">
            <div class="rounded-2xl border border-[rgb(var(--border))] bg-white p-6 text-center">
              <div class="text-3xl font-extrabold text-[rgb(var(--text))]">1.2M+</div>
              <div class="text-sm text-[rgb(var(--text-light))]">lượt học viên</div>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] bg-white p-6 text-center">
              <div class="text-3xl font-extrabold text-[rgb(var(--text))]">8,500+</div>
              <div class="text-sm text-[rgb(var(--text-light))]">khóa học đang mở</div>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] bg-white p-6 text-center">
              <div class="text-3xl font-extrabold text-[rgb(var(--text))]">96%</div>
              <div class="text-sm text-[rgb(var(--text-light))]">tỉ lệ hoàn thành</div>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] bg-white p-6 text-center">
              <div class="text-3xl font-extrabold text-[rgb(var(--text))]">140+</div>
              <div class="text-sm text-[rgb(var(--text-light))]">đối tác doanh nghiệp</div>
            </div>
          </div>
        </div>
      </section>

      <!-- Course Library -->
      <section class="py-24 bg-white">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="flex flex-col md:flex-row md:items-end md:justify-between gap-6 mb-10">
            <div>
              <h2 class="text-3xl md:text-4xl font-extrabold text-[rgb(var(--text))]">
                Thư viện khóa học chuẩn LMS
              </h2>
              <p class="mt-3 text-[rgb(var(--text-light))] max-w-2xl">
                Danh mục đa lĩnh vực, cập nhật theo năng lực, có đề cương, tài liệu, bài tập và bài
                kiểm tra kèm rubric.
              </p>
            </div>
            <button
              class="h-11 px-6 rounded-full bg-[rgb(var(--text))] text-white text-sm font-semibold hover:bg-slate-800 transition shadow"
            >
              Xem toàn bộ khóa học
            </button>
          </div>

          <div class="grid md:grid-cols-3 gap-8">
            <div class="rounded-2xl border border-[rgb(var(--border))] bg-[rgb(var(--bg))] p-6">
              <div class="text-xs uppercase tracking-widest text-[rgb(var(--text-light))] mb-2">
                Data & AI
              </div>
              <div class="text-xl font-bold text-[rgb(var(--text))]">Phân tích dữ liệu cơ bản</div>
              <div class="mt-3 flex items-center gap-2 text-sm text-[rgb(var(--text-light))]">
                <span>24 bài</span><span>·</span><span>6 tuần</span><span>·</span
                ><span>2 dự án</span>
              </div>
              <div class="mt-5 flex items-center justify-between">
                <span class="text-sm font-semibold text-[rgb(var(--primary))]"
                  >Cấp độ: Beginner</span
                >
                <span class="text-xs text-[rgb(var(--text-light))]">4.8/5 (2.1k)</span>
              </div>
            </div>

            <div class="rounded-2xl border border-[rgb(var(--border))] bg-[rgb(var(--bg))] p-6">
              <div class="text-xs uppercase tracking-widest text-[rgb(var(--text-light))] mb-2">
                Business
              </div>
              <div class="text-xl font-bold text-[rgb(var(--text))]">Quản trị dự án Agile</div>
              <div class="mt-3 flex items-center gap-2 text-sm text-[rgb(var(--text-light))]">
                <span>18 bài</span><span>·</span><span>5 tuần</span><span>·</span
                ><span>1 thi thử</span>
              </div>
              <div class="mt-5 flex items-center justify-between">
                <span class="text-sm font-semibold text-[rgb(var(--primary))]"
                  >Cấp độ: Intermediate</span
                >
                <span class="text-xs text-[rgb(var(--text-light))]">4.7/5 (980)</span>
              </div>
            </div>

            <div class="rounded-2xl border border-[rgb(var(--border))] bg-[rgb(var(--bg))] p-6">
              <div class="text-xs uppercase tracking-widest text-[rgb(var(--text-light))] mb-2">
                Design
              </div>
              <div class="text-xl font-bold text-[rgb(var(--text))]">UX Research và Product</div>
              <div class="mt-3 flex items-center gap-2 text-sm text-[rgb(var(--text-light))]">
                <span>30 bài</span><span>·</span><span>8 tuần</span><span>·</span
                ><span>3 workshop</span>
              </div>
              <div class="mt-5 flex items-center justify-between">
                <span class="text-sm font-semibold text-[rgb(var(--primary))]"
                  >Cấp độ: Advanced</span
                >
                <span class="text-xs text-[rgb(var(--text-light))]">4.9/5 (1.4k)</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- Learning Path -->
      <section class="py-24 bg-[rgb(var(--bg))]">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <h2 class="text-3xl md:text-4xl font-extrabold text-[rgb(var(--text))]">
                Lộ trình học tập cá nhân hóa
              </h2>
              <p class="mt-4 text-[rgb(var(--text-light))]">
                Tự động đề xuất khóa học theo mục tiêu nghề nghiệp, theo dõi tiến độ và cảnh báo
                nguy cơ bỏ cuộc.
              </p>
              <div class="mt-8 grid sm:grid-cols-2 gap-6">
                <div class="rounded-xl border border-[rgb(var(--border))] bg-white p-5">
                  <div class="text-sm font-semibold text-[rgb(var(--text))]">Chuẩn đầu ra</div>
                  <div class="mt-2 text-sm text-[rgb(var(--text-light))]">
                    Kỹ năng, KPI, điểm thử thách
                  </div>
                </div>
                <div class="rounded-xl border border-[rgb(var(--border))] bg-white p-5">
                  <div class="text-sm font-semibold text-[rgb(var(--text))]">Đánh giá liên tục</div>
                  <div class="mt-2 text-sm text-[rgb(var(--text-light))]">
                    Quiz, assignment, project
                  </div>
                </div>
                <div class="rounded-xl border border-[rgb(var(--border))] bg-white p-5">
                  <div class="text-sm font-semibold text-[rgb(var(--text))]">Mentor & feedback</div>
                  <div class="mt-2 text-sm text-[rgb(var(--text-light))]">
                    Lịch tương tác và rubric
                  </div>
                </div>
                <div class="rounded-xl border border-[rgb(var(--border))] bg-white p-5">
                  <div class="text-sm font-semibold text-[rgb(var(--text))]">Báo cáo trực quan</div>
                  <div class="mt-2 text-sm text-[rgb(var(--text-light))]">
                    Dashboard theo nhóm và cá nhân
                  </div>
                </div>
              </div>
            </div>

            <div class="rounded-3xl border border-[rgb(var(--border))] bg-white p-8">
              <div class="text-sm font-semibold text-[rgb(var(--text))] mb-6">
                Mẫu lộ trình 12 tuần
              </div>
              <ol class="space-y-5 text-sm text-[rgb(var(--text-light))]">
                <li class="flex items-start gap-3">
                  <span class="mt-1 h-2 w-2 rounded-full bg-[rgb(var(--primary))]"></span>
                  <div>
                    <div class="font-semibold text-[rgb(var(--text))]">Tuần 1–2</div>
                    Onboarding, bài test đầu vào, chuẩn mục tiêu
                  </div>
                </li>
                <li class="flex items-start gap-3">
                  <span class="mt-1 h-2 w-2 rounded-full bg-[rgb(var(--primary))]"></span>
                  <div>
                    <div class="font-semibold text-[rgb(var(--text))]">Tuần 3–6</div>
                    Bài học, practice, quiz theo chủ đề
                  </div>
                </li>
                <li class="flex items-start gap-3">
                  <span class="mt-1 h-2 w-2 rounded-full bg-[rgb(var(--primary))]"></span>
                  <div>
                    <div class="font-semibold text-[rgb(var(--text))]">Tuần 7–10</div>
                    Dự án thực hành, review với mentor
                  </div>
                </li>
                <li class="flex items-start gap-3">
                  <span class="mt-1 h-2 w-2 rounded-full bg-[rgb(var(--primary))]"></span>
                  <div>
                    <div class="font-semibold text-[rgb(var(--text))]">Tuần 11–12</div>
                    Báo cáo tổng kết, cấp chứng chỉ
                  </div>
                </li>
              </ol>
            </div>
          </div>
        </div>
      </section>

      <!-- Roles -->
      <section class="py-24 bg-white">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="grid md:grid-cols-3 gap-8">
            <div class="rounded-2xl border border-[rgb(var(--border))] p-6">
              <div class="text-sm uppercase tracking-widest text-[rgb(var(--text-light))] mb-3">
                Giảng viên
              </div>
              <div class="text-xl font-bold text-[rgb(var(--text))]">Tạo khóa học nhanh</div>
              <p class="mt-3 text-[rgb(var(--text-light))]">
                Kế hoạch giảng dạy, tạo bài tập, chấm điểm theo rubric và quản lý chat lớp.
              </p>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] p-6">
              <div class="text-sm uppercase tracking-widest text-[rgb(var(--text-light))] mb-3">
                Học viên
              </div>
              <div class="text-xl font-bold text-[rgb(var(--text))]">Học tập mọi lúc</div>
              <p class="mt-3 text-[rgb(var(--text-light))]">
                Bài giảng video, tài liệu, checklist, nhắc nhở deadline và bảng điểm tổng hợp.
              </p>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] p-6">
              <div class="text-sm uppercase tracking-widest text-[rgb(var(--text-light))] mb-3">
                Quản trị
              </div>
              <div class="text-xl font-bold text-[rgb(var(--text))]">Theo dõi toàn bộ</div>
              <p class="mt-3 text-[rgb(var(--text-light))]">
                Phân quyền, báo cáo, tích hợp SSO và kiểm soát chất lượng.
              </p>
            </div>
          </div>
        </div>
      </section>

      <!-- Testimonials -->
      <section class="py-24 bg-[rgb(var(--bg))]">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div class="text-center mb-12">
            <h2 class="text-3xl md:text-4xl font-extrabold text-[rgb(var(--text))]">
              Phản hồi từ doanh nghiệp và trường học
            </h2>
            <p class="mt-3 text-[rgb(var(--text-light))]">
              Hiệu quả rõ ràng với báo cáo đầy đủ và hệ thống đánh giá minh bạch.
            </p>
          </div>
          <div class="grid md:grid-cols-3 gap-8">
            <div class="rounded-2xl border border-[rgb(var(--border))] bg-white p-6">
              <p class="text-[rgb(var(--text-light))]">
                “Tỉ lệ hoàn thành khóa học tăng 28% sau 2 tháng. Dashboard rất dễ theo dõi.”
              </p>
              <div class="mt-4 text-sm font-semibold text-[rgb(var(--text))]">
                Lê Minh – HR Lead
              </div>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] bg-white p-6">
              <p class="text-[rgb(var(--text-light))]">
                “Tạo đề thi, chấm điểm và cấp chứng chỉ chỉ trong vài phút.”
              </p>
              <div class="mt-4 text-sm font-semibold text-[rgb(var(--text))]">
                Nguyễn Hà – Teacher
              </div>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] bg-white p-6">
              <p class="text-[rgb(var(--text-light))]">
                “Giao diện dễ dùng, học viên tương tác nhiều hơn và kết quả tốt hơn.”
              </p>
              <div class="mt-4 text-sm font-semibold text-[rgb(var(--text))]">
                Phạm Long – Training Manager
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- FAQ -->
      <section class="py-24 bg-white">
        <div class="mx-auto max-w-5xl px-4 sm:px-6 lg:px-8">
          <div class="text-center mb-10">
            <h2 class="text-3xl md:text-4xl font-extrabold text-[rgb(var(--text))]">FAQ</h2>
            <p class="mt-3 text-[rgb(var(--text-light))]">Giải đáp nhanh về triển khai LMS</p>
          </div>
          <div class="space-y-5">
            <div class="rounded-2xl border border-[rgb(var(--border))] p-6">
              <div class="font-semibold text-[rgb(var(--text))]">Có thể tích hợp SSO không?</div>
              <div class="mt-2 text-[rgb(var(--text-light))]">
                Hỗ trợ SSO, SCORM, LTI và API đồng bộ dữ liệu.
              </div>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] p-6">
              <div class="font-semibold text-[rgb(var(--text))]">Hệ thống có theo dõi KPI?</div>
              <div class="mt-2 text-[rgb(var(--text-light))]">
                Dashboard cập nhật theo thời gian thực, báo cáo theo nhóm và cá nhân.
              </div>
            </div>
            <div class="rounded-2xl border border-[rgb(var(--border))] p-6">
              <div class="font-semibold text-[rgb(var(--text))]">Có thể tự tạo nội dung?</div>
              <div class="mt-2 text-[rgb(var(--text-light))]">
                Giảng viên tự tạo bài giảng, bài tập, đề thi và rubric đánh giá.
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- CTA -->
      <section class="py-20 bg-[rgb(var(--text))]">
        <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 text-center text-white">
          <h2 class="text-3xl md:text-4xl font-extrabold">Sẵn sàng nâng cấp LMS?</h2>
          <p class="mt-4 text-white/80 max-w-2xl mx-auto">
            Khởi tạo lớp học, phân quyền và bắt đầu giảng dạy chỉ trong vài phút.
          </p>
          <div class="mt-8 flex flex-col sm:flex-row justify-center gap-4">
            <button
              @click="router.push('/register')"
              class="h-12 px-8 rounded-full bg-white text-[rgb(var(--text))] font-semibold hover:bg-gray-100 transition"
            >
              Đăng ký dùng thử
            </button>
            <button
              class="h-12 px-8 rounded-full border border-white/30 text-white font-semibold hover:bg-white/10 transition"
            >
              Đặt lịch demo
            </button>
          </div>
        </div>
      </section>
    </main>
    <footer class="border-t border-[rgb(var(--border))] bg-white">
      <div class="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-12">
        <div class="grid gap-10 md:grid-cols-4">
          <div>
            <div class="flex items-center gap-2">
              <div
                class="h-9 w-9 rounded-lg bg-gradient-to-br from-[rgb(var(--primary))] to-[rgb(var(--secondary))] flex items-center justify-center text-white font-bold text-lg"
              >
                E
              </div>
              <div class="text-lg font-bold text-[rgb(var(--text))]">EduRiot</div>
            </div>
            <p class="mt-3 text-sm text-[rgb(var(--text-light))]">
              Nền tảng LMS hiện đại cho trường học và doanh nghiệp. Tối ưu hóa quản lý, đào tạo và
              đánh giá theo chuẩn đầu ra.
            </p>
            <div class="mt-4 text-sm text-[rgb(var(--text-light))]">
              Hotline: 1900 123 456
              <br />
              Email: support@eduriot.vn
            </div>
          </div>

          <div>
            <div class="text-sm font-semibold text-[rgb(var(--text))]">Sản phẩm</div>
            <ul class="mt-4 space-y-2 text-sm text-[rgb(var(--text-light))]">
              <li>Quản lý khóa học</li>
              <li>Lớp học trực tuyến</li>
              <li>Thi &amp; đánh giá</li>
              <li>Báo cáo &amp; phân tích</li>
              <li>Tích hợp SCORM/LTI</li>
            </ul>
          </div>

          <div>
            <div class="text-sm font-semibold text-[rgb(var(--text))]">Tài nguyên</div>
            <ul class="mt-4 space-y-2 text-sm text-[rgb(var(--text-light))]">
              <li>Hướng dẫn sử dụng</li>
              <li>Câu hỏi thường gặp</li>
              <li>Học liệu mẫu</li>
              <li>Blog &amp; sự kiện</li>
              <li>Trung tâm hỗ trợ</li>
            </ul>
          </div>

          <div>
            <div class="text-sm font-semibold text-[rgb(var(--text))]">Doanh nghiệp</div>
            <ul class="mt-4 space-y-2 text-sm text-[rgb(var(--text-light))]">
              <li>Giới thiệu</li>
              <li>Tuyển dụng</li>
              <li>Đối tác</li>
              <li>Bảo mật</li>
              <li>Điều khoản</li>
            </ul>
          </div>
        </div>

        <div
          class="mt-10 flex flex-col gap-4 border-t border-[rgb(var(--border))] pt-6 text-sm text-[rgb(var(--text-light))] md:flex-row md:items-center md:justify-between"
        >
          <div>© 2024 EduRiot LMS. All rights reserved.</div>
          <div class="flex flex-wrap items-center gap-3">
            <span class="rounded-full bg-[rgb(var(--bg))] px-3 py-1">ISO 27001</span>
            <span class="rounded-full bg-[rgb(var(--bg))] px-3 py-1">GDPR Ready</span>
            <span class="rounded-full bg-[rgb(var(--bg))] px-3 py-1">99.9% Uptime</span>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>
