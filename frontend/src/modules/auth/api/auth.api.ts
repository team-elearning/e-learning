import http from '@/shared/api/http'

type BackendRole = 'admin' | 'student' | 'instructor'

export interface LoginResponse {
    access: string
    refresh: string
    user: {
        username: string
        email: string
        role: BackendRole
        full_name: string
    }
}

function isEmail(input: string) {
    const v = input.trim()
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(v)
}

export async function loginApi(identifier: string, password: string) {
    const id = identifier.trim()
    const payload = isEmail(id)
        ? { email: id, password }
        : { username: id, password }

    const { data } = await http.post<LoginResponse>('/api/account/login/', payload)
    return data
}

export async function googleLoginApi(accessToken: string) {
    const { data } = await http.post<LoginResponse>('/api/auth/google/', { access_token: accessToken })
    return data
}

export async function requestPasswordReset(email: string) {
    return http.post('/api/account/password/reset/', { email })
}

export async function confirmPasswordReset(uid: string, token: string, newPassword1: string, newPassword2: string) {
    const url = `/api/account/password/reset/confirm/${uid}/${token}/`
    return http.post(url, { new_password1: newPassword1, new_password2: newPassword2 })
}

export async function changePasswordApi(oldPassword: string, newPassword: string) {
    return http.post('/api/account/password/change/', {
        old_password: oldPassword,
        new_password: newPassword
    })
}

console.log('VITE_API_BASE_URL =', import.meta.env.VITE_API_BASE_URL)
