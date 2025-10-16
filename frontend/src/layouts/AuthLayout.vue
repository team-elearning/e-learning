<template>
  <div class="kids-auth-layout-green">
    <!-- Minimal Background -->
    <div class="green-background">
      <div class="green-orb orb-1"></div>
      <div class="green-orb orb-2"></div>
    </div>

    <!-- Home Button -->
    <router-link to="/" class="home-btn-green">
      <div class="home-icon-wrapper">
        <svg class="home-icon" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2.5"
            d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
          />
        </svg>
      </div>
      <div class="home-tooltip">Về trang chủ</div>
    </router-link>

    <!-- Main Container -->
    <div class="auth-container-equal">
      <!-- Left Column -->
      <section class="welcome-column">
        <div class="welcome-content">
          <!-- Mascot -->
          <div class="mascot-area">
            <div class="mascot-glow-green"></div>
            <div class="mascot-char">🦁</div>
          </div>

          <!-- Title -->
          <h1 class="main-title">Chào bạn nhỏ! 👋</h1>
          <p class="main-subtitle">Sẵn sàng học bài mới chưa?</p>

          <!-- Features -->
          <div class="features-grid">
            <div class="feature-box" v-for="(f, i) in features" :key="i">
              <div class="feature-emoji">{{ f.icon }}</div>
              <div class="feature-name">{{ f.text }}</div>
            </div>
          </div>

          <!-- Stats -->
          <div class="stats-grid">
            <div class="stat-box" v-for="(s, i) in stats" :key="i">
              <div class="stat-icon">{{ s.emoji }}</div>
              <div class="stat-num">{{ s.number }}</div>
              <div class="stat-text">{{ s.label }}</div>
            </div>
          </div>
        </div>

        <!-- Single Float -->
        <div class="float-emoji">📚</div>
      </section>

      <!-- Right Column -->
      <section class="form-column">
        <div class="form-box">
          <!-- Logo -->
          <div class="logo-area">
            <LogoEduriot :size="100" />
          </div>

          <!-- Title -->
          <div class="form-heading">
            <h2 class="form-title">Đăng nhập 🎓</h2>
            <p class="form-desc">Nhập thông tin để vào lớp học nhé!</p>
          </div>

          <!-- Form -->
          <div class="form-body">
            <router-view v-slot="{ Component }">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
          </div>

          <!-- Footer -->
          <p class="form-footer">
            © {{ new Date().getFullYear() }} EDURIOT - Học vui mỗi ngày! 🌈
          </p>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import LogoEduriot from '@/components/ui/LogoEduriot.vue'

const features = ref([
  { icon: '🎮', text: 'Học qua trò chơi' },
  { icon: '🏆', text: 'Nhận huy chương' },
  { icon: '📊', text: 'Xem tiến độ' },
])

const stats = ref([
  { emoji: '👦', number: '50K+', label: 'Học sinh' },
  { emoji: '📚', number: '1000+', label: 'Bài học' },
  { emoji: '⭐', number: '4.9', label: 'Đánh giá' },
])
</script>

<style scoped>
/* 🌿 BASE */
.kids-auth-layout-green {
  width: 100vw;
  height: 100vh;
  position: fixed;
  inset: 0;
  overflow: hidden;
  background: linear-gradient(135deg, #d1fae5, #a7f3d0, #6ee7b7);
  animation: fade-in 0.5s ease-out;
}

@keyframes fade-in {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

/* 🍃 BACKGROUND */
.green-background {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}

.green-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0;
  animation: orb-appear 1s ease-out 0.2s forwards;
}

@keyframes orb-appear {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 0.25;
    transform: scale(1);
  }
}

.orb-1 {
  width: 350px;
  height: 350px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.4), transparent);
  top: -10%;
  left: -10%;
}

.orb-2 {
  width: 300px;
  height: 300px;
  background: radial-gradient(circle, rgba(20, 184, 166, 0.4), transparent);
  bottom: -10%;
  right: -10%;
  animation-delay: 0.4s;
}

