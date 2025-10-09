<template>
  <div class="font-sans text-gray-800 bg-gradient-to-b from-pink-50 via-blue-50 to-green-50">
    <!-- Header -->
    <header
      class="flex justify-between items-center px-8 py-4 bg-white shadow-md sticky top-0 z-50"
      style="height: 80px"
    >
      <LogoEduriot :size="90" />
      <nav class="hidden md:flex space-x-6">
        <a href="#" class="hover:text-pink-500">Trang chủ</a>
        <a href="#about" class="hover:text-blue-500">Giới thiệu</a>
        <a href="#courses" class="hover:text-green-500">Khóa học</a>
        <a href="#reviews" class="hover:text-yellow-500">Cảm nhận</a>
        <a href="#contact" class="hover:text-purple-500">Liên hệ</a>
      </nav>
      <button class="bg-pink-500 text-white px-4 py-2 rounded-lg hover:bg-pink-600 transition">
        <router-link to="/auth/login">Đăng nhập</router-link>
      </button>
    </header>

    <!-- Hero Section -->
    <section class="text-center py-20">
      <h2 class="text-4xl md:text-5xl font-extrabold text-blue-700 mb-4 animate-fade-in">
        Học mà chơi – Chơi mà học mỗi ngày!
      </h2>
      <p class="text-lg text-gray-700 mb-8 max-w-2xl mx-auto">
        Cùng EDURIOT, bé sẽ được khám phá thế giới kiến thức qua trò chơi, video hoạt hình và bài
        tập tương tác đầy thú vị.
      </p>
      <button
        class="bg-gradient-to-r from-pink-400 to-yellow-400 text-white px-8 py-3 rounded-full font-semibold shadow hover:scale-105 transition"
      >
        <router-link to="/auth/login"> Bắt đầu học thử ngay </router-link>
      </button>
    </section>

    <!-- About Section -->
    <section id="about" class="py-16 px-6 md:px-20 text-center">
      <h3 class="text-3xl font-bold text-blue-700 mb-10">Tại sao chọn EDURIOT?</h3>
      <div class="grid md:grid-cols-3 gap-8">
        <div
          v-for="item in aboutItems"
          :key="item.title"
          class="bg-white p-6 rounded-2xl shadow hover:shadow-lg transition"
        >
          <div class="text-5xl mb-4" :class="item.color">{{ item.icon }}</div>
          <h4 class="text-xl font-semibold mb-2 text-blue-600">{{ item.title }}</h4>
          <p class="text-gray-700">{{ item.description }}</p>
        </div>
      </div>
    </section>

    <!-- Courses Section -->
    <section id="courses" class="py-16 px-6 md:px-20 bg-white/80">
      <h3 class="text-3xl font-bold text-center text-blue-700 mb-10">Các môn học tiêu biểu</h3>
      <div class="grid md:grid-cols-3 gap-8">
        <div
          v-for="course in courses"
          :key="course.title"
          class="rounded-2xl p-6 shadow hover:scale-105 transition"
          :class="course.bg"
        >
          <h4 class="text-xl font-bold mb-2">{{ course.title }}</h4>
          <p class="text-gray-700 mb-4">{{ course.description }}</p>
          <button
            class="bg-white text-blue-600 px-4 py-2 rounded-lg shadow hover:bg-blue-100 transition"
          >
            <router-link to="/auth/login">khám phá</router-link>
          </button>
        </div>
      </div>
    </section>

    <section id="featured-lessons" class="py-16 px-6 md:px-20">
      <div class="flex justify-between items-center mb-10">
        <h3 class="text-3xl font-bold text-blue-700">Bài học nổi bật</h3>
        <a href="#" class="text-pink-500 font-semibold hover:underline">Xem tất cả</a>
      </div>
      <div class="grid md:grid-cols-3 gap-8">
        <div
          v-for="lesson in featuredLessons"
          :key="lesson.title"
          class="bg-white rounded-2xl shadow-lg overflow-hidden transform hover:-translate-y-2 transition-transform duration-300"
        >
          <div class="relative">
            <img :src="lesson.image" :alt="lesson.title" class="w-full h-48 object-cover" />
            <span
              v-if="lesson.tag"
              class="absolute top-3 right-3 px-3 py-1 text-sm font-semibold text-white rounded-full"
              :class="lesson.tag.bg"
            >
              {{ lesson.tag.text }}
            </span>
          </div>
          <div class="p-6">
            <div class="flex items-center text-sm text-gray-500 mb-3">
              <span class="px-2 py-1 bg-blue-100 text-blue-600 rounded-md font-semibold text-xs">{{
                lesson.grade
              }}</span>
              <span class="ml-4 flex items-center">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  class="h-4 w-4 mr-1"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                {{ lesson.duration }}
              </span>
            </div>
            <h4 class="text-xl font-bold text-gray-800 mb-2 truncate">{{ lesson.title }}</h4>
            <p class="text-gray-600 text-sm mb-4 h-10">{{ lesson.description }}</p>
            <div class="flex justify-between items-center">
              <div class="flex items-center">
                <span v-for="star in 5" :key="star" class="text-xl">
                  <template v-if="star <= lesson.rating">⭐</template>
                  <template v-else>
                    <span class="text-gray-300">⭐</span>
                  </template>
                </span>
              </div>
              <button
                class="bg-purple-100 text-purple-700 px-5 py-2 rounded-lg font-semibold hover:bg-purple-200 transition-colors"
              >
                Học ngay
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Benefits Section -->
    <section class="py-16 px-6 md:px-20">
      <h3 class="text-3xl font-bold text-center text-blue-700 mb-10">
        Lợi ích khi học tại EDURIOT
      </h3>
      <ul class="max-w-3xl mx-auto space-y-4 text-lg">
        <li v-for="b in benefits" :key="b" class="flex items-start space-x-3">
          <span class="text-green-500 text-2xl">✔️</span>
          <span>{{ b }}</span>
        </li>
      </ul>
    </section>

    <!-- Reviews Section -->
    <section id="reviews" class="py-16 px-6 md:px-20 bg-gradient-to-r from-yellow-50 to-pink-50">
      <h3 class="text-3xl font-bold text-center text-blue-700 mb-10">Cảm nhận của phụ huynh</h3>
      <div class="grid md:grid-cols-3 gap-6">
        <div
          v-for="review in reviews"
          :key="review.name"
          class="bg-white rounded-2xl shadow p-6 text-center hover:shadow-lg transition"
        >
          <p class="text-gray-700 italic mb-4">“{{ review.text }}”</p>
          <h4 class="font-semibold text-blue-600">— {{ review.name }}</h4>
          <p class="text-sm text-gray-500">{{ review.info }}</p>
        </div>
      </div>
    </section>

    <!-- Call to Action -->
    <section class="py-20 text-center bg-gradient-to-r from-green-100 to-blue-100">
      <h3 class="text-3xl font-bold text-blue-700 mb-6">
        Hãy để bé bắt đầu hành trình học vui ngay hôm nay!
      </h3>
      <button
        class="bg-gradient-to-r from-pink-400 to-yellow-400 text-white px-10 py-4 rounded-full text-lg font-semibold hover:scale-105 transition"
      >
        <router-link to="/auth/login"> Đăng ký học thử miễn phí </router-link>
      </button>
    </section>

    <!-- Footer -->
    <footer
      id="contact"
      class="bg-blue-700 text-white py-10 px-6 md:px-20"
      style="background: #1e3a8a"
    >
      <div
        class="grid md:grid-cols-3 gap-8"
        style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr))"
      >
        <div>
          <h4 class="font-bold text-xl mb-2">EDURIOT</h4>
          <p>Học tập vui nhộn, an toàn và hiệu quả cho học sinh tiểu học Việt Nam.</p>
        </div>
        <div>
          <h4 class="font-bold text-xl mb-2">Liên kết nhanh</h4>
          <ul>
            <li><a href="#about" class="hover:underline">Giới thiệu</a></li>
            <li><a href="#courses" class="hover:underline">Khóa học</a></li>
            <li><a href="#reviews" class="hover:underline">Cảm nhận</a></li>
          </ul>
        </div>
        <div>
          <h4 class="font-bold text-xl mb-2">Liên hệ</h4>
          <p>Email: contact@hocvuionline.vn</p>
          <p>Hotline: 0123 456 789</p>
        </div>
        <div>
          <h4 class="font-bold text-lg mb-4">Kết nối với chúng tôi</h4>
          <div class="flex space-x-4 mb-4">
            <!-- <a
              href="https://www.facebook.com/tu.chu.46680?locale=vi_VN"
              class="bg-gray-700 hover:bg-blue-600 w-10 h-10 rounded-full flex items-center justify-center"
            >
              <i data-feather="facebook" class="w-5 h-5"></i>
            </a>
            <a
              href="https://www.instagram.com/tustar.k72/"
              class="bg-gray-700 hover:bg-pink-600 w-10 h-10 rounded-full flex items-center justify-center"
            >
              <i data-feather="instagram" class="w-5 h-5"></i>
            </a>
            <a
              href="#"
              class="bg-gray-700 hover:bg-blue-400 w-10 h-10 rounded-full flex items-center justify-center"
            >
              <i data-feather="twitter" class="w-5 h-5"></i>
            </a>
            <a
              href="https://www.youtube.com/@T%C3%BANguy%E1%BB%85nanh-tuna2004/featured"
              class="bg-gray-700 hover:bg-red-500 w-10 h-10 rounded-full flex items-center justify-center"
            >
              <i data-feather="youtube" class="w-5 h-5"></i>
            </a>   -->
            <a
              href="https://www.facebook.com/tu.chu.46680?locale=vi_VN"
              class="bg-gray-700 hover:bg-blue-600 w-10 h-10 rounded-full flex items-center justify-center transition-colors"
              target="_blank"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"
                />
              </svg>
            </a>
            <a
              href="https://www.instagram.com/tustar.k72/"
              class="bg-gray-700 hover:bg-pink-600 w-10 h-10 rounded-full flex items-center justify-center transition-colors"
              target="_blank"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"
                />
              </svg>
            </a>
            <a
              href="#"
              class="bg-gray-700 hover:bg-blue-400 w-10 h-10 rounded-full flex items-center justify-center transition-colors"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M23.953 4.57a10 10 0 01-2.825.775 4.958 4.958 0 002.163-2.723c-.951.555-2.005.959-3.127 1.184a4.92 4.92 0 00-8.384 4.482C7.69 8.095 4.067 6.13 1.64 3.162a4.822 4.822 0 00-.666 2.475c0 1.71.87 3.213 2.188 4.096a4.904 4.904 0 01-2.228-.616v.06a4.923 4.923 0 003.946 4.827 4.996 4.996 0 01-2.212.085 4.936 4.936 0 004.604 3.417 9.867 9.867 0 01-6.102 2.105c-.39 0-.779-.023-1.17-.067a13.995 13.995 0 007.557 2.209c9.053 0 13.998-7.496 13.998-13.985 0-.21 0-.42-.015-.63A9.935 9.935 0 0024 4.59z"
                />
              </svg>
            </a>
            <a
              href="https://www.youtube.com/@T%C3%BANguy%E1%BB%85nanh-tuna2004/featured"
              class="bg-gray-700 hover:bg-red-500 w-10 h-10 rounded-full flex items-center justify-center transition-colors"
              target="_blank"
            >
              <svg
                xmlns="http://www.w3.org/2000/svg"
                class="w-5 h-5"
                fill="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"
                />
              </svg>
            </a>
          </div>
          <p class="text-gray-400">Email: anhtu105182@gmail.com</p>
          <p class="text-gray-400">Hotline: 0383137092</p>
        </div>
      </div>
      <div class="text-center mt-10 border-t border-blue-500 pt-4">
        © 2025 EDURIOT. All rights reserved.
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import LogoEduriot from '@/components/ui/LogoEduriot.vue'
// import { onMounted, nextTick } from 'vue'

