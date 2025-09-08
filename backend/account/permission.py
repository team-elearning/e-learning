from rest_framework import permissions
from .services import user_services

class RestrictRoles(permissions.BasePermission):
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
        user_domain = user_services.get_user(request.user.id)
        if not user_domain:
            return False
        
        # Check if the user's role is in the allowed roles
        return user_domain.role in self.allow_roles