/* 🏠 HOME BUTTON */
.home-btn-green {
  position: fixed;
  top: 1.5rem;
  left: 1.5rem;
  z-index: 100;
  animation: slide-in-left 0.6s ease-out;
}

@keyframes slide-in-left {
  from {
    opacity: 0;
    transform: translateX(-30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.home-icon-wrapper {
  position: relative;
  width: 3.5rem;
  height: 3.5rem;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 20px rgba(16, 185, 129, 0.4);
  transition: transform 0.2s;
}

.home-btn-green:hover .home-icon-wrapper {
  transform: translateY(-2px);
}

.home-icon {
  width: 1.75rem;
  height: 1.75rem;
  color: white;
}

.home-tooltip {
  position: absolute;
  left: calc(100% + 1rem);
  top: 50%;
  transform: translateY(-50%);
  padding: 0.5rem 1rem;
  background: #1f2937;
  color: white;
  font-size: 0.875rem;
  font-weight: 700;
  border-radius: 10px;
  white-space: nowrap;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.2s;
}

.home-btn-green:hover .home-tooltip {
  opacity: 1;
}

/* 📦 GRID */
.auth-container-equal {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 1fr 1fr;
  height: 100vh;
  width: 100vw;
}

/* 🌟 LEFT COLUMN */
.welcome-column {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
  background: rgba(16, 185, 129, 0.08);
  overflow-y: auto;
  overflow-x: hidden;
  animation: slide-in-left 0.7s ease-out 0.2s both;
}

.welcome-content {
  width: 100%;
  max-width: 550px;
}

.mascot-area {
  position: relative;
  width: 120px;
  height: 120px;
  margin: 0 auto 1.5rem;
  animation: scale-in 0.6s ease-out 0.4s both;
}

@keyframes scale-in {
  from {
    opacity: 0;
    transform: scale(0.5);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.mascot-glow-green {
  position: absolute;
  inset: -10px;
  background: linear-gradient(135deg, #10b981, #14b8a6);
  border-radius: 50%;
  filter: blur(15px);
  opacity: 0.4;
  animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.4;
  }
  50% {
    opacity: 0.6;
  }
}

.mascot-char {
  position: relative;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #d1fae5, #a7f3d0);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 4rem;
  box-shadow: 0 8px 24px rgba(16, 185, 129, 0.25);
}

.main-title {
  font-size: 2.25rem;
  font-weight: 900;
  color: #1f2937;
  text-align: center;
  margin-bottom: 0.5rem;
  animation: fade-in-up 0.6s ease-out 0.5s both;
}

@keyframes fade-in-up {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.main-subtitle {
  font-size: 1.125rem;
  font-weight: 700;
  color: #10b981;
  text-align: center;
  margin-bottom: 2rem;
  animation: fade-in-up 0.6s ease-out 0.6s both;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.feature-box {
  padding: 1.25rem 0.75rem;
  background: white;
  border-radius: 16px;
  text-align: center;
  border: 2px solid rgba(16, 185, 129, 0.2);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.08);
  transition:
    transform 0.2s,
    box-shadow 0.2s;
  animation: fade-in-up 0.5s ease-out both;
}

.feature-box:nth-child(1) {
  animation-delay: 0.7s;
}
.feature-box:nth-child(2) {
  animation-delay: 0.8s;
}
.feature-box:nth-child(3) {
  animation-delay: 0.9s;
}

.feature-box:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.15);
}

.feature-emoji {
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
}

.feature-name {
  font-size: 0.875rem;
  font-weight: 700;
  color: #374151;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
}

.stat-box {
  padding: 1.25rem 0.75rem;
  background: white;
  border-radius: 16px;
  text-align: center;
  border: 2px solid rgba(16, 185, 129, 0.2);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.08);
  animation: fade-in-up 0.5s ease-out both;
}

.stat-box:nth-child(1) {
  animation-delay: 1s;
}
.stat-box:nth-child(2) {
  animation-delay: 1.1s;
}
.stat-box:nth-child(3) {
  animation-delay: 1.2s;
}

.stat-icon {
  font-size: 1.75rem;
  margin-bottom: 0.5rem;
}

.stat-num {
  font-size: 1.25rem;
  font-weight: 900;
  color: #10b981;
  margin-bottom: 0.25rem;
}

.stat-text {
  font-size: 0.75rem;
  color: #6b7280;
  font-weight: 600;
}

.float-emoji {
  position: absolute;
  bottom: 15%;
  right: 15%;
  font-size: 2.5rem;
  opacity: 0;
  animation:
    float 6s ease-in-out infinite,
    fade-in 0.6s ease-out 1.3s forwards;
}

@keyframes float {
  0%,
  100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-15px);
  }
}

/* 📝 RIGHT COLUMN */
.form-column {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem 1.5rem;
  background: rgba(255, 255, 255, 0.5);
  backdrop-filter: blur(8px);
  overflow-y: auto;
  overflow-x: hidden;
  animation: slide-in-right 0.7s ease-out 0.3s both;
}

@keyframes slide-in-right {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.form-box {
  width: 100%;
  max-width: 440px;
  padding: 2.5rem 2rem;
  background: white;
  border-radius: 24px;
  border: 2px solid rgba(16, 185, 129, 0.2);
  box-shadow: 0 12px 40px rgba(16, 185, 129, 0.12);
  animation: scale-in 0.6s ease-out 0.5s both;
}

.logo-area {
  display: flex;
  justify-content: center;
  margin-bottom: 1.5rem;
}

.form-heading {
  text-align: center;
  margin-bottom: 2rem;
}

.form-title {
  font-size: 2rem;
  font-weight: 900;
  color: #1f2937;
  margin-bottom: 0.5rem;
}

.form-desc {
  font-size: 1rem;
  color: #6b7280;
  font-weight: 600;
}

.form-body {
  margin-bottom: 1.5rem;
}

.form-footer {
  text-align: center;
  font-size: 0.8125rem;
  color: #9ca3af;
  font-weight: 600;
}

/* 🎬 TRANSITION */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.15s;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 📱 RESPONSIVE */
@media (max-width: 1024px) {
  .auth-container-equal {
    grid-template-columns: 1fr;
  }

  .welcome-column {
    display: none;
  }

  .form-column {
    padding: 1.5rem 1rem;
    animation: fade-in 0.5s ease-out;
  }

  .form-box {
    padding: 2rem 1.5rem;
    max-width: 100%;
    animation: fade-in-up 0.6s ease-out 0.2s both;
  }

  .home-btn-green {
    top: 1rem;
    left: 1rem;
  }

  .home-icon-wrapper {
    width: 3rem;
    height: 3rem;
  }

  .home-icon {
    width: 1.5rem;
    height: 1.5rem;
  }

  .home-tooltip {
    display: none;
  }
}

@media (max-width: 640px) {
  .form-column {
    padding: 1rem 0.75rem;
  }

  .form-box {
    padding: 1.5rem 1.25rem;
    border-radius: 20px;
  }

  .form-title {
    font-size: 1.75rem;
  }

  .form-desc {
    font-size: 0.9375rem;
  }

  .logo-area {
    margin-bottom: 1.25rem;
  }

  .home-btn-green {
    top: 0.75rem;
    left: 0.75rem;
  }

  .home-icon-wrapper {
    width: 2.75rem;
    height: 2.75rem;
  }
}

@media (max-width: 480px) {
  .form-box {
    padding: 1.25rem 1rem;
  }

  .form-title {
    font-size: 1.5rem;
  }

  .form-heading {
    margin-bottom: 1.5rem;
  }
}
</style>
