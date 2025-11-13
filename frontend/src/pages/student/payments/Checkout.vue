<template>
  <div class="pay-page">
    <div class="container">
      <h1 class="title">Thanh toán MoMo</h1>

      <div class="grid">
        <section class="card flow-card">
          <div class="status-chip" :class="statusClass">{{ statusLabel }}</div>
          <h2>Thanh toán trực tuyến với MoMo</h2>
          <p>
            Chúng tôi sẽ chuyển bạn sang cổng MoMo để hoàn tất giao dịch. Vui lòng chuẩn bị ứng dụng MoMo
            hoặc thẻ ngân hàng đã liên kết.
          </p>

          <ol class="steps">
            <li>Kiểm tra lại gói học và số tiền ở khung bên phải.</li>
            <li>Nhấn <strong>Thanh toán bằng MoMo</strong> để tạo yêu cầu thanh toán.</li>
            <li>Hoàn tất giao dịch trong ứng dụng MoMo hoặc trên web.</li>
            <li>Sau khi thành công, bạn sẽ được chuyển về hệ thống và kích hoạt quyền học.</li>
          </ol>

          <p v-if="!canPay" class="note warning">
            Số tiền không hợp lệ. Vui lòng quay lại giỏ hàng để chọn gói học.
          </p>
          <p v-else-if="errorMessage" class="note error">{{ errorMessage }}</p>
          <p v-else class="note muted">
            Nếu cần hỗ trợ, vui lòng liên hệ hotline
            <a href="tel:19001234">1900 1234</a>.
          </p>

          <button class="btn-primary" :disabled="!canPay || isProcessing" @click="payWithMomo">
            <span v-if="isProcessing" class="spinner" />
            {{ isProcessing ? 'Đang chuyển tới MoMo...' : 'Thanh toán bằng MoMo' }}
          </button>

          <div v-if="lastOrderId" class="note success">
            Đã tạo đơn hàng tạm: <strong>{{ lastOrderId }}</strong>
          </div>
        </section>

        <section class="card summary-card">
          <h2 class="section-title">Tóm tắt</h2>
          <div class="summary">
            <div class="line"><span>Gói học</span><b>{{ plan }}</b></div>
            <div class="line"><span>Số tiền</span><b>{{ vnd(amountNumber) }}</b></div>
            <div class="line"><span>Phương thức</span><b>MoMo</b></div>
            <div class="divider"></div>
            <div class="line total"><span>Tổng thanh toán</span><b>{{ vnd(amountNumber) }}</b></div>
          </div>

          <div class="helper">
            <p>MoMo hỗ trợ thẻ ATM, Visa/Mastercard, ví điện tử và chuỗi cửa hàng tiện lợi.</p>
            <ul>
              <li>Không thu phí thêm</li>
              <li>Đối soát tự động trong vài phút</li>
              <li>Bảo mật chuẩn PCI DSS</li>
            </ul>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { paymentService } from '@/services/payment.service'

const route = useRoute()

const plan = computed(() => String(route.query.plan || 'Khoá học Standard'))
const amountNumber = computed(() => {
  const value = Number(route.query.amount)
  return Number.isFinite(value) && value > 0 ? Math.round(value) : 0
})

const status = ref<'idle' | 'processing' | 'error'>('idle')
const errorMessage = ref('')
const lastOrderId = ref('')

const canPay = computed(() => amountNumber.value > 0)
const isProcessing = computed(() => status.value === 'processing')
const statusClass = computed(() => ({
  idle: 'chip-idle',
  processing: 'chip-processing',
  error: 'chip-error',
}[status.value] || 'chip-idle'))
const statusLabel = computed(() => ({
  idle: 'Sẵn sàng thanh toán',
  processing: 'Đang tạo giao dịch',
  error: 'Có lỗi',
}[status.value] || 'Sẵn sàng thanh toán'))

function vnd(n: number) {
  return n ? n.toLocaleString('vi-VN') + 'đ' : '0đ'
}

function buildReturnUrl() {
  return new URL('/student/payments', window.location.origin).toString()
}

