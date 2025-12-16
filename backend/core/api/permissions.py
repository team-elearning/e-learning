from rest_framework.permissions import BasePermission

from core.services.access_policy import can_edit_course_content, can_view_course_content, is_quiz_owner_logic, can_access_attempt



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
    

class IsCourseOwner(BasePermission):
    """
    Dùng cho các API: Update Course, Create Module, Upload File...
    """
    def has_object_permission(self, request, view, obj):
        return can_edit_course_content(request.user, obj)
    

class CanViewCourseContent(BasePermission):
    """
    Dùng cho các API: Get Course Detail, Get Lesson, Get File...
    """
    def has_object_permission(self, request, view, obj):
        return can_view_course_content(request.user, obj, request=request)
    

class IsQuizOwner(BasePermission):
    """
    Permission chỉ cho phép Owner của Quiz (hoặc Admin/Course Owner) thao tác.
    Dùng cho: Update Quiz, Delete Quiz, Add Question, Reorder Question...
    """
    def has_object_permission(self, request, view, obj):
        return is_quiz_owner_logic(request.user, obj)
    

class IsAttemptOwner(BasePermission):
    """    
    Cho phép:
    1. Học viên (chủ sở hữu lượt thi).
    2. Giáo viên (chủ sở hữu đề thi) - để vào xem/chấm.
    """
    def has_object_permission(self, request, view, obj):
        return can_access_attempt(request.user, obj)