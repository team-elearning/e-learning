import os
import boto3
import json
import numpy as np
from dotenv import load_dotenv
from django.conf import settings
from django.db import models
from openai import OpenAI

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
    
 
def suggest_courses(user_interest_text, top_n=5, exclude_ids: list = None, min_score: float = 0.5):
    """
    Input: Text sở thích của user
    Output: QuerySet các khóa học phù hợp nhất
    """
    # 1. Biến input của user thành Vector, Lấy vector query từ Bedrock
    query_vector = get_embedding(user_interest_text)
    if not query_vector:
        return []
    
    # Chuẩn bị Query Vector (Normalize luôn để tính Cosine cho nhanh)
    # Cosine(A, B) = (A . B) / (|A| * |B|)
    # Nếu A và B đều đã chuẩn hóa (độ dài = 1), thì Cosine(A, B) = A . B
    query_vec_np = np.array(query_vector)
    query_norm = np.linalg.norm(query_vec_np)
    if query_norm == 0: 
        return []
    query_vec_normalized = query_vec_np / query_norm

    # 2. Lấy dữ liệu từ DB
    # Chỉ lấy trường id và vector để tiết kiệm RAM (đừng lấy hết các trường title, desc...)
    queryset = CourseEmbedding.objects.filter(vector__isnull=False).values('course_id', 'vector')
    
    if exclude_ids:
        queryset = queryset.exclude(course_id__in=exclude_ids)

    candidates = list(queryset)
    if not candidates:
        return []
    
    # 3. TÍNH TOÁN MA TRẬN (VECTORIZATION) - Thay thế vòng lặp for
    # Tạo ma trận các vector khóa học (N rows, 1536 cols)
    # Lưu ý: 'item' ở đây là dict, phải truy cập bằng ['vector']
    course_vectors = np.array([item['vector'] for item in candidates])
    course_ids = np.array([item['course_id'] for item in candidates])

    # Tính norm cho toàn bộ ma trận khóa học (axis=1 là tính theo hàng)
    course_norms = np.linalg.norm(course_vectors, axis=1)

    # Tránh chia cho 0
    course_norms[course_norms == 0] = 1e-10 
    
    # Chuẩn hóa ma trận khóa học
    # [:, np.newaxis] giúp biến mảng 1 chiều thành cột để chia broadcasting
    course_matrix_normalized = course_vectors / course_norms[:, np.newaxis]

    # Tính Dot Product: (N, 1536) dot (1536,) -> (N,)
    # Kết quả là mảng điểm số của tất cả khóa học
    scores = np.dot(course_matrix_normalized, query_vec_normalized)

    # 4. Lọc và Sắp xếp
    # Lấy các index có điểm >= min_score
    filtered_indices = np.where(scores >= min_score)[0]

    results = []
    for idx in filtered_indices:
        results.append({
            'course_id': course_ids[idx], # Truy cập bằng index numpy
            'score': scores[idx]
        })

    # Sort giảm dần
    results.sort(key=lambda x: x['score'], reverse=True)
    
    # 5. Lấy Top N & Fetch DB
    top_ids = [r['course_id'] for r in results[:top_n]]

    if not top_ids:
        return []
    
    preserved = models.Case(*[models.When(pk=pk, then=pos) for pos, pk in enumerate(top_ids)])
    
    course_queryset = Course.objects.filter(pk__in=top_ids).order_by(preserved)\
        .select_related('owner', 'subject')\
        .prefetch_related('categories', 'tags')

    domain_list = []
    for course_model in course_queryset:
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
        .prefetch_related('course__tags')\
        .order_by('-last_accessed_at')[:3]

    if not recent_enrollments.exists():
        # COLD START:
        # Gợi ý: Nên trả về các khóa học "Trending" hoặc "Free" thay vì rỗng hoàn toàn
        # return suggest_trending_courses(top_n)
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
        interest_parts.append(f"{course.title}. Topics: {tags}")

    # Tạo câu query giả lập
    user_context_text = ". ".join(interest_parts)
    # VD: "Lập trình Python cơ bản (beginner, coding). Django Framework (backend, web)"

    # 3. Gọi lại hàm suggest với text vừa tạo
    return suggest_courses(
        user_interest_text=user_context_text,
        top_n=top_n,
        exclude_ids=exclude_ids # Quan trọng: Không gợi ý lại khóa đã mua
    )