// onMounted(() => {
//   nextTick(() => {
//     if (window.feather) window.feather.replace()
//   })
// })
const aboutItems = ref([
  {
    icon: '🎯',
    title: 'Chương trình cá nhân hóa',
    description: 'Lộ trình học được thiết kế phù hợp với năng lực và sở thích của từng bé.',
    color: 'text-pink-500',
  },
  {
    icon: '🎮',
    title: 'Trò chơi học tập',
    description: 'Mỗi bài học là một trò chơi giúp bé ghi nhớ tự nhiên và hứng thú học tập.',
    color: 'text-green-500',
  },
  {
    icon: '👨‍👩‍👧',
    title: 'Phụ huynh dễ theo dõi',
    description: 'Xem tiến độ, thành tích và thời gian học của con chỉ với vài thao tác.',
    color: 'text-yellow-500',
  },
])
// ... (bên dưới const reviews = ref([...]))

const featuredLessons = ref([
  {
    image:
      'https://images.pexels.com/photos/4145190/pexels-photo-4145190.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
    tag: { text: 'Mới', bg: 'bg-yellow-400' },
    grade: 'Lớp 1',
    duration: '5 phút',
    title: 'Học đếm từ 1 đến 10',
    description: 'Cùng chú gấu dễ thương học đếm qua bài hát vui nhộn.',
    rating: 3,
  },
  {
    image:
      'https://images.pexels.com/photos/5905445/pexels-photo-5905445.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
    tag: null,
    grade: 'Lớp 2',
    duration: '7 phút',
    title: 'Bảng chữ cái vui nhộn',
    description: 'Học 29 chữ cái qua các bài hát và hình ảnh sinh động.',
    rating: 4,
  },
  {
    image:
      'https://images.pexels.com/photos/4056461/pexels-photo-4056461.jpeg?auto=compress&cs=tinysrgb&w=1260&h=750&dpr=1',
    tag: { text: 'Phổ biến', bg: 'bg-pink-500' },
    grade: 'Lớp 3',
    duration: '6 phút',
    title: 'Khám phá hệ mặt trời',
    description: 'Hành trình thú vị qua 8 hành tinh trong hệ mặt trời.',
    rating: 3,
  },
])