async function payWithMomo() {
  if (!canPay.value || isProcessing.value) return
  status.value = 'processing'
  errorMessage.value = ''

  try {
    const response = await paymentService.createMomoPayment({
      amount: amountNumber.value,
      planName: plan.value,
      redirectUrl: buildReturnUrl(),
      orderInfo: `Thanh toán ${plan.value}`,
    })
    lastOrderId.value = response.orderId

    const target = response.payUrl || response.deeplink || response.qrCodeUrl
    if (!target) {
      throw new Error('Không nhận được payUrl từ MoMo')
    }
    window.location.href = target
  } catch (error: any) {
    status.value = 'error'
    errorMessage.value =
      error?.response?.data?.detail ||
      error?.message ||
      'Không thể tạo giao dịch. Vui lòng thử lại.'
  } finally {
    if (status.value === 'processing') {
      status.value = 'idle'
    }
  }
}
</script>

<style>
:root{
  --bg:#f6f7fb; --card:#fff; --text:#0f172a; --muted:#6b7280; --line:#e5e7eb;
  --accent:#16a34a; --focus-border:#86efac; --focus-ring:rgba(22,163,74,.18);
}
</style>

<style scoped>
.pay-page{ background:var(--bg); min-height:100vh; color:var(--text); }
.container{ max-width:1100px; margin:0 auto; padding:24px 16px 40px; }
.title{ font-size:22px; font-weight:800; margin-bottom:12px; }
.grid{ display:grid; grid-template-columns: 1.5fr 1fr; gap:16px; }
.card{ background:var(--card); border:1px solid var(--line); border-radius:14px; padding:20px; box-shadow:0 10px 30px rgba(15,23,42,.04); }

.flow-card h2{ margin:0 0 8px; font-size:20px; font-weight:800; }
.flow-card p{ margin-bottom:10px; color:var(--muted); }

.status-chip{
  display:inline-flex;
  padding:6px 12px;
  border-radius:999px;
  font-size:12px;
  font-weight:700;
  margin-bottom:12px;
}
.chip-idle{ background:#ecfdf5; color:#047857; }
.chip-processing{ background:#fef3c7; color:#b45309; }
.chip-error{ background:#fee2e2; color:#b91c1c; }

.steps{ margin:0 0 16px 18px; color:#1f2937; display:grid; gap:8px; }
.steps strong{ color:#0f172a; }

.note{
  border-radius:10px;
  padding:10px 12px;
  font-size:14px;
  margin-bottom:12px;
}
.note.success{ background:#ecfdf5; color:#0f5132; border:1px solid #bbf7d0; }
.note.error{ background:#fee2e2; color:#b91c1c; border:1px solid #fecaca; }
.note.warning{ background:#fef3c7; color:#92400e; border:1px solid #fde68a; }
.note.muted{ background:#f8fafc; color:var(--muted); border:1px solid var(--line); }
.note a{ color:#2563eb; font-weight:700; }

.btn-primary{
  width:100%;
  background:var(--accent);
  color:#fff;
  border:1px solid var(--accent);
  padding:14px 16px;
  border-radius:12px;
  font-weight:800;
  font-size:16px;
  cursor:pointer;
  display:inline-flex;
  align-items:center;
  justify-content:center;
  gap:8px;
  transition:all .2s ease;
}
.btn-primary:hover:not(:disabled){ filter:brightness(1.05); transform:translateY(-1px); }
.btn-primary:disabled{ opacity:.6; cursor:not-allowed; }

.spinner{
  width:16px;
  height:16px;
  border-radius:50%;
  border:2px solid rgba(255,255,255,.4);
  border-top-color:#fff;
  animation:spin .8s linear infinite;
}
@keyframes spin{ to { transform:rotate(360deg); } }

.summary{ display:grid; gap:10px; margin-bottom:8px; }
.line{ display:flex; justify-content:space-between; font-size:15px; color:#1f2937; }
.line b{ font-size:16px; }
.divider{ height:1px; background:var(--line); margin:6px 0; }
.total b{ color:#065f46; font-size:18px; }
.helper{ background:#f8fafc; border-radius:12px; padding:12px 14px; color:var(--muted); }
.helper ul{ margin:8px 0 0 18px; padding:0; }

.section-title{ font-size:18px; font-weight:800; margin-bottom:12px; }

@media (max-width: 960px){
  .grid{ grid-template-columns:1fr; }
}
</style>
