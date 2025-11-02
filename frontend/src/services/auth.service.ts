import http from '@/config/axios'
// src/services/auth.service.ts
export type Role = 'admin' | 'teacher' | 'student'


export interface AuthUser {
  id: number
  name: string
  email: string
  role: Role
  // các field optional để trang Profile có thể dùng
  phone?: string
  title?: string
  bio?: string
  avatar?: string
}


export interface AuthPayload {
  token: string
  user: AuthUser
}


// DTO cho cập nhật hồ sơ
export interface UpdateProfileDto extends Partial<AuthUser> {
  avatar?: string
}


export const authService = {
  async login(email: string, password: string): Promise<AuthPayload> {
    if (!email || !password) throw new Error('Thiếu thông tin đăng nhập')
    // gọi api thật
    const { data } = await http.post('/account/login/', {
      username_or_email: email,
      password,
    })


    // map về authuser
    const user: AuthUser = {
      id: Number(data.user.id),
      name: data.user.username ?? 'User',
      email: data.user.email,
      // BE chưa trả role -> tạm mặc định 'student' (sau này BE có thì sửa lại chỗ này)
      role: 'student',
    }


    localStorage.setItem('access', data.access)
    if (data.refresh) localStorage.setItem('refresh', data.refresh)


    return { token: data.access as string, user }
  },


  async loginWithGoogle(): Promise<AuthPayload> {
    return {
      token: 'mock-google-' + Date.now(),
      user: {
        id: 2,
        name: 'Google User',
        email: 'googleuser@example.com',
        role: 'student',
      },
    }
  },


  async register(payload: {
    fullName?: string
    username: string
    phone?: string
    password: string
    email?: string
    confirm?: string
    agree?: boolean
  }): Promise<{ ok: boolean }> {
    // chỉ gửi những key be nhận
    const body = {
      username: payload.username,
      password: payload.password,
      email: payload.email ?? undefined,
      phone: payload.phone ?? undefined,
    }
    await http.post('/account/register/', body)
    return { ok: true }
  },


  // Hàm phục vụ trang Profile; backend thật thì PATCH /me
  async updateProfile(payload: UpdateProfileDto): Promise<{ user: AuthUser }> {
    // mock: trả về user đã merge
    return {
      user: {
        id: 1,
        name: payload.name ?? 'User teacher',
        email: payload.email ?? 'teacher@example.com',
        role: 'teacher',
        phone: payload.phone,
        title: payload.title,
        bio: payload.bio,
        avatar: payload.avatar,
      },
    }
  },


  // [ADD] Đổi mật khẩu (mock). Backend thật: POST/PATCH /auth/change-password
  async changePassword(oldPassword: string, newPassword: string): Promise<{ ok: boolean }> {
    if (!oldPassword || !newPassword) throw new Error('Thiếu mật khẩu') // ADD
    await new Promise((r) => setTimeout(r, 400)) // ADD giả lập gọi API
    return { ok: true } // [ADD]
  },
}
