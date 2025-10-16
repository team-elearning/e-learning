<template>
  <div class="min-h-screen w-screen bg-gradient-to-br from-slate-50 via-emerald-50/30 to-sky-50 flex relative overflow-hidden">
    
    <!-- Glassmorphism Home Button -->
    <router-link 
      to="/"
      class="fixed top-8 left-8 z-50 group"
      title="Về trang chủ"
    >
      <div class="relative">
        <!-- Animated Glow Effect -->
        <div class="absolute inset-0 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl blur-xl opacity-40 group-hover:opacity-70 group-hover:scale-110 transition-all duration-500"></div>
        
        <!-- Glass Button -->
        <div class="relative flex items-center justify-center w-14 h-14 rounded-2xl bg-white/10 backdrop-blur-xl border border-white/20 shadow-lg shadow-emerald-500/20 hover:bg-white/20 hover:scale-110 hover:rotate-12 hover:shadow-emerald-500/40 transition-all duration-300">
          <svg 
            class="w-6 h-6 text-white drop-shadow-lg" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path 
              stroke-linecap="round" 
              stroke-linejoin="round" 
              stroke-width="2.5" 
              d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" 
            />
          </svg>
        </div>

        <!-- Tooltip on Hover -->
        <div class="absolute left-full ml-4 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 transition-all duration-300 pointer-events-none">
          <div class="px-3 py-1.5 bg-gray-900/90 backdrop-blur-sm text-white text-xs font-medium rounded-lg shadow-xl whitespace-nowrap">
            Về trang chủ
            <div class="absolute right-full top-1/2 -translate-y-1/2 border-4 border-transparent border-r-gray-900/90"></div>
          </div>
        </div>
      </div>
    </router-link>

    <!-- Animated background shapes -->
    <div class="absolute inset-0 overflow-hidden pointer-events-none">
      <div class="shape shape-1"></div>
      <div class="shape shape-2"></div>
      <div class="shape shape-3"></div>
      <div class="shape shape-4"></div>
    </div>

    <!-- Cột trái -->
    <section class="relative hidden lg:flex w-1/2 items-center justify-center overflow-hidden">
      <div class="absolute inset-0 bg-gradient-to-br from-emerald-600 via-teal-500 to-cyan-600 animate-gradient-xy"></div>
      
      <div class="absolute inset-0 opacity-10">
        <div class="grid-pattern"></div>
      </div>

      <div class="absolute inset-0">
        <div class="floating-element floating-1"></div>
        <div class="floating-element floating-2"></div>
        <div class="floating-element floating-3"></div>
      </div>

      <div class="relative z-10 px-12 text-white max-w-lg">
        <div class="transform transition-all duration-1000 animate-fade-in-up">
          <div class="mb-8">
            <div class="inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-white/20 backdrop-blur-lg mb-6 animate-bounce-slow">
              <svg class="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
          </div>
          
          <h1 class="text-4xl font-bold mb-4 leading-tight">
            Welcome to Your
            <span class="block text-transparent bg-clip-text bg-gradient-to-r from-yellow-200 to-orange-200 animate-shimmer">
              Learning Space
            </span>
          </h1>
          
          <p class="text-lg text-emerald-50 mb-8 leading-relaxed">
            Học tập hiệu quả, quản lý lớp học thông minh, báo cáo rõ ràng.
          </p>

          <div class="space-y-4">
            <div class="flex items-center gap-3 animate-slide-in-left" style="animation-delay: 0.2s">
              <div class="flex-shrink-0 w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span class="text-white/90">Học tập cá nhân hóa</span>
            </div>
            
            <div class="flex items-center gap-3 animate-slide-in-left" style="animation-delay: 0.4s">
              <div class="flex-shrink-0 w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span class="text-white/90">Theo dõi tiến độ real-time</span>
            </div>
            
            <div class="flex items-center gap-3 animate-slide-in-left" style="animation-delay: 0.6s">
              <div class="flex-shrink-0 w-10 h-10 rounded-lg bg-white/20 backdrop-blur-sm flex items-center justify-center">
                <svg class="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <span class="text-white/90">Báo cáo chi tiết & insights</span>
            </div>
          </div>
        </div>
      </div>

      <!-- LIQUID MORPHING EFFECT -->
      <div class="absolute bottom-0 left-0 right-0 h-48 pointer-events-none overflow-hidden">
        <svg class="absolute bottom-0 w-full h-full" viewBox="0 0 1440 320" preserveAspectRatio="none">
          <defs>
            <filter id="goo">
              <feGaussianBlur in="SourceGraphic" stdDeviation="15" result="blur" />
              <feColorMatrix in="blur" mode="matrix" values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 25 -10" result="goo" />
              <feComposite in="SourceGraphic" in2="goo" operator="atop"/>
            </filter>
          </defs>
          <g filter="url(#goo)">
            <circle cx="100" cy="250" r="80" fill="#1a1a1a" class="liquid-blob blob-1"/>
            <circle cx="350" cy="280" r="100" fill="#1a1a1a" class="liquid-blob blob-2"/>
            <circle cx="600" cy="260" r="90" fill="#0d0d0d" class="liquid-blob blob-3"/>
            <circle cx="850" cy="270" r="110" fill="#0d0d0d" class="liquid-blob blob-4"/>
            <circle cx="1100" cy="250" r="85" fill="#000000" class="liquid-blob blob-5"/>
            <circle cx="1350" cy="280" r="95" fill="#000000" class="liquid-blob blob-6"/>
            <rect x="0" y="280" width="1440" height="40" fill="#000000"/>
          </g>
        </svg>
      </div>
    </section>

    <!-- Cột phải -->
    <section class="flex w-full lg:w-1/2 items-center justify-center relative z-10">
      <div class="w-full max-w-md p-6 sm:p-8 animate-fade-in">
        <div class="mb-8 text-center">
          <div class="flex justify-center mb-6">
            <div class="transform transition-all duration-300 hover:scale-110">
              <LogoEduriot :size="120" />
            </div>
          </div>
          
          <h2 class="text-2xl sm:text-3xl font-bold text-gray-800 mb-2">
            Chào mừng trở lại
          </h2>
          <p class="text-sm text-gray-600">
            Đăng nhập để tiếp tục học tập
          </p>
        </div>

        <div class="rounded-2xl bg-white/80 backdrop-blur-xl p-6 sm:p-8 shadow-2xl shadow-emerald-500/10 ring-1 ring-black/5 transform transition-all duration-500 hover:shadow-emerald-500/20">
          <router-view v-slot="{ Component }">
            <transition name="page" mode="out-in">
              <component :is="Component" />
            </transition>
          </router-view>
        </div>

        <div class="mt-8 text-center">
          <p class="text-xs text-gray-500 mb-4">Bảo mật bởi SSL encryption</p>
          <div class="flex items-center justify-center gap-2 text-gray-400">
            <svg class="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clip-rule="evenodd" />
            </svg>
            <span class="text-xs">Kết nối an toàn</span>
          </div>
        </div>

        <p class="mt-8 text-center text-xs text-gray-400">
          © {{ new Date().getFullYear() }} Eduriot. All rights reserved.
        </p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import LogoEduriot from '@/components/ui/LogoEduriot.vue'
