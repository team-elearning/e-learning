<template>
  <div class="pay-page">
    <div class="container">
      <h1 class="title">Thanh toán</h1>

      <div class="grid">
        <!-- QR + form -->
        <section class="card qr-card">
          <div class="qr-left">
            <div class="qr-wrap">
              <img :src="qrUrl" alt="VietQR" />
            </div>

            <div class="qr-actions">
              <button class="btn-outline" @click="downloadQR">Tải QR</button>
              <button class="btn-light" @click="refreshOrder">Tạo mã mới</button>
              <div class="muted small">Hết hạn trong: <b>{{ mm }}:{{ ss }}</b></div>
            </div>
          </div>

          <div class="qr-right">
            <h2 class="section-title">Quét QR để thanh toán</h2>
            <ol class="steps">
              <li>Mở App ngân hàng có hỗ trợ <b>VietQR/NAPAS 247</b>.</li>
              <li>Chọn mục <b>Quét QR</b> và quét mã bên trái.</li>
              <li>Kiểm tra thông tin khớp 100% rồi xác nhận thanh toán.</li>
            </ol>

            <div class="note success" v-if="copied">Đã sao chép: {{ copied }}</div>

            <div class="field">
              <span class="label">Ngân hàng</span>
              <select v-model="bank" class="input select">
                <option v-for="b in banks" :key="b.code" :value="b.code">{{ b.name }}</option>
              </select>
            </div>

            <div class="row-2">
              <div class="field">
                <span class="label">Số tài khoản</span>
                <div class="copy-line">
                  <input v-model="account" class="input" />
                  <button class="copy" @click="copy(account)">Copy</button>
                </div>
              </div>

              <div class="field">
                <span class="label">Chủ tài khoản</span>
                <input v-model="accountName" class="input" />
              </div>
            </div>

            <!-- Nội dung CK -->
            <div class="field">
              <span class="label">Nội dung chuyển khoản</span>
              <div class="copy-line">
                <input v-model="orderNote" class="input" />
                <button class="copy" @click="copy(orderNote)">Copy</button>
              </div>
              <small class="muted">Vui lòng giữ nguyên đúng nội dung để tự động đối soát.</small>
            </div>

            <!-- Số tiền -->
            <div class="field">
              <span class="label">Số tiền (VND)</span>
              <input
                v-model="amountText"
                @input="onAmountInput"
                class="input right"
                inputmode="numeric"
                placeholder="Nhập số tiền, ví dụ 215000"
              />
              <small class="muted">Chỉ nhập chữ số.</small>
            </div>

            <div class="actions">
              <button 
                class="btn-primary" 
                :class="{ 'is-busy': justMarked }"
                @click="markPaid"
              >
                <span v-if="justMarked" class="spinner"></span>
                {{ justMarked ? 'Đang xử lý...' : 'Tôi đã thanh toán' }}
              </button>
            </div>
            <span class="muted confirm-note" v-if="justMarked">
              ✓ Đã ghi nhận. Hệ thống sẽ kích hoạt ngay sau khi đối soát.
            </span>
          </div>
        </section>

        <!-- Tóm tắt -->
        <section class="card">
          <h2 class="section-title">Tóm tắt</h2>
          <div class="summary">
            <div class="line"><span>Gói</span><b>{{ plan }}</b></div>
            <div class="line"><span>Thành tiền</span><b>{{ vnd(amountNumber) }}</b></div>
            <div class="line"><span>Phí</span><b>0đ</b></div>
            <div class="divider"></div>
            <div class="line total"><span>Tổng thanh toán</span><b>{{ vnd(amountNumber) }}</b></div>
          </div>
        </section>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()

/** ==== Config (đổi lại cho đúng) ==== */
const banks = [
  { code: 'vcb', name: 'Vietcombank' },
  { code: 'mbbank', name: 'MBBank' },
  { code: 'tcb', name: 'Techcombank' },
  { code: 'bidv', name: 'BIDV' },
  { code: 'vtb', name: 'VietinBank' },
  { code: 'acb', name: 'ACB' },
  { code: 'tpb', name: 'TPBank' },
  { code: 'vpbank', name: 'VPBank' },
  { code: 'agribank', name: 'Agribank' },
]

const bank = ref('mbbank')
const account = ref('0966148388')
const accountName = ref('Vu Le Kien')

/** Đọc amount & plan từ query (nếu không có → mặc định) */
const plan = ref(String(route.query.plan || 'Khoá học Standard'))
const amountText = ref(String(route.query.amount || '199000'))

const amountNumber = computed(() => {
  const digits = amountText.value.replace(/[^\d]/g, '')
  return digits ? parseInt(digits, 10) : 0
})
function onAmountInput(){ amountText.value = amountText.value.replace(/[^\d]/g,'') }

const orderId = ref(createOrderId())
const orderNote = ref(`HOCVIEN-${orderId.value}`)

/** URL ảnh QR */
const qrUrl = computed(() => {
  const p = new URLSearchParams({
    amount: String(amountNumber.value || 0),
    addInfo: orderNote.value,
    accountName: accountName.value,
  })
  return `https://img.vietqr.io/image/${bank.value}-${account.value}-qr_only.png?${p.toString()}`
})

/** Helpers */
function vnd(n:number){ return n.toLocaleString('vi-VN') + 'đ' }
function createOrderId(){
  const t = new Date()
  return t.getFullYear().toString().slice(-2)
    + String(t.getMonth()+1).padStart(2,'0')
    + String(t.getDate()).padStart(2,'0')
    + '-' + Math.random().toString(36).slice(2,7).toUpperCase()
}

