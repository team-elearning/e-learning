<template>
  <div class="not-found-container">
    <div class="not-found-content">
      <h1>404</h1>
      <h2>Oops! Trang không tồn tại.</h2>
      <p>Trang bạn tìm kiếm không được tìm thấy hoặc đã bị di chuyển.</p>
      <router-link to="/" class="home-link">Quay về trang chủ</router-link>
    </div>
  </div>
</template>

<script setup>
// Không cần script cho trang này
</script>

<style scoped>
.not-found-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #f8fafc 0%, #e0e7ff 100%);
}

.not-found-content {
  text-align: center;
  background: #fff;
  padding: 48px 32px;
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(60, 72, 88, 0.12);
}

.not-found-content h1 {
  font-size: 6rem;
  color: #6366f1;
  margin-bottom: 0.5rem;
  font-weight: 800;
  letter-spacing: 2px;
}

.not-found-content h2 {
  font-size: 2rem;
  color: #334155;
  margin-bottom: 1rem;
}

.not-found-content p {
  color: #64748b;
  margin-bottom: 2rem;
}

.home-link {
  display: inline-block;
  padding: 12px 32px;
  background: #6366f1;
  color: #fff;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 600;
  transition: background 0.2s;
}

.home-link:hover {
  background: #4f46e5;
}
</style>
