import os
import boto3
import json
import numpy as np
from dotenv import load_dotenv
from django.conf import settings
from django.db import models
from openai import OpenAI
from sentence_transformers import SentenceTransformer

from content.models import Course, Enrollment
from content.domains.course_domain import CourseDomain
from content.types import CourseFetchStrategy
from personalization.models import CourseEmbedding
from personalization.domains.sync_result_domain import SyncResultDomain



# load_dotenv()

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# # Khởi tạo Client (Nên để API Key trong .env)
# client = OpenAI(api_key=OPENAI_API_KEY)

# @staticmethod
# def get_embedding(text):
#     """Gọi OpenAI để biến Text thành Vector"""
#     text = text.replace("\n", " ")
#     try:
#         response = client.embeddings.create(input=[text], model="text-embedding-3-small")
#         return response.data[0].embedding
#     except Exception as e:
#         print(f"Lỗi OpenAI: {e}")
#         return []

# _model_instance = None

# def get_model():
#     """
#     Singleton Pattern: Chỉ load model 1 lần duy nhất khi cần dùng.
#     """
#     global _model_instance
#     if _model_instance is None:
#         print("⏳ Đang tải Model AI vào RAM... (Chỉ chạy lần đầu)")
#         _model_instance = SentenceTransformer('all-MiniLM-L6-v2')
#         print("✅ Đã tải xong Model!")
#     return _model_instance

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime', 
    region_name='us-east-1',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
)

def get_embedding(text: str):
    text = text[:6000] 
    body = json.dumps({"inputText": text})
    
    try:
        response = bedrock_runtime.invoke_model(
            body=body,
            modelId='amazon.titan-embed-text-v1',
            accept='application/json',
            contentType='application/json'
        )
        response_body = json.loads(response.get('body').read())
        return response_body.get('embedding')
    except Exception as e:
        print(f"🔴 Lỗi AWS Bedrock: {e}")
        return []


def sync_course_embeddings(force_update=False) -> SyncResultDomain:
    """
    Quét toàn bộ khóa học, cái nào chưa có vector thì tạo.
    Hàm này có thể chạy định kỳ hoặc chạy tay.
    """
    courses = Course.objects.all()
    count = 0
    for course in courses:
        # Nếu đã có embedding thì bỏ qua (hoặc check updated_at nếu muốn kỹ hơn)
        if hasattr(course, 'embedding') and course.embedding.vector and not force_update:
            continue

        # Tạo nội dung để embed
        # Gộp Title + Description + Tags + Category
        tags_str = ", ".join([t.name for t in course.tags.all()])
        cat_str = ", ".join([c.name for c in course.categories.all()])
        
        content_text = f"Title: {course.title}. Category: {cat_str}. Tags: {tags_str}. Description: {course.description}"
        
        # Gọi API lấy vector
        vector = get_embedding(content_text)
        
        if vector:
            # Lưu vào DB Postgres
            CourseEmbedding.objects.update_or_create(
                course=course,
                defaults={'vector': vector}
            )
            count += 1
    
    return SyncResultDomain(
            status="success", 
            message="Đã đồng bộ vector hoàn tất.", 
            count=count
        )


def suggest_courses(user_interest_text, top_n=5, exclude_ids: list = None):
    """
    Input: Text sở thích của user
    Output: QuerySet các khóa học phù hợp nhất
    """
    # 1. Biến input của user thành Vector
    query_vector = get_embedding(user_interest_text)
    if not query_vector:
        return []

    # 2. Lấy tất cả vector từ DB ra
    # (Với < 1000 khóa học, load hết vào RAM tính cho lẹ, ko cần query phức tạp)
    embeddings = CourseEmbedding.objects.select_related('course').filter(vector__isnull=False)
    
    if exclude_ids:
        embeddings = embeddings.exclude(course_id__in=exclude_ids)

    results = []
    query_vec_np = np.array(query_vector)

    for item in embeddings:
        course_vec_np = np.array(item.vector)
        
        # Tính Cosine Similarity thủ công (bằng Numpy)
        # Công thức: (A . B) / (||A|| * ||B||)
        dot_product = np.dot(query_vec_np, course_vec_np)
        norm_a = np.linalg.norm(query_vec_np)
        norm_b = np.linalg.norm(course_vec_np)
        
        similarity = dot_product / (norm_a * norm_b)
        
        results.append({
            'course_id': item.course.id,
            'score': similarity
        })

    # 3. Sắp xếp điểm từ cao xuống thấp
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 4. Lấy top N ID
    top_ids = [r['course_id'] for r in results[:top_n]]
    
    # 5. Trả về QuerySet (để Django View dễ serialize)
    # Dùng case/when để giữ đúng thứ tự sắp xếp của kết quả
    preserved = models.Case(*[models.When(pk=pk, then=pos) for pos, pk in enumerate(top_ids)])
    
    # [QUAN TRỌNG]: Phải dùng select_related/prefetch_related
    # Vì Domain.factory sẽ chọc vào tags, categories, owner -> Tránh lỗi N+1 query
    queryset = Course.objects.filter(pk__in=top_ids).order_by(preserved)\
        .select_related('owner', 'subject')\
        .prefetch_related('categories', 'tags')

    # 5. [NEW] Convert Model -> Domain bằng Factory
    domain_list = []
    for course_model in queryset:
        # Sử dụng Strategy CATALOG_LIST như bạn mong muốn
        domain = CourseDomain.factory(
            model=course_model, 
            strategy=CourseFetchStrategy.CATALOG_LIST
        )
        domain_list.append(domain)
        
    return domain_list


def recommend_for_user(user, top_n: int = 5) -> list[CourseDomain]:
    """
    AUTO RECOMMENDATION: Dựa trên lịch sử học của User.
    """
    # 1. Lấy danh sách khóa học user đang học/đã học
    # Lấy 3 khóa gần nhất user vừa tương tác để gợi ý cho "tươi mới"
    recent_enrollments = Enrollment.objects.filter(user=user)\
        .select_related('course')\
        .order_by('-last_accessed_at')[:3]

    if not recent_enrollments.exists():
        # COLD START: Nếu user mới tinh chưa học gì
        # -> Trả về danh sách rỗng (để Frontend hiện "Khóa học mới nhất")
        # Hoặc gọi hàm lấy Trending Course tại đây.
        return []

    # 2. Xây dựng "Chân dung sở thích" (User Profile Context)
    # Gom title, tags, category của các khóa đã học thành 1 đoạn văn
    interest_parts = []
    exclude_ids = []

    for enroll in recent_enrollments:
        course = enroll.course
        exclude_ids.append(course.id)
        
        # Gom thông tin: "User thích Python Basic. User thích Web Development."
        tags = ", ".join([t.name for t in course.tags.all()])
        interest_parts.append(f"{course.title} ({tags})")

    # Tạo câu query giả lập
    user_context_text = ". ".join(interest_parts)
    # VD: "Lập trình Python cơ bản (beginner, coding). Django Framework (backend, web)"

    # 3. Gọi lại hàm suggest với text vừa tạo
    return suggest_courses(
        user_interest_text=user_context_text,
        top_n=top_n,
        exclude_ids=exclude_ids # Quan trọng: Không gợi ý lại khóa đã mua
    )