
import http from '@/config/axios'
import { jwtDecode } from 'jwt-decode'

export type Role = 'admin' | 'teacher' | 'student'

export const getRoleFromToken = (token: string): Role | null => {
  if (!token) return null
  try {
    const raw = token.startsWith('Bearer ') ? token.slice(7) : token
    const decoded: any = jwtDecode(raw)

    const maybeRole =
      decoded.role ||
      decoded.roles ||
      decoded.user?.role ||
      (Array.isArray(decoded.roles) && decoded.roles[0]) ||
      null

    if (!maybeRole) return null

    const r = String(maybeRole).toLowerCase()
    if (r === 'admin') return 'admin'
    if (r === 'teacher') return 'teacher'
    return 'student'
  } catch (error) {
    console.error('Invalid token:', error)
    return null
  }
}

export interface AuthUser {
  id: number
  name: string
  email: string
  role: Role
  phone?: string
  title?: string
  bio?: string
  avatar?: string
}

export interface AuthPayload {
  token: string
  user: AuthUser
}

export interface UpdateProfileDto extends Partial<AuthUser> {
  avatar?: string
}

export const authService = {
  async login(emailOrUsername: string, password: string): Promise<AuthPayload> {
    if (!emailOrUsername || !password) throw new Error('Thiếu thông tin đăng nhập')

    const { data } = await http.post('/account/login/', {
      username_or_email: emailOrUsername,
      password,
    })

    const token = (data.access || data.access_token || data.token) as string
    if (!token) throw new Error('Không nhận được token từ server')

    const role = (getRoleFromToken(token) || (data.user?.role as Role) || 'student') as Role

    const user: AuthUser = {
      id: Number(data.user?.id ?? data.user_id ?? 0),
      name: data.user?.username ?? data.user?.name ?? 'User',
      email: data.user?.email ?? '',
      role,
    }

    localStorage.setItem('access', token)
    localStorage.setItem('accessToken', token)
    if (data.refresh) localStorage.setItem('refresh', data.refresh)

    return { token, user }
  },

  // Nếu backend hỗ trợ social login bằng token từ client
  async loginWithGoogle(googleToken: string): Promise<AuthPayload> {
    const { data } = await http.post('/account/social/google/', { token: googleToken })
    const token = (data.access || data.access_token || data.token) as string
    if (!token) throw new Error('Không nhận được token từ server')

    const role = (getRoleFromToken(token) || (data.user?.role as Role) || 'student') as Role
    const user: AuthUser = {
      id: Number(data.user?.id ?? 0),
      name: data.user?.username ?? data.user?.name ?? 'User',
      email: data.user?.email ?? '',
      role,
    }

    localStorage.setItem('access', token)
    localStorage.setItem('accessToken', token)
    if (data.refresh) localStorage.setItem('refresh', data.refresh)

    return { token, user }
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
    const body = {
      username: payload.username,
      password: payload.password,
      email: payload.email ?? undefined,
      phone: payload.phone ?? undefined,
    }
    await http.post('/account/register/', body)
    return { ok: true }
  },

  async updateProfile(payload: UpdateProfileDto): Promise<{ user: AuthUser }> {
    const { data } = await http.patch('/account/profile/', payload)
    // giả sử backend trả về { user: {...} } hoặc trả user trực tiếp
    const returnedUser = data.user ?? data
    const user: AuthUser = {
      id: Number(returnedUser.id ?? 0),
      name: returnedUser.username ?? returnedUser.name ?? 'User',
      email: returnedUser.email ?? '',
      role: (returnedUser.role as Role) || 'student',
      phone: returnedUser.phone,
      title: returnedUser.title,
      bio: returnedUser.bio,
      avatar: returnedUser.avatar,
    }
    return { user }
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<{ ok: boolean }> {
    if (!oldPassword || !newPassword) throw new Error('Thiếu mật khẩu')
    await http.post('/account/change-password/', {
      old_password: oldPassword,
      new_password: newPassword,
    })
    return { ok: true }
  },
}