const courses = ref([
  {
    title: 'Toán học vui nhộn',
    description: 'Khám phá phép tính qua trò chơi và thử thách hấp dẫn.',
    bg: 'bg-pink-100',
  },
  {
    title: 'Tiếng Việt',
    description: 'Luyện đọc hiểu, chính tả và viết sáng tạo với câu chuyện gần gũi.',
    bg: 'bg-yellow-100',
  },
  {
    title: 'Tiếng Anh',
    description: 'Phát âm và học từ vựng qua hình ảnh và âm thanh sinh động.',
    bg: 'bg-green-100',
  },
  {
    title: 'Khoa học',
    description: 'Tìm hiểu thế giới quanh ta qua video minh họa hấp dẫn.',
    bg: 'bg-blue-100',
  },
  {
    title: 'Mỹ thuật',
    description: 'Phát triển óc sáng tạo với bài học vẽ và tô màu trực tuyến.',
    bg: 'bg-purple-100',
  },
  {
    title: 'Tin học cơ bản',
    description: 'Làm quen máy tính và lập trình Scratch cho trẻ nhỏ.',
    bg: 'bg-pink-200',
  },
])

const benefits = ref([
  'Học mọi lúc, mọi nơi trên điện thoại, máy tính bảng hoặc PC.',
  'Nội dung được biên soạn theo chương trình tiểu học Việt Nam.',
  'Theo dõi tiến độ học và điểm số dễ dàng.',
  'Giao diện thân thiện, nhiều màu sắc giúp trẻ thích thú.',
  'Hỗ trợ 24/7 và cập nhật bài học mới hàng tuần.',
])

const reviews = ref([
  {
    name: 'Chị Lan',
    info: 'Phụ huynh bé Minh – lớp 3',
    text: 'Con tôi rất thích các trò chơi Toán và Tiếng Việt, học mà vẫn cười tươi mỗi ngày!',
  },
  {
    name: 'Anh Dũng',
    info: 'Phụ huynh bé Linh – lớp 4',
    text: 'Giao diện dễ dùng, bài học sinh động, con tự học được mà không cần nhắc nhở.',
  },
  {
    name: 'Cô Mai',
    info: 'Giáo viên tiểu học',
    text: 'Nội dung rất sát chương trình, tôi khuyến khích học sinh của mình sử dụng.',
  },
])
</script>

<style scoped>
html {
  scroll-behavior: smooth;
}

.animate-fade-in {
  animation: fadeIn 1.2s ease-in-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }

  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
