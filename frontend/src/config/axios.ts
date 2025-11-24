// src/config/axios.ts
import router from "@/router";
import { useAuthStore } from "@/store/auth.store";
import axios from "axios";
import { ElMessage } from "element-plus";

const baseURL =
  import.meta.env.MODE === "development"
    ? "/api"
    : import.meta.env.VITE_API_BASE + (import.meta.env.VITE_API_PREFIX || "");

const http = axios.create({
  baseURL,
  timeout: 10000,
  headers: { "Content-Type": "application/json" },
});

/*=========================================
 ✅ Mapping error sang tiếng Việt
==========================================*/
function translateMessage(message: string): string {
  const translations: Record<string, string> = {
    "Invalid credentials": "Tài khoản hoặc mật khẩu không chính xác",
    "Invalid email or password": "Tài khoản hoặc mật khẩu không chính xác",
    "Unable to log in with provided credentials.": "Tài khoản hoặc mật khẩu không chính xác",
    "Username already taken": "Username đã tồn tại",
    "Email already taken": "Email đã tồn tại",
    "Email already exists": "Email đã tồn tại",
    "Invalid email": "Email không hợp lệ",
    "Password is too weak": "Mật khẩu quá yếu",
    "Password must be at least 6 characters": "Mật khẩu phải ít nhất 6 ký tự"
  };
  return translations[message] || message;
}

/*=========================================
 ✅ Add Token vào request
==========================================*/
http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("accessToken") || sessionStorage.getItem("accessToken");
    if (token && config.headers && !config.url?.includes("/login")) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // const origin =
    //   typeof window !== "undefined" && window.location?.origin
    //     ? window.location.origin
    //     : "";
    // const configuredBase = config.baseURL ?? http.defaults.baseURL ?? "";
    // const base = configuredBase.startsWith("http")
    //   ? configuredBase
    //   : `${origin}${configuredBase}`;
    // console.log(`[HTTP] ${config.method?.toUpperCase()} ${base}${config.url}`);

    return config;
  },
  (error) => Promise.reject(error)
);


/*=========================================
 ✅ Response Interceptor DUY NHẤT
==========================================*/
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const auth = useAuthStore();

    // 🔥 Token hết hạn → logout luôn
    if (error.response?.status === 401) {
      auth.logout();
      ElMessage.error("Phiên đăng nhập đã hết hạn, vui lòng đăng nhập lại");
      router.push("/auth/login");
      return;
    }

    // ✅ Ưu tiên lấy error từ backend
    let message =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.response?.data?.error ||
      "Có lỗi xảy ra";

    // ✅ Dịch sang tiếng Việt nếu có
    message = translateMessage(message);

    ElMessage.error(message);
    return Promise.reject(error);
  }
);

export default http;
