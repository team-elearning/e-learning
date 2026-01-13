<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth.store'
import { homePathByRole } from '@/shared/utils/role-home'

const router = useRouter()
const auth = useAuthStore()

const loading = ref(false)
const error = ref<string | null>(null)
const isGoogleReady = ref(false)

const form = reactive({
  identifier: '',
  password: '',
  remember: true,
})

onMounted(() => {
  // Check if script is already loaded
  if ((window as any).google?.accounts?.oauth2) {
    isGoogleReady.value = true
    return
  }

  // Load Google Identity Services script
  const script = document.createElement('script')
  script.src = 'https://accounts.google.com/gsi/client'
  script.async = true
  script.defer = true
  script.onload = () => {
    isGoogleReady.value = true
  }
  document.head.appendChild(script)
})

function triggerGoogleLogin() {
  if (!isGoogleReady.value) {
    ElMessage.warning('Dịch vụ Google Sign-In đang khởi động. Vui lòng thử lại sau giây lát.')
    return
  }

  // @ts-ignore
  if (typeof google === 'undefined') {
    ElMessage.error('Google Sign-In chưa sẵn sàng. Vui lòng tải lại trang.')
    return
  }

  try {
    // @ts-ignore
    const client = google.accounts.oauth2.initTokenClient({
      client_id: import.meta.env.VITE_GOOGLE_CLIENT_ID,
      scope: 'email profile openid',
      callback: async (response: any) => {
        if (response.error) {
          console.error('Google Auth Error:', response)
          return
        }
        if (response.access_token) {
          performGoogleLogin(response.access_token)
        }
      },
    })
    client.requestAccessToken()
  } catch (err) {
    console.error('Failed to trigger Google Login:', err)
    ElMessage.error('Không thể khởi tạo đăng nhập Google.')
  }
}

async function performGoogleLogin(token: string) {
  loading.value = true
  error.value = null
  try {
    const role = await auth.loginWithGoogle(token)
    ElMessage.success('Đăng nhập Google thành công!')
    router.push(homePathByRole(role))
  } catch (e: any) {
    const data = e?.response?.data
    error.value =
      data?.detail ||
      (typeof data === 'object' ? JSON.stringify(data) : null) ||
      e?.message ||
      'Đăng nhập Google thất bại'
  } finally {
    loading.value = false
  }
}

async function onSubmit() {
  error.value = null
  if (!form.identifier.trim() || !form.password) {
    error.value = 'Vui lòng nhập Username/Email và mật khẩu.'
    return
  }

  loading.value = true
  try {
    const role = await auth.login(form.identifier, form.password)
    ElMessage.success('Đăng nhập thành công!')
    router.push(homePathByRole(role))
  } catch (e: any) {
    const data = e?.response?.data
    error.value =
      data?.detail ||
      (typeof data === 'object' ? JSON.stringify(data) : null) ||
      e?.message ||
      'Đăng nhập thất bại'
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
      class="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-blue-400/20 blur-[100px] pointer-events-none"
    ></div>
    <div
      class="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-purple-400/20 blur-[100px] pointer-events-none"
    ></div>

    <div
      class="w-full max-w-md bg-white/80 backdrop-blur-xl border border-white/50 shadow-2xl rounded-3xl p-8 relative z-10 transition-all duration-300 hover:shadow-[0_20px_40px_rgba(0,0,0,0.12)]"
    >
      <!-- Header -->
      <div class="text-center mb-8">
        <div
          class="h-12 w-12 bg-gradient-to-tr from-[rgb(var(--primary))] to-[rgb(var(--secondary))] rounded-xl mx-auto flex items-center justify-center shadow-lg mb-4"
        >
          <span class="text-white font-bold text-2xl"><img src="/favicon.png" alt="" /></span>
        </div>
        <h1 class="text-2xl font-bold text-[rgb(var(--text))]">Chào mừng trở lại!</h1>
        <p class="text-[rgb(var(--text-light))] mt-2 text-sm">Đăng nhập vào hệ thống EduRiot</p>
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
      <form @submit.prevent="onSubmit" class="space-y-5">
        <div>
          <label class="block text-sm font-semibold text-[rgb(var(--text))] mb-1.5 ml-1"
            >Tài khoản</label
          >
          <input
            v-model="form.identifier"
            type="text"
            placeholder="Username hoặc Email"
            class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-[rgb(var(--primary))] focus:ring-4 focus:ring-blue-500/10 transition-all outline-none text-[rgb(var(--text))] placeholder:text-slate-400 font-medium"
          />
        </div>

        <div>
          <div class="flex items-center justify-between mb-1.5 ml-1">
            <label class="block text-sm font-semibold text-[rgb(var(--text))]">Mật khẩu</label>
            <button
              type="button"
              @click="router.push('/forgot-password')"
              class="text-xs font-semibold text-[rgb(var(--primary))] hover:underline"
            >
              Quên mật khẩu?
            </button>
          </div>
          <input
            v-model="form.password"
            type="password"
            placeholder="••••••••"
            class="w-full px-4 py-3 rounded-xl bg-slate-50 border-2 border-slate-100 focus:bg-white focus:border-[rgb(var(--primary))] focus:ring-4 focus:ring-blue-500/10 transition-all outline-none text-[rgb(var(--text))] placeholder:text-slate-400 font-medium"
          />
        </div>

        <button
          type="submit"
          :disabled="loading"
          class="w-full py-3.5 rounded-xl bg-gradient-to-r from-[rgb(var(--primary))] to-blue-600 text-white font-bold text-lg shadow-lg shadow-blue-500/30 hover:shadow-blue-500/40 hover:-translate-y-0.5 active:translate-y-0 transition-all disabled:opacity-70 disabled:pointer-events-none"
        >
          <span v-if="loading" class="flex items-center justify-center gap-2">
            <span
              class="animate-spin h-5 w-5 border-2 border-white/30 border-t-white rounded-full"
            ></span>
            Đang xử lý...
          </span>
          <span v-else>Đăng nhập</span>
        </button>

        <div class="relative py-2">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-200"></div>
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-white text-gray-500">Hoặc</span>
          </div>
        </div>

        <button
          type="button"
          @click="triggerGoogleLogin"
          :disabled="loading"
          class="w-full py-3 rounded-xl bg-white border-2 border-slate-200 text-slate-700 font-bold text-lg hover:bg-slate-50 hover:border-slate-300 transition-all flex items-center justify-center gap-3 disabled:opacity-70 disabled:pointer-events-none"
        >
          <img
            src="https://www.svgrepo.com/show/475656/google-color.svg"
            class="w-6 h-6"
            alt="Google"
          />
          <span>Đăng nhập với Google</span>
        </button>
      </form>

      <!-- Footer -->
      <div class="mt-8 text-center text-sm text-[rgb(var(--text-light))]">
        Chưa có tài khoản?
        <button
          @click="router.push('/register')"
          class="font-bold text-[rgb(var(--primary))] hover:underline ml-1"
        >
          Đăng ký ngay
        </button>
      </div>
    </div>
  </div>
</template>
