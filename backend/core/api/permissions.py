from rest_framework.permissions import BasePermission

class IsInstructor(BasePermission):
    """
    Chỉ cho phép truy cập nếu user là 'instructor'.
    (Bạn hãy thay 'role' bằng trường thực tế trên UserModel của bạn)
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.is_staff:
            return True
        
        # Giả định User model của bạn có trường 'role'
        return getattr(request.user, 'role', None) == 'instructor'