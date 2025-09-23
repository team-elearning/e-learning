
from account.models import UserModel
from classroom.models import ClassroomModel, MembershipModel



class ServiceError(Exception):
    pass

class ConflictError(ServiceError):
    pass

class NotFoundError(ServiceError):
    pass

class PermissionDenied(ServiceError):
    pass

class InvalidOperation(ServiceError):
    pass


def ensure_is_admin_or_instructor(requesting: UserModel, classroom: ClassroomModel) -> None:
    if requesting.is_staff:
        return
    # instructor if user id matches any active instructor membership
    is_instructor = MembershipModel.objects.filter(classroom=classroom, 
                                                   student_id=requesting.id, 
                                                   role_exact="instructor", 
                                                   is_active=True).exists()
    if not is_instructor:
        raise PermissionDenied("Requires instructor or admin privileges.")


def ensure_is_admin(requesting: UserModel) -> None:
    if not requesting.is_staff:
        raise PermissionDenied("Admin privileges required.")