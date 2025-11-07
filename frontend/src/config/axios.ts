// src/config/axios.ts
import router from '@/router'
import { useAuthStore } from '@/store/auth.store'
import axios from 'axios'
import { ElMessage } from 'element-plus'


const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
  headers: { 'Content-Type': 'application/json' }
})

// http.interceptors.response.use(
//   (response) => {
//     console.log('Response Data:', response.data)
//     return response
//   },
//   (error) => Promise.reject(error)
// )
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const auth = useAuthStore()

    // ====== AUTO LOGOUT WHEN TOKEN EXPIRED ======
    if (error.response?.status === 401) {
      auth.logout()
      ElMessage.error("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại")
      router.push('/auth/login')
      return Promise.reject(error)
    }

    // ====== HANDLE BACKEND ERROR MESSAGE ======
    let message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.response?.data?.error ||
      'Có lỗi xảy ra'

    return Promise.reject(new Error(message))
  }
)
/*=============backend có phần nào sửa lại như này nhé để fortend dịch=========*/
function translateMessage(message: string): string {
  const translations: Record<string, string> = {
    // Login errors
    'Invalid credentials': 'Tài khoản hoặc mật khẩu không chính xác',
    'Invalid email or password': 'Tài khoản hoặc mật khẩu không chính xác',
    'Email not found': 'Tài khoản không tồn tại',
    'User not found': 'Tài khoản không tồn tại',

    // Register errors
    'Username already taken': 'Username đã tồn tại',
    'Email already taken': 'Email đã tồn tại',
    'Email already exists': 'Email đã tồn tại',
    'Invalid email': 'Email không hợp lệ',
    'Password is too weak': 'Mật khẩu quá yếu',
    'Password must be at least 6 characters': 'Mật khẩu phải ít nhất 6 ký tự',
  }
  return translations[message] || message
}

// Interceptor để thêm token vào tất cả các request
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken') || sessionStorage.getItem('accessToken')
    // Bỏ qua thêm token nếu là login hoặc register
    if (config.url && !config.url.includes('/login') && !config.url.includes('/register')) {
      if (token && config.headers) {
        config.headers.Authorization = `Bearer ${token}` // Thêm token vào header Authorization
      }
    }
    return config
  },
  (error) => Promise.reject(error)
)

http.interceptors.response.use(
  (response) => response,
  (error: any) => {
    let message = 'Có lỗi xảy ra'

    if (error.response) {
      //Lấy message từ backend trước
      if (error.response.data?.message) {
        message = error.response.data.message
      } else if (error.response.data?.error) {
        message = error.response.data.error
      } else if (error.response.data?.detail) {
        message = error.response.data.detail
      } else {
        // Default message theo status
        if (error.response.status === 401) {
          message = 'Yêu cầu không hợp lệ'
        } else if (error.response.status === 400) {
          message = 'Tài khoản hoặc mật khẩu không chính xác'
        } else if (error.response.status === 500) {
          message = 'Lỗi máy chủ'
        }
      }

      message = translateMessage(message)
    } else if (!error.response) {
      message = 'Lỗi kết nối. Kiểm tra internet'
    }

    error.customMessage = translateMessage(message)
    return Promise.reject(error)
  }
)

export default http
