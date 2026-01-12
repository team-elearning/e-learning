import { Role } from '@/shared/constants/roles'

export function homePathByRole(role: Role) {
    switch (role) {
        case Role.ADMIN:
            return '/admin/dashboard'
        case Role.TEACHER:
            return '/teacher/dashboard'
        case Role.STUDENT:
            return '/student/dashboard'
        default:
            return '/login'
    }
}
