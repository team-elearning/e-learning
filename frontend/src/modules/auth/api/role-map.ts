import { Role } from '@/shared/constants/roles'

type BackendRole = 'admin' | 'student' | 'instructor'

export function normalizeRole(role: BackendRole): Role {
    switch (role) {
        case 'admin':
            return Role.ADMIN
        case 'student':
            return Role.STUDENT
        case 'instructor':
            return Role.TEACHER
        default:
            return Role.STUDENT
    }
}
