from celery import shared_task
from django.apps import apps

from content.models import Course
from personalization.domains.sync_result_domain import SyncResultDomain
from personalization.services.ai_recommendation_service import get_embedding
from personalization.models import CourseEmbedding



def build_course_context(course) -> str:
    """
    Tạo prompt ngữ nghĩa phong phú cho Bedrock.
    """
    tags = ", ".join([t.name for t in course.tags.all()])
    categories = ", ".join([c.name for c in course.categories.all()])
    
    # Level khóa học (nếu có trong model)
    # level = course.get_level_display() 
    
    # Prompt engineering: Cấu trúc câu giúp AI hiểu rõ đây là tài liệu giáo dục
    # Dùng tiếng Anh để Embedding model (thường train data tiếng Anh nhiều) hiểu tốt hơn
    # dù nội dung có thể là tiếng Việt.
    prompt = (
        f"Course Title: {course.title}\n"
        f"Domain/Category: {categories}\n"
        f"Key Topics/Tags: {tags}\n"
        f"Content Summary: {course.description}\n"
        f"Target Audience: Students interested in {categories} and {tags}."
    )
    
    # Cắt ngắn nếu quá dài (AWS Titan limit khoảng 8k token, text 6000 chars là an toàn)
    return prompt[:6000]


@shared_task
def sync_course_embeddings(course_id):
    """
    Xử lý embedding cho 1 khóa học
    """
    Course = apps.get_model('content', 'Course')
    CourseEmbedding = apps.get_model('content', 'CourseEmbedding')

    try:
        course = Course.objects.get(id=course_id)
        
        # 1. Tạo context
        context_text = build_course_context(course)
        
        # 2. Gọi AWS Bedrock
        vector = get_embedding(context_text)
        
        if vector:
            CourseEmbedding.objects.update_or_create(
                course=course,
                defaults={'vector': vector}
            )
            return f"Synced: {course.title}"
            
    except Course.DoesNotExist:
        return "Course not found"
    except Exception as e:
        return f"Error syncing {course_id}: {str(e)}"


@shared_task
def trigger_bulk_sync(force_update=False):
    """
    Quét DB và đẩy job vào queue.
    Hàm này trả về rất nhanh để UI không bị treo.
    """
    Course = apps.get_model('content', 'Course')
    courses = Course.objects.all()
    
    triggered_count = 0
    for course in courses:
        # Check logic force update
        has_embedding = hasattr(course, 'embedding') and course.embedding.vector is not None
        
        if force_update or not has_embedding:
            # Đẩy vào hàng đợi Celery
            sync_course_embeddings.delay(course.id)
            triggered_count += 1
            
    return f"Triggered {triggered_count} sync jobs."