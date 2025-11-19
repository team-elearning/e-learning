class DomainError(Exception):
    """
    Base class cho tất cả các exception thuộc về nghiệp vụ (Domain) của dự án.
    Giúp phân biệt lỗi của Python (KeyError, IndexError) và lỗi do logic app.
    """
    pass


# =============================================================================
# 1. NHÓM LỖI KHÔNG TÌM THẤY (RESOURCE NOT FOUND)
# Thường map về HTTP 404 Not Found
# =============================================================================

class ResourceNotFound(DomainError):
    """Base class cho các lỗi không tìm thấy dữ liệu."""
    pass

class UserNotFoundError(ResourceNotFound):
    pass

class CourseNotFoundError(ResourceNotFound):
    pass

class SubjectNotFoundError(ResourceNotFound):
    pass

class ModuleNotFoundError(ResourceNotFound):
    pass

class LessonNotFoundError(ResourceNotFound):
    pass

class ContentBlockNotFoundError(ResourceNotFound): 
    pass

class ExplorationNotFoundError(ResourceNotFound):
    pass

class VersionNotFoundError(ResourceNotFound):
    pass

class LessonVersionNotFoundError(ResourceNotFound):
    pass

class StateNotFoundError(ResourceNotFound):
    pass


# =============================================================================
# 2. NHÓM LỖI LOGIC & VALIDATION (BUSINESS LOGIC ERRORS)
# Thường map về HTTP 400 Bad Request hoặc 403 Forbidden
# =============================================================================

class BusinessLogicError(DomainError):
    """Base class cho các lỗi vi phạm quy tắc nghiệp vụ."""
    pass

class DomainValidationError(BusinessLogicError):
    """Lỗi khi validate dữ liệu đầu vào không thỏa mãn logic domain."""
    pass

class InvalidOperation(BusinessLogicError):
    """Hành động không hợp lệ trong ngữ cảnh hiện tại."""
    pass

class BlockMismatchError(BusinessLogicError):
    """Lỗi khi block không khớp với loại mong đợi."""
    pass


# =============================================================================
# 3. NHÓM LỖI QUYỀN TRUY CẬP & TRẠNG THÁI (ACCESS & STATE)
# Thường map về HTTP 403 Forbidden
# =============================================================================

class AccessDeniedError(DomainError):
    """Base class cho các lỗi từ chối truy cập."""
    pass

class IncorrectPasswordError(AccessDeniedError):
    pass

class NotEnrolledError(AccessDeniedError):
    """User chưa tham gia khóa học."""
    pass

class ContentNotAvailableError(AccessDeniedError):
    """Nội dung tồn tại nhưng không khả dụng (chưa publish)."""
    pass

class NoPublishedContentError(ContentNotAvailableError):
    pass

class VersionNotPublishedError(ContentNotAvailableError):
    pass