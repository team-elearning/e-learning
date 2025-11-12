class DomainValidationError(ValueError):
    pass

class NotFoundError(Exception):
    pass

class InvalidOperation(Exception):
    pass

class DomainError(Exception):
    pass

class CourseNotFoundError(DomainError):
    """Ném ra khi không tìm thấy course."""
    pass

class SubjectNotFoundError(DomainError):
    """Ném ra khi không tìm thấy subject."""
    pass

class LessonNotFoundError(DomainError):
    """Ném ra khi không tìm thấy lesson."""
    pass

class ModuleNotFoundError(DomainError):
    """Ném ra khi không tìm thấy module."""
    pass

class ValidationError(DomainError):
    """Ném ra khi có lỗi validation trong domain logic."""
    pass

class VersionNotFoundError(DomainError):
    pass

class NotEnrolledError(DomainError):
    pass

class NoPublishedContentError(DomainError):
    pass