<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth.store'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)

const form = reactive({
  username: '',
  email: '',
  phone: '',
  password: '',
  confirmPassword: '',
  agree: false,
})

function isEmail(v: string) {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v.trim())
}

function validate() {
  if (!form.username.trim()) return 'Vui lòng nhập username.'
  if (!isEmail(form.email)) return 'Email không hợp lệ.'
  if (!/^\d{8,15}$/.test(form.phone.trim())) return 'Số điện thoại chỉ gồm số (8–15 ký tự).'
  if (form.password.length < 6) return 'Mật khẩu tối thiểu 6 ký tự.'
  if (form.confirmPassword !== form.password) return 'Mật khẩu nhập lại không khớp.'
  if (!form.agree) return 'Bạn cần đồng ý điều khoản để tiếp tục.'
  return null
}

async function onSubmit() {
  error.value = null
  const msg = validate()
  if (msg) {
    error.value = msg
    return
  }

  loading.value = true
  try {
    await auth.register({
      username: form.username.trim(),
      email: form.email.trim(),
      password: form.password,
      phone: form.phone.trim(),
    })

    ElMessage.success('Đăng ký thành công! Vui lòng đăng nhập.')
    router.push('/login')
  } catch (e: any) {
    const data = e?.response?.data
    error.value =
      data?.detail ||
      (typeof data === 'object' ? JSON.stringify(data) : null) ||
      e?.message ||
      'Đăng ký thất bại'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div
    class="min-h-screen flex items-center justify-center p-4 relative overflow-hidden bg-slate-50"
  >
    <!-- Decorative Bloom -->
    <div
      class="absolute top-[-20%] right-[-10%] w-[60%] h-[60%] rounded-full bg-emerald-400/20 blur-[100px] pointer-events-none"
    ></div>
    <div
      class="absolute bottom-[-20%] left-[-10%] w-[60%] h-[60%] rounded-full bg-blue-400/20 blur-[100px] pointer-events-none"
    ></div>

    <div
      class="w-full max-w-lg bg-white/80 backdrop-blur-xl border border-white/50 shadow-2xl rounded-3xl p-8 relative z-10 transition-all duration-300 hover:shadow-[0_20px_40px_rgba(0,0,0,0.12)]"
    >
      <!-- Header -->
      <div class="text-center mb-8">
        <h1 class="text-3xl font-bold text-[rgb(var(--text))]">Tạo tài khoản mới</h1>
        <p class="text-[rgb(var(--text-light))] mt-2">
          Tham gia cộng đồng học tập EduRiot ngay hôm nay
        </p>
      </div>

      <!-- Error Alert -->
      <div
        v-if="error"
        class="mb-6 p-4 rounded-xl bg-red-50 border border-red-100 text-red-600 text-sm flex items-start gap-3"
      >
        <span>⚠️</span>
        <span>{{ error }}</span>
      </div>

      <!-- Form -->
      <form @submit.prevent="onSubmit" class="space-y-4">
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-semibold text-[rgb(var(--text))] mb-1.5 ml-1"
              >Username</label
            >
            <input
              v-model="form.username"
              type="text"
              class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-[rgb(var(--secondary))] focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none text-[rgb(var(--text))] font-medium"
            />
          </div>
          <div>
            <label class="block text-sm font-semibold text-[rgb(var(--text))] mb-1.5 ml-1"
              >SĐT</label
            >
            <input
              v-model="form.phone"
              type="tel"
              class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-[rgb(var(--secondary))] focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none text-[rgb(var(--text))] font-medium"
            />
          </div>
        </div>

        <div>
          <label class="block text-sm font-semibold text-[rgb(var(--text))] mb-1.5 ml-1"
            >Email</label
          >
          <input
            v-model="form.email"
            type="email"
            class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-[rgb(var(--secondary))] focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none text-[rgb(var(--text))] font-medium"
          />
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-sm font-semibold text-[rgb(var(--text))] mb-1.5 ml-1"
              >Mật khẩu</label
            >
            <input
              v-model="form.password"
              type="password"
              placeholder="••••••••"
              class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-[rgb(var(--secondary))] focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none text-[rgb(var(--text))] font-medium"
            />
          </div>
          <div>
            <label class="block text-sm font-semibold text-[rgb(var(--text))] mb-1.5 ml-1"
              >Nhập lại MK</label
            >
            <input
              v-model="form.confirmPassword"
              type="password"
              placeholder="••••••••"
              class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-[rgb(var(--secondary))] focus:ring-4 focus:ring-emerald-500/10 transition-all outline-none text-[rgb(var(--text))] font-medium"
            />
          </div>
        </div>

        <div class="pt-2">
          <label class="flex items-center gap-3 cursor-pointer group">
            <input
              v-model="form.agree"
              type="checkbox"
              class="w-5 h-5 rounded border-gray-300 text-[rgb(var(--secondary))] focus:ring-[rgb(var(--secondary))]"
            />
            <span
              class="text-sm text-[rgb(var(--text-light))] group-hover:text-[rgb(var(--text))] transition"
            >
              Tôi đồng ý với
              <a href="#" class="text-[rgb(var(--secondary))] font-bold hover:underline"
                >Điều khoản sử dụng</a
              >
            </span>
          </label>
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3.5 rounded-xl bg-gradient-to-r from-[rgb(var(--secondary))] to-emerald-600 text-white font-bold text-lg shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/40 hover:-translate-y-0.5 active:translate-y-0 transition-all disabled:opacity-70 disabled:pointer-events-none mt-4"
        >
          <span v-if="loading" class="flex items-center justify-center gap-2">
            <span
              class="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full"
            ></span>
            Đang xử lý...
          </span>
          <span v-else>Đăng ký ngay</span>
        </button>
      </form>

      <!-- Footer -->
      <div class="mt-8 text-center text-sm text-[rgb(var(--text-light))]">
        Đã có tài khoản?
        <button
          @click="router.push('/login')"
          class="font-bold text-[rgb(var(--secondary))] hover:underline ml-1"
        >
          Đăng nhập
        </button>
      </div>
    </div>
  </div>
</template>
