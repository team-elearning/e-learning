import os
import numpy as np
from dotenv import load_dotenv
from django.conf import settings
from django.db import models
from openai import OpenAI

from content.models import Course
from personalization.models import CourseEmbedding
from personalization.domains.sync_result_domain import SyncResultDomain



load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Khởi tạo Client (Nên để API Key trong .env)
client = OpenAI(api_key=OPENAI_API_KEY)

@staticmethod
def get_embedding(text):
    """Gọi OpenAI để biến Text thành Vector"""
    text = text.replace("\n", " ")
    try:
        response = client.embeddings.create(input=[text], model="text-embedding-3-small")
        return response.data[0].embedding
    except Exception as e:
        print(f"Lỗi OpenAI: {e}")
        return []


@classmethod
def sync_course_embeddings(force_update=False) -> SyncResultDomain:
    """
    Quét toàn bộ khóa học, cái nào chưa có vector thì tạo.
    Hàm này có thể chạy định kỳ hoặc chạy tay.
    """
    courses = Course.objects.all()
    count = 0
    for course in courses:
        # Nếu đã có embedding thì bỏ qua (hoặc check updated_at nếu muốn kỹ hơn)
        if hasattr(course, 'embedding') and course.embedding.vector:
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


@classmethod
def suggest_courses(user_interest_text, top_n=5):
    """
    Input: Text sở thích của user
    Output: QuerySet các khóa học phù hợp nhất
    """
    # 1. Biến input của user thành Vector
    query_vector = get_embedding(user_interest_text)
    if not query_vector:
        return Course.objects.none()

    # 2. Lấy tất cả vector từ DB ra
    # (Với < 1000 khóa học, load hết vào RAM tính cho lẹ, ko cần query phức tạp)
    embeddings = CourseEmbedding.objects.select_related('course').filter(vector__isnull=False)
    
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
    
    return Course.objects.filter(pk__in=top_ids).order_by(preserved)