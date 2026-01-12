import http from '@/shared/api/http'

export interface RegisterBody {
    username: string
    email: string
    password: string
    phone: string
}

export async function registerApi(payload: RegisterBody) {
    const { data } = await http.post('/api/account/register/', payload)
    return data
}