</script>

<style scoped>
/* Gradient Animation */
@keyframes gradient-xy { 
  0%, 100% { background-position: 0% 50%; } 
  50% { background-position: 100% 50%; } 
}
.animate-gradient-xy { 
  background-size: 200% 200%; 
  animation: gradient-xy 15s ease infinite; 
}

/* Floating Background Shapes */
.shape { 
  position: absolute; 
  border-radius: 50%; 
  filter: blur(80px); 
  opacity: 0.3; 
  animation: float 20s ease-in-out infinite; 
}
.shape-1 { 
  width: 500px; 
  height: 500px; 
  background: linear-gradient(135deg, #10b981 0%, #06b6d4 100%); 
  top: -10%; 
  left: -10%; 
}
.shape-2 { 
  width: 400px; 
  height: 400px; 
  background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%); 
  bottom: -10%; 
  right: -10%; 
  animation-delay: -7s; 
}
.shape-3 { 
  width: 300px; 
  height: 300px; 
  background: linear-gradient(135deg, #14b8a6 0%, #0ea5e9 100%); 
  top: 50%; 
  right: 30%; 
  animation-delay: -14s; 
}
.shape-4 { 
  width: 350px; 
  height: 350px; 
  background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%); 
  bottom: 20%; 
  left: 20%; 
  animation-delay: -21s; 
}

