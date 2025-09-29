<template>
  <div class="page">
    <div class="container">
      <h1 class="title">Thanh toán</h1>

      <div class="grid">
        <div class="card method">
          <h2>Chuyển khoản qua VietQR</h2>
          <p>Quét mã QR bằng App ngân hàng (NAPAS 247) để thanh toán nhanh chóng.</p>
          <div class="actions">
            <button class="btn-primary" :disabled="loading" @click="goCheckout">
              <span v-if="loading" class="spinner" />
              <span>Tiếp tục</span>
            </button>
          </div>
        </div>

        <div class="card method muted">
          <h2>Thẻ/Tài khoản (Đang phát triển)</h2>
          <p>Tính năng này sẽ sớm có mặt.</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)

// Prefetch chunk của Checkout.vue để click là chuyển ngay
onMounted(() => {
  // Không cần giữ reference, chỉ cần import để trình duyệt tải sẵn
  import('@/pages/student/payments/Checkout.vue')
})

async function goCheckout() {
  if (loading.value) return
  loading.value = true
  try {
    await router.push({ name: 'student-payments-checkout' })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
:root{ --accent:#16a34a; --line:#e5e7eb; --muted:#6b7280; }
.page{ background:#f6f7fb; min-height:100vh; }
.container{ max-width:1000px; margin:0 auto; padding:24px 16px 40px; }
.title{ font-size:22px; font-weight:800; margin-bottom:12px; }
.grid{ display:grid; grid-template-columns: 1fr 1fr; gap:16px; }
.card{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px; }
.method h2{ margin:0 0 6px; }
.method.muted{ color:var(--muted); }
.actions{ margin-top:10px; display:flex; gap:8px; }

.btn-primary{
  background:var(--accent); color:#fff; border:1px solid var(--accent);
  padding:10px 14px; border-radius:10px; font-weight:800; cursor:pointer;
  display:inline-flex; align-items:center; gap:8px;
}
.btn-primary[disabled]{ opacity:.7; cursor:not-allowed; }

.spinner{
  width:16px; height:16px; border:2px solid rgba(255,255,255,.6);
  border-top-color:#fff; border-radius:50%; animation:spin .8s linear infinite;
}
@keyframes spin{ to{ transform:rotate(360deg); } }

@media (max-width: 900px){ .grid{ grid-template-columns: 1fr; } }
</style>
