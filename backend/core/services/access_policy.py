from django.utils import timezone

from content.models import Course, Enrollment, Quiz
from quiz.models import QuizAttempt, Question



# ==========================================
# HELPER 
# ==========================================

def _resolve_course(obj):
    """
    Helper function: Tìm Course cha từ bất kỳ object con nào (Module, Lesson, Block, File...).
    Mô phỏng tư duy 'Context' của Moodle.
    """
    if obj is None:
        return None
    if isinstance(obj, Course):
        return obj
    
    if hasattr(obj, 'course'): # Module, Enrollment...
        return obj.course
    if hasattr(obj, 'module') and hasattr(obj.module, 'course'): # Lesson
        return obj.module.course
    if hasattr(obj, 'lesson') and hasattr(obj.lesson, 'module'): # ContentBlock
        return obj.lesson.module.course
    # # Nếu là File/UploadedFile, cần check content_object (logic cũ của bạn)
    # if hasattr(obj, 'content_object'): 
    #     return _resolve_course(obj.content_object)
    
    return None


def _check_quiz_access(user, quiz_obj):
        """
        Kiểm tra user có đủ điều kiện làm bài Quiz không.
        Check: Thời gian mở/đóng, Số lần làm bài (Attempts).
        Không check Enrollment ở đây (Enrollment check ở tầng Course rồi).
        """
        # 1. Admin/Giảng viên sở hữu -> Luôn OK (để họ còn test bài)
        if user.is_staff or user.is_superuser:
            return True
        if quiz_obj.owner == user:
            return True

        now = timezone.now()

        # 2. Check thời gian Mở (Time Open)
        if quiz_obj.time_open and now < quiz_obj.time_open:
            # Chưa đến giờ mở
            return False

        # 3. Check thời gian Đóng (Deadline)
        if quiz_obj.time_close and now > quiz_obj.time_close:
            # Đã hết hạn
            # Tùy nghiệp vụ: Nếu hết hạn nhưng user muốn xem lại bài đã làm thì OK.
            # Nhưng nếu muốn "Start" bài mới thì False. 
            # Ở đây ta chặn access nói chung để bảo mật đề thi.
            return False

        # 4. Check chế độ Ôn luyện (Practice)
        # Nếu là practice thì thường cho làm thoải mái, bỏ qua check số lần
        if quiz_obj.mode == 'practice':
            return True

        # 5. Check số lần làm bài (Max Attempts) cho chế độ Exam
        if quiz_obj.max_attempts is not None:
            # Đếm số lần user đã làm (QuizAttempt)
            # Giả sử bạn có model QuizAttempt
            attempt_count = QuizAttempt.objects.filter(
                user=user, 
                quiz=quiz_obj
            ).count()
            
            if attempt_count >= quiz_obj.max_attempts:
                return False # Hết lượt làm bài

        return True


# ==========================================
# SERVICE 
# ==========================================

def is_course_owner(user, obj):
    course = _resolve_course(obj)
    if not course or not user.is_authenticated:
        return False
    return course.owner == user


def is_enrolled(user, obj):
    course = _resolve_course(obj)
    if not course or not user.is_authenticated:
        return False
    return Enrollment.objects.filter(user=user, course=course).exists()


def can_view_course_content(user, obj):
    """
    Quyền xem nội dung (Module, Lesson, Video, File...).
    Logic: Admin > Owner > Public Course > Enrolled Student
    """
    # 1. Admin/Staff luôn có quyền
    if user.is_staff or user.is_superuser:
        return True

    course = _resolve_course(obj)
    if not course:
        return False

    # 2. Owner (Giảng viên)
    if course.owner == user:
        return True

    # 3. Public Course (nếu có logic xem thử)
    if getattr(course, 'published', False) or getattr(course, 'is_public', False):
        return True

    # 4. Học viên đã ghi danh
    if is_enrolled(user, course):
        return True
        
    return False


def can_edit_course_content(user, obj):
    """
    Chỉ cho phép Owner hoặc Admin sửa đổi.
    """
    if user.is_staff or user.is_superuser:
        return True
    return is_course_owner(user, obj)


def can_access_file(user, file_object):
    """
    Logic check file phức tạp của bạn được đưa vào đây.
    """
    # Logic Public (Avatar, Logo...)
    PUBLIC_COMPONENTS = {'course_thumbnail', 'user_avatar', 'site_logo'}
    if file_object.component in PUBLIC_COMPONENTS:
        return True

    # Nếu file thuộc về Quiz (logic riêng)
    related_object = file_object.content_object
    if hasattr(related_object, 'quiz') or isinstance(related_object, Quiz):
        # Gọi lại logic check quiz (có thể refactor vào đây luôn nếu muốn)
        return _check_quiz_access(user, related_object)

    # Với các file bài giảng thông thường, quy về quyền xem Course
    return can_view_course_content(user, related_object)


def is_quiz_owner_logic(user, obj):
    """
    Logic check quyền sở hữu Quiz (Standalone Mode).
    """
    if not user.is_authenticated:
        return False
        
    # 1. Admin/Superuser
    if user.is_staff or user.is_superuser:
        return True

    # 2. Check Owner trực tiếp (Nếu Quiz model có field owner)
    # Áp dụng cho cả Quiz và Question (Question.quiz.owner)
    quiz_obj = obj
    if isinstance(obj, Question):
        quiz_obj = obj.quiz
    
    if hasattr(quiz_obj, 'owner') and quiz_obj.owner == user:
        return True

    return False
