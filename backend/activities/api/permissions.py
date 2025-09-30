from rest_framework import permissions

class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow unsafe methods only to admin users."""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Generic owner-or-admin permission.
    Must set view.lookup_object() or view.get_object() to return model instance with `student` or `owner` attribute.
    Fallback: allow if admin.
    """
    def has_object_permission(self, request, view, obj):
        if request.user and request.user.is_staff:
            return True
        # support objects with .student, .user, or .owner attribute
        owner = getattr(obj, "student", None) or getattr(obj, "user", None) or getattr(obj, "owner", None)
        if owner is None:
            return False
        return bool(owner == request.user)
