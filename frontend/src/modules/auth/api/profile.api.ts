import http from '@/shared/api/http'

export interface UserProfile {
    username: string
    email: string
    role: string
    phone: string | null
    display_name: string | null
    avatar_id: string | null
    dob: string | null
    gender: 'male' | 'female' | 'other' | null
    language: string | null
    metadata: any
    created_at: string
}

export interface UpdateProfileBody {
    phone?: string
    display_name?: string
    dob?: string
    gender?: 'male' | 'female' | 'other'
    language?: string
}

export const profileApi = {
    getProfile() {
        return http.get<UserProfile>('/api/account/profile/')
    },
    updateProfile(data: UpdateProfileBody) {
        return http.patch<UserProfile>('/api/account/profile/', data)
    }
}
