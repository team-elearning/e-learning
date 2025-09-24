<template>
  <div class="page">
    <div class="container">
      <h1 class="title">Giỏ hàng</h1>

      <div v-if="items.length" class="card">
        <table class="table">
          <thead>
            <tr>
              <th>Khoá học</th>
              <th class="right">Giá</th>
              <th class="center">Hành động</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="it in items" :key="it.id">
              <td>{{ it.name }}</td>
              <td class="right">{{ vnd(it.price) }}</td>
              <td class="center">
                <button class="btn-light sm" @click="remove(it.id)">Xoá</button>
              </td>
            </tr>
          </tbody>
          <tfoot>
            <tr>
              <td><b>Tổng cộng</b></td>
              <td class="right"><b>{{ vnd(total) }}</b></td>
              <td></td>
            </tr>
          </tfoot>
        </table>

        <div class="actions">
          <button class="btn-primary" :disabled="!items.length" @click="goCheckout">
            Thanh toán
          </button>
        </div>
      </div>

      <div v-else class="empty card">
        Giỏ hàng trống.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// Demo data - thay bằng dữ liệu thật của bạn
const items = reactive([
  { id: 1, name: 'Khoá học Standard', price: 199000 },
  // { id: 2, name: 'Khoá học Pro', price: 299000 },
])

const total = computed(() => items.reduce((s, i) => s + i.price, 0))
function vnd(n: number) { return n.toLocaleString('vi-VN') + 'đ' }

function remove(id: number) {
  const idx = items.findIndex(i => i.id === id)
  if (idx >= 0) items.splice(idx, 1)
}

function goCheckout() {
  router.push({
    name: 'student-payments-checkout',
    query: { amount: String(total.value), plan: items[0]?.name || 'Thanh toán' }
  })
}
</script>

<style scoped>
:root{ --accent:#16a34a; --line:#e5e7eb; --muted:#6b7280; }
.page{ background:#f6f7fb; min-height:100vh; }
.container{ max-width:1000px; margin:0 auto; padding:24px 16px 40px; }
.title{ font-size:22px; font-weight:800; margin-bottom:12px; }

.card{ background:#fff; border:1px solid var(--line); border-radius:14px; padding:16px; }
.table{ width:100%; border-collapse:collapse; }
th,td{ padding:10px; border-bottom:1px solid var(--line); }
tfoot td{ border-bottom:0; }
.right{ text-align:right; }
.center{ text-align:center; }

.actions{ display:flex; justify-content:flex-end; margin-top:12px; gap:8px; }
.btn-primary{ background:var(--accent); color:#fff; border:1px solid var(--accent); padding:10px 14px; border-radius:10px; font-weight:800; cursor:pointer; }
.btn-light{ background:#fff; border:1px solid var(--line); border-radius:10px; padding:8px 12px; cursor:pointer; font-weight:700; }
.btn-light.sm{ padding:6px 10px; }
.empty{ color:var(--muted); }
</style>
