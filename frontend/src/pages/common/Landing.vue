<template>
  <div class="min-h-screen">
    <header class="bg-gradient-to-r from-purple-500 to-pink-500 shadow-lg">
      <div class="container mx-auto px-4 py-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center space-x-2">
            <LogoEduriot :size="70" primary="#E0E7FF" accent="#FFD166" />
          </div>
          <nav class="hidden md:flex space-x-6">
            <a href="#" class="text-white hover:text-yellow-200 font-medium">Trang chủ</a>
            <a href="#" class="text-white hover:text-yellow-200 font-medium">Bài học</a>
            <a href="#" class="text-white hover:text-yellow-200 font-medium">Trò chơi</a>
            <a href="#" class="text-white hover:text-yellow-200 font-medium">Hồ sơ</a>
            <a href="#" class="text-white hover:text-yellow-200 font-medium">Phụ huynh</a>
          </nav>
          <div class="flex items-center space-x-4">
            <button
              class="bg-white text-purple-600 px-4 py-2 rounded-full font-bold hover:bg-yellow-200 transition"
            >
              <router-link to="/auth/login">Đăng nhập</router-link>
            </button>
            <button class="md:hidden text-white" @click="toggleMobileMenu">
              <i data-feather="menu"></i>
            </button>
          </div>
        </div>
      </div>
    </header>

    <section class="bg-gradient-to-br from-blue-100 to-purple-100 py-12">
      <div class="container mx-auto px-4">
        <div class="flex flex-col md:flex-row items-center">
          <div class="md:w-1/2 mb-8 md:mb-0" data-aos="fade-right">
            <h2 class="text-4xl font-bold text-purple-800 mb-4">
              Học tập vui vẻ, Khám phá thế giới!
            </h2>
            <p class="text-lg text-gray-700 mb-6">
              Nơi bé từ lớp 1 đến lớp 5 học tập qua những bài giảng sinh động và trò chơi thú vị.
            </p>
            <div class="flex space-x-4">
              <button
                class="bg-purple-600 hover:bg-purple-700 text-white px-6 py-3 rounded-full font-bold shadow-lg transition"
              >
                <router-link to="/auth/login">Bắt đầu học ngay</router-link>
              </button>
              <button
                class="bg-white hover:bg-gray-100 text-purple-600 px-6 py-3 rounded-full font-bold shadow-lg transition"
              >
                <i data-feather="play-circle" class="inline mr-2"></i> Xem video
              </button>
            </div>
          </div>
          <div class="md:w-1/2" data-aos="fade-left">
            <img
              src="http://static.photos/education/640x360/2"
              alt="Kids learning"
              class="w-full rounded-lg shadow-xl bounce"
            />
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-white">
      <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center text-purple-800 mb-12">Các Môn Học</h2>
        <div class="grid grid-cols-2 md:grid-cols-5 gap-6">
          <div
            v-for="(subject, index) in subjects"
            :key="subject.name"
            class="subject-card rounded-xl p-6 text-center cursor-pointer transition"
            :class="subject.bgColor"
            :data-aos-delay="index * 100"
            data-aos="zoom-in"
            @click="selectSubject(subject.name)"
          >
            <div
              class="w-20 h-20 mx-auto rounded-full flex items-center justify-center mb-4"
              :class="subject.iconBgColor"
            >
              <i :data-feather="subject.icon" class="w-10 h-10" :class="subject.iconTextColor"></i>
            </div>
            <h3 class="font-bold text-xl mb-2" :class="subject.textColor">
              {{ subject.name }}
            </h3>
            <p class="text-gray-600">{{ subject.description }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-gray-50">
      <div class="container mx-auto px-4">
        <div class="flex justify-between items-center mb-12">
          <h2 class="text-3xl font-bold text-purple-800">Bài học nổi bật</h2>
          <a href="#" class="text-purple-600 font-medium hover:underline">Xem tất cả</a>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            v-for="(lesson, index) in featuredLessons"
            :key="lesson.title"
            class="bg-white rounded-xl overflow-hidden shadow-lg"
            data-aos="fade-up"
            :data-aos-delay="index * 100"
          >
            <div class="relative">
              <img :src="lesson.image" alt="Lesson" class="w-full h-48 object-cover" />
              <div
                v-if="lesson.tag"
                class="absolute top-2 right-2 px-2 py-1 rounded-full text-xs font-bold"
                :class="lesson.tag.class"
              >
                {{ lesson.tag.text }}
              </div>
            </div>
            <div class="p-6">
              <div class="flex items-center mb-2">
                <span class="text-xs px-2 py-1 rounded mr-2" :class="lesson.grade.class">{{
                  lesson.grade.text
                }}</span>
                <span class="text-gray-500 text-sm"
                  ><i data-feather="clock" class="w-3 h-3 inline mr-1"></i>
                  {{ lesson.duration }}</span
                >
              </div>
              <h3 class="font-bold text-xl mb-2">{{ lesson.title }}</h3>
              <p class="text-gray-600 mb-4">{{ lesson.description }}</p>
              <div class="flex justify-between items-center">
                <div class="flex">
                  <i
                    v-for="n in 5"
                    :key="n"
                    data-feather="star"
                    class="w-4 h-4"
                    :class="
                      n <= lesson.rating ? 'text-yellow-500 fill-yellow-500' : 'text-gray-300'
                    "
                  ></i>
                </div>
                <button
                  class="bg-purple-100 text-purple-600 px-3 py-1 rounded-full text-sm font-medium hover:bg-purple-200"
                >
                  Học ngay
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-white">
      <div class="container mx-auto px-4">
        <div class="flex justify-between items-center mb-12">
          <h2 class="text-3xl font-bold text-purple-800">Trò chơi giáo dục</h2>
          <a href="#" class="text-purple-600 font-medium hover:underline">Xem tất cả</a>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div
            v-for="(game, index) in educationalGames"
            :key="game.title"
            class="game-card rounded-xl p-6 text-center cursor-pointer"
            :class="game.gradient"
            data-aos="zoom-in"
            :data-aos-delay="index * 100"
            @click="selectGame(game.title)"
          >
            <div
              class="bg-white w-24 h-24 mx-auto rounded-full flex items-center justify-center mb-4 shadow-md"
            >
              <i :data-feather="game.icon" class="w-12 h-12" :class="game.iconColor"></i>
            </div>
            <h3 class="font-bold text-xl mb-2" :class="game.textColor">
              {{ game.title }}
            </h3>
            <p class="text-gray-600 mb-4">{{ game.description }}</p>
            <button class="text-white px-4 py-2 rounded-full font-medium" :class="game.buttonClass">
              Chơi ngay
            </button>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-gradient-to-r from-indigo-500 to-blue-500 text-white">
      <div class="container mx-auto px-4">
        <div class="flex flex-col md:flex-row items-center">
          <div class="md:w-1/2 mb-8 md:mb-0" data-aos="fade-right">
            <h2 class="text-3xl font-bold mb-4">Dành cho phụ huynh</h2>
            <p class="text-lg mb-6 opacity-90">
              Theo dõi tiến độ học tập của con và nhận báo cáo chi tiết hàng tuần.
            </p>
            <ul class="space-y-3 mb-8">
              <li class="flex items-center">
                <i data-feather="check-circle" class="w-5 h-5 mr-2 text-green-300"></i>
                Báo cáo học tập chi tiết
              </li>
              <li class="flex items-center">
                <i data-feather="check-circle" class="w-5 h-5 mr-2 text-green-300"></i>
                Gợi ý bài học phù hợp
              </li>
              <li class="flex items-center">
                <i data-feather="check-circle" class="w-5 h-5 mr-2 text-green-300"></i>
                Quản lý thời gian học
              </li>
            </ul>
            <button
              class="bg-white text-indigo-600 px-6 py-3 rounded-full font-bold shadow-lg hover:bg-gray-100 transition"
            >
              Đăng ký tài khoản phụ huynh
            </button>
          </div>
          <div class="md:w-1/2" data-aos="fade-left">
            <img
              src="http://static.photos/education/640x360/6"
              alt="Parent dashboard"
              class="w-full rounded-lg shadow-xl"
            />
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-white">
      <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center text-purple-800 mb-12">
          Phụ huynh nói gì về chúng tôi
        </h2>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div
            v-for="(testimonial, index) in testimonials"
            :key="testimonial.name"
            class="bg-gray-50 p-6 rounded-xl"
            data-aos="fade-up"
            :data-aos-delay="index * 100"
          >
            <div class="flex items-center mb-4">
              <img :src="testimonial.avatar" alt="Parent" class="w-12 h-12 rounded-full mr-4" />
              <div>
                <h4 class="font-bold">{{ testimonial.name }}</h4>
                <p class="text-gray-500 text-sm">{{ testimonial.relation }}</p>
              </div>
            </div>
            <p class="text-gray-700 italic">"{{ testimonial.quote }}"</p>
            <div class="flex mt-4">
              <i
                v-for="n in 5"
                :key="n"
                data-feather="star"
                class="w-4 h-4"
                :class="
                  n <= testimonial.rating ? 'text-yellow-500 fill-yellow-500' : 'text-yellow-500'
                "
              ></i>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section class="py-16 bg-purple-100">
      <div class="container mx-auto px-4 text-center">
        <h2 class="text-3xl font-bold text-purple-800 mb-6">
          Sẵn sàng cho hành trình học tập vui vẻ?
        </h2>
        <p class="text-xl text-gray-700 mb-8 max-w-2xl mx-auto">
          Đăng ký ngay để bé có thể bắt đầu học tập và khám phá thế giới diệu kỳ!
        </p>
        <div class="flex flex-col sm:flex-row justify-center space-y-4 sm:space-y-0 sm:space-x-4">
          <button
            class="bg-purple-600 hover:bg-purple-700 text-white px-8 py-4 rounded-full font-bold shadow-lg text-lg transition"
          >
            Đăng ký miễn phí
          </button>
          <button
            class="bg-white hover:bg-gray-100 text-purple-600 px-8 py-4 rounded-full font-bold shadow-lg text-lg transition"
          >
            <i data-feather="play-circle" class="inline mr-2"></i> Xem demo
          </button>
        </div>
      </div>
    </section>

    <footer class="bg-gray-800 text-white py-12">
      <div class="container mx-auto px-4">
        <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <LogoEduriot :size="90" primary="#E0E7FF" accent="#FFD166" />
            <h3 class="text-xl font-bold mb-4">Học Vui</h3>
            <p class="text-gray-400">
              Nền tảng học tập trực tuyến hàng đầu dành cho học sinh tiểu học.
            </p>
          </div>

          <div>
            <h4 class="font-bold text-lg mb-4">Liên kết</h4>
            <ul class="space-y-2">
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Trang chủ</a>
              </li>
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Về chúng tôi</a>
              </li>
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Bài học</a>
              </li>
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Trò chơi</a>
              </li>
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Liên hệ</a>
              </li>
            </ul>
          </div>

          <div>
            <h4 class="font-bold text-lg mb-4">Hỗ trợ</h4>
            <ul class="space-y-2">
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Câu hỏi thường gặp</a>
              </li>
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Hướng dẫn sử dụng</a>
              </li>
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Chính sách bảo mật</a>
              </li>
              <li>
                <a href="#" class="text-gray-400 hover:text-white">Điều khoản sử dụng</a>
              </li>
            </ul>
          </div>

          <div>
            <h4 class="font-bold text-lg mb-4">Kết nối với chúng tôi</h4>
            <div class="flex space-x-4 mb-4">
              <a
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
              </a>
            </div>
            <p class="text-gray-400">Email: support@hocvui.edu.vn</p>
            <p class="text-gray-400">Hotline: 1900 1234</p>
          </div>
        </div>

        <div class="border-t border-gray-700 mt-12 pt-8 text-center text-gray-400">
          <p>© 2023 Học Vui. Tất cả quyền được bảo lưu.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { onMounted, nextTick, ref } from 'vue'
import AOS from 'aos'
import feather from 'feather-icons'
import 'aos/dist/aos.css'
import LogoEduriot from '@/components/ui/LogoEduriot.vue'

// Reactive data for dynamic content
const subjects = ref([
  {
    name: 'Toán học',
    description: 'Con số thú vị',
    icon: 'plus',
    bgColor: 'bg-yellow-100',
    iconBgColor: 'bg-yellow-200',
    textColor: 'text-yellow-800',
    iconTextColor: 'text-yellow-700',
  },
  {
    name: 'Tiếng Việt',
    description: 'Ngôn ngữ diệu kỳ',
    icon: 'book',
    bgColor: 'bg-blue-100',
    iconBgColor: 'bg-blue-200',
    textColor: 'text-blue-800',
    iconTextColor: 'text-blue-700',
  },
  {
    name: 'Khoa học',
    description: 'Khám phá tự nhiên',
    icon: 'flask',
    bgColor: 'bg-green-100',
    iconBgColor: 'bg-green-200',
    textColor: 'text-green-800',
    iconTextColor: 'text-green-700',
  },
  {
    name: 'Lịch sử',
    description: 'Hành trình thời gian',
    icon: 'clock',
    bgColor: 'bg-red-100',
    iconBgColor: 'bg-red-200',
    textColor: 'text-red-800',
    iconTextColor: 'text-red-700',
  },
  {
    name: 'Địa lý',
    description: 'Thế giới quanh ta',
    icon: 'globe',
    bgColor: 'bg-purple-100',
    iconBgColor: 'bg-purple-200',
    textColor: 'text-purple-800',
    iconTextColor: 'text-purple-700',
  },
])

const featuredLessons = ref([
  {
    image: 'http://static.photos/education/640x360/3',
    tag: { text: 'Mới', class: 'bg-yellow-400 text-white' },
    grade: { text: 'Lớp 1', class: 'bg-blue-100 text-blue-800' },
    duration: '5 phút',
    title: 'Học đếm từ 1 đến 10',
    description: 'Cùng chú gấu dễ thương học đếm qua bài hát vui nhộn',
    rating: 4,
  },
  {
    image: 'http://static.photos/education/640x360/4',
    tag: null,
    grade: { text: 'Lớp 2', class: 'bg-green-100 text-green-800' },
    duration: '7 phút',
    title: 'Bảng chữ cái vui nhộn',
    description: 'Học 29 chữ cái qua các bài hát và hình ảnh sinh động',
    rating: 5,
  },
  {
    image: 'http://static.photos/education/640x360/5',
    tag: { text: 'Phổ biến', class: 'bg-red-400 text-white' },
    grade: { text: 'Lớp 3', class: 'bg-purple-100 text-purple-800' },
    duration: '6 phút',
    title: 'Khám phá hệ mặt trời',
    description: 'Hành trình thú vị qua 8 hành tinh trong hệ mặt trời',
    rating: 4,
  },
])

const educationalGames = ref([
  {
    gradient: 'bg-gradient-to-br from-yellow-100 to-yellow-200',
    icon: 'plus-circle',
    iconColor: 'text-yellow-600',
    title: 'Toán nhanh',
    description: 'Tính toán thần tốc',
    textColor: 'text-yellow-800',
    buttonClass: 'bg-yellow-400 hover:bg-yellow-500',
  },
  {
    gradient: 'bg-gradient-to-br from-blue-100 to-blue-200',
    icon: 'book-open',
    iconColor: 'text-blue-600',
    title: 'Ghép từ',
    description: 'Rèn luyện từ vựng',
    textColor: 'text-blue-800',
    buttonClass: 'bg-blue-400 hover:bg-blue-500',
  },
  {
    gradient: 'bg-gradient-to-br from-green-100 to-green-200',
    icon: 'puzzle',
    iconColor: 'text-green-600',
    title: 'Câu đố',
    description: 'Rèn trí thông minh',
    textColor: 'text-green-800',
    buttonClass: 'bg-green-400 hover:bg-green-500',
  },
  {
    gradient: 'bg-gradient-to-br from-purple-100 to-purple-200',
    icon: 'award',
    iconColor: 'text-purple-600',
    title: 'Đố vui',
    description: 'Kiến thức tổng hợp',
    textColor: 'text-purple-800',
    buttonClass: 'bg-purple-400 hover:bg-purple-500',
  },
])

const testimonials = ref([
  {
    avatar: 'http://static.photos/people/200x200/1',
    name: 'Chị Nguyễn Thị Mai',
    relation: 'Phụ huynh bé Minh Anh',
    quote:
      'Bé nhà mình rất thích học trên Học Vui, mỗi ngày đều đòi mở bài học mới. Mình thấy chương trình rất phù hợp với lứa tuổi các bé.',
    rating: 5,
  },
  {
    avatar: 'http://static.photos/people/200x200/2',
    name: 'Anh Trần Văn Nam',
    relation: 'Phụ huynh bé Tuấn Anh',
    quote:
      'Tôi rất hài lòng với hệ thống báo cáo học tập hàng tuần. Nó giúp tôi theo dõi được sự tiến bộ của con rõ ràng.',
    rating: 4,
  },
  {
    avatar: 'http://static.photos/people/200x200/3',
    name: 'Chị Lê Thị Hương',
    relation: 'Phụ huynh bé Ngọc Linh',
    quote:
      'Các trò chơi giáo dục rất thú vị, bé nhà mình vừa học vừa chơi mà tiếp thu kiến thức rất nhanh. Cảm ơn Học Vui!',
    rating: 5,
  },
])

onMounted(() => {
  // Initialize AOS animation
  AOS.init({
    duration: 800,
    easing: 'ease-in-out',
    once: true,
  })

  // Use nextTick to ensure the DOM is updated before replacing icons
  nextTick(() => {
    feather.replace()
  })
})

// Methods
const selectSubject = (subject) => {
  alert(`Bạn đã chọn môn: ${subject}. Tính năng đang được phát triển!`)
}

const selectGame = (game) => {
  alert(`Bạn đã chọn trò chơi: ${game}. Tính năng đang được phát triển!`)
}

const toggleMobileMenu = () => {
  alert('Menu di động sẽ hiển thị tại đây!')
}
</script>

<style scoped>
@import url('https://fonts.googleapis.com/css2?family=Baloo+2:wght@400;500;600;700&display=swap');

@tailwind base;
@tailwind components;
@tailwind utilities;
:root {
  --primary: #ff6b6b;
  --secondary: #4ecdc4;
  --accent: #ffe66d;
  --dark: #292f36;
  --light: #f7fff7;
}

body {
  font-family: 'Baloo 2', cursive;
  background-color: #f9f9f9;
  color: var(--dark);
}

.subject-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.game-card {
  transition: all 0.3s ease;
}

.game-card:hover {
  transform: scale(1.05);
}

.progress-ring__circle {
  transition: stroke-dashoffset 0.5s;
  transform: rotate(-90deg);
  transform-origin: 50% 50%;
}

.avatar-selector {
  transition: all 0.3s ease;
}

.avatar-selector:hover {
  transform: scale(1.1);
  border-color: var(--primary);
}

.bounce {
  animation: bounce 2s infinite;
}

@keyframes bounce {
  0%,
  20%,
  50%,
  80%,
  100% {
    transform: translateY(0);
  }

  40% {
    transform: translateY(-15px);
  }

  60% {
    transform: translateY(-7px);
  }
}
</style>
