import http from '@/shared/api/http'

export interface AdminUser {
    id: string
    username: string
    email: string
    created_on: string
    updated_on: string | null
    phone: string | null
    role: 'student' | 'instructor' | 'admin' | string
    is_active: boolean
}

export interface CreateUserDto {
    username: string
    email: string
    password?: string
    role: string
    phone?: string
    is_active?: boolean
}

export interface UpdateUserDto {
    username?: string
    email?: string
    password?: string
    role?: string
    phone?: string
    is_active?: boolean
}

export const adminUsersApi = {
    getUsers: () => http.get<AdminUser[]>('/api/account/admin/users/'),
    getUserDetail: (id: string) => http.get<AdminUser>(`/api/account/admin/users/${id}/`),
    createUser: (data: CreateUserDto) => http.post<AdminUser>('/api/account/admin/users/', data),
    updateUser: (id: string, data: UpdateUserDto) => http.patch<AdminUser>(`/api/account/admin/users/${id}/`, data),
    deleteUser: (id: string) => http.delete(`/api/account/admin/users/${id}/`),
    syncData: () => http.post('/api/account/admin/maintenance/', {}),
}