/** Copy */
const copied = ref('')
async function copy(text:string){
  try{ await navigator.clipboard.writeText(text); copied.value = text; setTimeout(()=>copied.value='',1500) }catch{}
}

/** Countdown 10 phút */
const seconds = ref(600)
let timer:any
onMounted(()=>{ timer=setInterval(()=>{ if(seconds.value>0) seconds.value-- },1000) })
onBeforeUnmount(()=>clearInterval(timer))
const mm = computed(()=> String(Math.floor(seconds.value/60)).padStart(2,'0'))
const ss = computed(()=> String(seconds.value%60).padStart(2,'0'))
function refreshOrder(){ orderId.value=createOrderId(); orderNote.value=`HOCVIEN-${orderId.value}`; seconds.value=600 }

/** Download QR */
async function downloadQR(){
  try{
    const res = await fetch(qrUrl.value, { mode:'cors' })
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = `vietqr-${orderId.value}.png`
    document.body.appendChild(a); a.click(); a.remove()
    URL.revokeObjectURL(url)
  }catch{ window.open(qrUrl.value,'_blank') }
}

/** Mock */
const justMarked = ref(false)
function markPaid(){ justMarked.value=true; setTimeout(()=>justMarked.value=false,3000) }
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

.grid{ display:grid; grid-template-columns: 2fr 1fr; gap:16px; }
.card{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px; }

/* Left card */
.qr-card{ display:grid; grid-template-columns: 320px 1fr; gap:16px; }
.qr-wrap{ width:100%; aspect-ratio:1/1; border:1px dashed var(--line); border-radius:14px; display:grid; place-items:center; overflow:hidden; }
.qr-wrap img{ width:100%; height:100%; object-fit:contain; }
.qr-actions{ display:flex; flex-direction:column; gap:8px; align-items:flex-start; margin-top:10px; }
.small{ font-size:12px; }
.muted{ color:var(--muted); }
.section-title{ font-size:16px; font-weight:800; margin-bottom:8px; }
.steps{ margin:0 0 8px; padding-left:18px; }
.steps li{ margin:6px 0; }
.note.success{ background:#f0fdf4; color:#166534; border:1px solid #bbf7d0; padding:8px 10px; border-radius:10px; margin-bottom:10px; }

/* Fields */
.field{ display:grid; gap:6px; margin-bottom:10px; }
.label{ font-size:12px; color:var(--muted); }
.input{ width:100%; padding:10px 12px; border:1px solid var(--line); border-radius:10px; outline:none; transition: all 0.2s ease; }
.input.right{ text-align:right; }
.input:focus{ border-color:var(--focus-border); box-shadow:0 0 0 3px var(--focus-ring); }
.select{ appearance:none; background-image: linear-gradient(45deg, transparent 50%, #9ca3af 50%), linear-gradient(135deg, #9ca3af 50%, transparent 50%); background-position: calc(100% - 18px) calc(1em + 2px), calc(100% - 13px) calc(1em + 2px); background-size: 5px 5px, 5px 5px; background-repeat:no-repeat; }

.row-2{ display:grid; grid-template-columns: 1fr 1fr; gap:12px; }

/* Copy line */
.copy-line{ position:relative; }
.copy-line .input{ padding-right: 96px; }
.copy{ position:absolute; right:6px; top:50%; transform:translateY(-50%); border:1px solid var(--line); padding:6px 10px; background:#fff; border-radius:8px; cursor:pointer; font-weight:700; transition: all 0.2s ease; }
.copy:hover{ background:#f9fafb; }

/* ===========================
   BUTTONS - DÙNG !IMPORTANT
   =========================== */
.btn-primary{
  background: var(--accent) !important;
  color: #fff !important;
  border: 1px solid var(--accent) !important;
  padding: 12px 16px !important;
  border-radius: 10px !important;
  font-weight: 800 !important;
  cursor: pointer !important;
  display: inline-flex !important;
  align-items: center !important;
  gap: 8px !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
  justify-content: center !important;
}

.btn-primary:hover{ 
  filter: brightness(1.1) !important;
  transform: translateY(-1px) !important;
}

.btn-primary.is-busy{
  opacity: .7 !important;
  cursor: progress !important;
}

.btn-outline, .btn-light{ 
  background:#fff !important; 
  border:1px solid var(--line) !important; 
  border-radius:10px !important; 
  padding:8px 12px !important; 
  cursor:pointer !important; 
  font-weight:700 !important;
  transition: all 0.2s ease !important;
  width: 100% !important;
}
.btn-outline:hover, .btn-light:hover{ 
  background:#f9fafb !important; 
}

.actions{ display:flex; flex-direction:column; gap:8px; margin-top:12px; }
.confirm-note{ 
  font-size:13px; 
  color:#166534; 
  font-weight:600; 
  text-align:center;
  display:block;
  padding:6px;
}

/* Spinner */
.spinner{ 
  width:16px !important; 
  height:16px !important; 
  border:2px solid rgba(255,255,255,.6) !important; 
  border-top-color:#fff !important; 
  border-radius:50% !important; 
  animation:spin .8s linear infinite !important; 
}
@keyframes spin{ to{ transform:rotate(360deg); } }

/* Summary */
.summary{ display:grid; gap:8px; }
.line{ display:flex; justify-content:space-between; }
.divider{ height:1px; background:var(--line); margin:6px 0; }
.total b{ color:#065f46; }

@media (max-width: 980px){
  .grid{ grid-template-columns: 1fr; }
  .qr-card{ grid-template-columns: 1fr; }
}
</style>
