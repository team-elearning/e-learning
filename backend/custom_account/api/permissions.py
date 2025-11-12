from rest_framework.permissions import BasePermission, SAFE_METHODS
from custom_account.services import user_service

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow read-only access to any user, but only allow write access to admin users.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and request.user.is_staff

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

class IsOwnerOrAdmin(BasePermission):
    """
    Custom permission to only allow owners of an object or admin users to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in SAFE_METHODS:
            return True

        # For objects that don't have an owner (like a Module, which belongs to a Course),
        # we might need to check the owner of the parent object.
        # The view should handle passing the correct object (e.g., the course) to check.
        # This default implementation assumes `obj` has an `owner` attribute.
        
        owner_attr = getattr(obj, 'owner', None)

        # If the object itself doesn't have an owner, deny access for safety,
        # unless the user is an admin.
        if owner_attr is None:
            return request.user.is_staff

        return owner_attr == request.user or request.user.is_staff