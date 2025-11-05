from rest_framework.permissions import BasePermission
from custom_account.services import user_service

class RestrictRoles(BasePermission):
    """
    Custom permission to restrict access based on user roles.
    """

    def __init__(self, allow_roles):
        self.allow_roles = allow_roles

    def has_permission(self, request, view):
        # Allow access if the user is an admin
        if not request.user or not request.user.is_authenticated:
            return False
        
        if request.user.role == 'admin':
                return True

        # Fetch user_domain from service layer
        user_domain = user_service.get_user(request.user.id)
        if not user_domain:
            return False
        
        # Check if the user's role is in the allowed roles
        return user_domain.role in self.allow_roles
    
class IsAdminOrSelf(BasePermission):
    """
    Custom permission to allow access if the user is an admin or accessing their own data.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return True
    
    def has_object_permission(self, request, view, obj):
        """
        Custom permission to allow access if the user is an admin or accessing their own data.
        """

        if request.user.is_staff:  # OR: if request.user.role == "admin":
            return True
       
       # Allow users accessing their own data
        return obj.id == request.user.id
    

class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj ở đây là instance của UserModel
        return obj.id == request.user.id