@keyframes float { 
  0%, 100% { transform: translate(0, 0) scale(1); } 
  33% { transform: translate(30px, -30px) scale(1.1); } 
  66% { transform: translate(-20px, 20px) scale(0.9); } 
}

/* Grid Pattern */
.grid-pattern { 
  background-image: linear-gradient(rgba(255, 255, 255, 0.1) 1px, transparent 1px), 
                    linear-gradient(90deg, rgba(255, 255, 255, 0.1) 1px, transparent 1px); 
  background-size: 50px 50px; 
  width: 100%; 
  height: 100%; 
  animation: slide-grid 20s linear infinite; 
}

@keyframes slide-grid { 
  0% { background-position: 0 0; } 
  100% { background-position: 50px 50px; } 
}

/* Floating Elements */
.floating-element { 
  position: absolute; 
  border-radius: 50%; 
  background: rgba(255, 255, 255, 0.1); 
  backdrop-filter: blur(10px); 
}
.floating-1 { 
  width: 100px; 
  height: 100px; 
  top: 20%; 
  left: 10%; 
  animation: float-slow 8s ease-in-out infinite; 
}
.floating-2 { 
  width: 150px; 
  height: 150px; 
  bottom: 30%; 
  right: 15%; 
  animation: float-slow 10s ease-in-out infinite reverse; 
}
.floating-3 { 
  width: 80px; 
  height: 80px; 
  top: 60%; 
  left: 70%; 
  animation: float-slow 12s ease-in-out infinite; 
}

@keyframes float-slow { 
  0%, 100% { transform: translateY(0) rotate(0deg); } 
  50% { transform: translateY(-20px) rotate(180deg); } 
}

/* Liquid Blob Animation */
.liquid-blob {
  animation: liquid-move 20s ease-in-out infinite;
  transform-origin: center;
}
.blob-1 { animation-delay: 0s; }
.blob-2 { animation-delay: -3s; }
.blob-3 { animation-delay: -6s; }
.blob-4 { animation-delay: -9s; }
.blob-5 { animation-delay: -12s; }
.blob-6 { animation-delay: -15s; }

@keyframes liquid-move {
  0%, 100% { transform: translate(0, 0) scale(1); }
  25% { transform: translate(-30px, -15px) scale(1.1); }
  50% { transform: translate(20px, 10px) scale(0.95); }
  75% { transform: translate(-20px, 5px) scale(1.05); }
}

/* Shimmer Effect */
@keyframes shimmer { 
  0% { background-position: -200% center; } 
  100% { background-position: 200% center; } 
}
.animate-shimmer { 
  background-size: 200% auto; 
  animation: shimmer 3s linear infinite; 
}

/* Bounce Slow */
@keyframes bounce-slow { 
  0%, 100% { transform: translateY(0); } 
  50% { transform: translateY(-10px); } 
}
.animate-bounce-slow { 
  animation: bounce-slow 3s ease-in-out infinite; 
}

/* Fade In Up */
@keyframes fade-in-up { 
  from { opacity: 0; transform: translateY(30px); } 
  to { opacity: 1; transform: translateY(0); } 
}
.animate-fade-in-up { 
  animation: fade-in-up 0.8s ease-out; 
}

/* Fade In */
@keyframes fade-in { 
  from { opacity: 0; transform: scale(0.95); } 
  to { opacity: 1; transform: scale(1); } 
}
.animate-fade-in { 
  animation: fade-in 0.6s ease-out; 
}

/* Slide In Left */
@keyframes slide-in-left { 
  from { opacity: 0; transform: translateX(-30px); } 
  to { opacity: 1; transform: translateX(0); } 
}
.animate-slide-in-left { 
  animation: slide-in-left 0.6s ease-out both; 
}

/* Page Transition */
.page-enter-active, 
.page-leave-active { 
  transition: all 0.3s ease; 
}
.page-enter-from { 
  opacity: 0; 
  transform: translateY(20px); 
}
.page-leave-to { 
  opacity: 0; 
  transform: translateY(-20px); 
}
</style>
