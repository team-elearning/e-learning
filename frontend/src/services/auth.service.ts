//frontend/src/services/auth.service.ts


import http from '@/config/axios'
import { jwtDecode } from 'jwt-decode'

export type Role = 'admin' | 'instructor' | 'student'

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
    if (r === 'instructor') return 'instructor'
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
  displayName?: string | null
  avatarUrl?: string | null
  dob?: string | null
  gender?: string | null
  language?: string | null
  metadata?: Record<string, any>
}

export interface AuthPayload {
  token: string
  user: AuthUser
}

export interface UpdateProfileDto extends Partial<AuthUser> {
  avatar?: string
}

function mapAuthUser(raw: any): AuthUser {
  const displayName =
    raw?.display_name ?? raw?.displayName ?? raw?.name ?? raw?.username ?? raw?.full_name ?? ''
  const avatarUrl =
    raw?.avatar_url ??
    raw?.avatarUrl ??
    raw?.avatar_id ?? // backend có thể trả avatar_id dạng data URI
    raw?.avatar ??
    ''
  const role = (raw?.role as Role) || 'student'

  return {
    id: Number(raw?.id ?? raw?.user_id ?? 0),
    name: displayName || raw?.username || raw?.name || 'User',
    displayName: displayName || raw?.username || raw?.name || 'User',
    email: raw?.email ?? '',
    role,
    phone: raw?.phone,
    title: raw?.title,
    bio: raw?.bio,
    avatar: avatarUrl || raw?.avatar || '',
    avatarUrl: avatarUrl || raw?.avatar || '',
    dob: raw?.dob ?? raw?.date_of_birth ?? raw?.birth_date ?? null,
    gender: raw?.gender ?? raw?.sex ?? null,
    language: raw?.language ?? null,
    metadata: raw?.metadata ?? {},
  }
}

function buildProfilePayload(payload: UpdateProfileDto) {
  const body: Record<string, any> = { ...payload }

  if (payload.displayName !== undefined) {
    body.display_name = payload.displayName
    body.name = payload.displayName
  }
  if (payload.avatarUrl !== undefined) {
    body.avatar_url = payload.avatarUrl
  }
  if (payload.avatar !== undefined && body.avatar_url === undefined) {
    body.avatar_url = payload.avatar
  }
  if (payload.dob !== undefined) body.dob = payload.dob
  if (payload.gender !== undefined) body.gender = payload.gender
  if (payload.language !== undefined) body.language = payload.language

  return body
}

export const authService = {
  async login(identifier: string, password: string): Promise<AuthPayload> {
    if (!identifier || !password) throw new Error('Thiếu thông tin đăng nhập')

    // xác định là email hay username
    const isEmail = /\S+@\S+\.\S+/.test(identifier)
    const body = isEmail
      ? { email: identifier, password }
      : { username: identifier, password }

    const { data } = await http.post('/account/login/', body)

    const token = (data.access || data.access_token || data.token) as string
    if (!token) throw new Error('Không nhận được token từ server')

    const role = (getRoleFromToken(token) || (data.user?.role as Role) || 'student') as Role

    const user = {
      ...mapAuthUser({ ...data.user, id: data.user?.id ?? data.user_id }),
      role,
    }

    localStorage.setItem('access', token)
    localStorage.setItem('accessToken', token)
    if (data.refresh) localStorage.setItem('refresh', data.refresh)

    return { token, user }
  },

  // Nếu backend hỗ trợ social login bằng token từ client
  // async loginWithGoogle(googleToken: string): Promise<AuthPayload> {
  //   const { data } = await http.post('/account/social/google/', { token: googleToken })
  //   const token = (data.access || data.access_token || data.token) as string
  //   if (!token) throw new Error('Không nhận được token từ server')

  //   const role = (getRoleFromToken(token) || (data.user?.role as Role) || 'student') as Role
  //   const user: AuthUser = {
  //     id: Number(data.user?.id ?? 0),
  //     name: data.user?.username ?? data.user?.name ?? 'User',
  //     email: data.user?.email ?? '',
  //     role,
  //   }

  //   localStorage.setItem('access', token)
  //   localStorage.setItem('accessToken', token)
  //   if (data.refresh) localStorage.setItem('refresh', data.refresh)

  //   return { token, user }
  // },

  async register(payload: {
    username: string
    email: string
    phone: string
    password: string
  }): Promise<{ ok: boolean }> {
    const body = {
      username: payload.username,
      email: payload.email,
      password: payload.password,
      phone: payload.phone,
    }

    await http.post('/account/register/', body)

    return { ok: true }
  },


  async updateProfile(payload: UpdateProfileDto): Promise<{ user: AuthUser }> {
    const { data } = await http.patch('/account/profile/', buildProfilePayload(payload))
    const returnedUser = data.user ?? data
    const user = mapAuthUser(returnedUser)
    return { user }
  },

  async getProfile(): Promise<AuthUser> {
    const { data } = await http.get('/account/profile/')
    const returnedUser = data.user ?? data
    return mapAuthUser(returnedUser)
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<{ ok: boolean }> {
    if (!oldPassword || !newPassword) throw new Error('Thiếu mật khẩu')
    await http.post('/account/password/change/', {
      old_password: oldPassword,
      new_password: newPassword,
    })
    return { ok: true }
  },

  async forgotPassword(email: string): Promise<{ ok: boolean }> {
    if (!email) throw new Error('Thiếu email')
    await http.post('/account/password/reset/', { email })
    return { ok: true }
  },

  async resetPassword(uid: string, token: string, newPassword: string): Promise<{ ok: boolean }> {
    if (!uid || !token || !newPassword) throw new Error('Thiếu thông tin đặt lại mật khẩu')
    await http.post(`/account/password/reset/confirm/${uid}/${token}/`, {
      new_password: newPassword,
    })
    return { ok: true }
  },
}
