# @staticmethod
# def handle_block_completion(user, block_instance):
#     """
#     Hàm entry-point: Gọi hàm này sau khi User hoàn thành 1 Block.
#     """
#     # 1. Truy ngược lên cha (Navigation)
#     # Block -> Lesson -> Module -> Course
#     lesson_instance = block_instance.lesson 
#     module_instance = lesson_instance.module
#     course_instance = module_instance.course
    
#     # 2. Check xem Lesson này đã xong chưa?
#     is_lesson_just_finished = _check_and_update_lesson(user, lesson_instance, course_instance)
    
#     # 3. Nếu Lesson vừa mới xong (hoặc trạng thái thay đổi), tính lại % Course
#     # (Hoặc có thể gọi luôn để đảm bảo tính realtime 100%)
#     _update_course_progress(user, course_instance)


# @staticmethod
# def _check_and_update_lesson(user, lesson, course) -> bool:
#     """
#     Kiểm tra xem user đã hoàn thành tất cả blocks trong Lesson chưa.
#     """
#     # A. Lấy tổng số block trong lesson
#     # Lưu ý: Nếu sau này bạn thêm field 'is_required' vào ContentBlock, hãy filter ở đây.
#     total_blocks = lesson.content_blocks.count() # Dùng related_name='content_blocks'
    
#     if total_blocks == 0:
#         # Lesson rỗng coi như xong (hoặc xử lý tùy logic)
#         return True

#     # B. Đếm số block đã hoàn thành
#     completed_blocks_count = UserBlockProgress.objects.filter(
#         user=user,
#         block__lesson=lesson, 
#         is_completed=True
#     ).count()

#     is_completed = completed_blocks_count >= total_blocks

#     # C. Lưu vào bảng LessonCompletion
#     if is_completed:
#         LessonCompletion.objects.update_or_create(
#             user=user,
#             lesson_id=lesson.id,
#             defaults={
#                 # Lưu denormalized fields để query nhanh
#                 'course_id': course.id, 
#                 'module_id': lesson.module_id,
#                 'is_completed': True,
#                 'completed_at': timezone.now()
#             }
#         )
    
#     return is_completed


# @staticmethod
# def _update_course_progress(user, course):
#     """
#     Tính % Course dựa trên tổng số Lesson (xuyên suốt các Module).
#     """
#     # A. Đếm tổng số Lesson trong Course (qua trung gian Module)
#     # Logic: Tìm tất cả Lesson mà module của nó thuộc course này
#     total_lessons = Lesson.objects.filter(module__course=course).count()
    
#     if total_lessons == 0:
#         percent = 0.0 # Course chưa có bài học nào
#     else:
#         # B. Đếm số Lesson user đã hoàn thành (Dựa vào bảng LessonCompletion)
#         # Bảng này đã có course_id (denormalized) nên query cực nhanh, không cần join bảng
#         completed_lessons_count = LessonCompletion.objects.filter(
#             user=user,
#             course_id=course.id,
#             is_completed=True
#         ).count()
        
#         percent = (completed_lessons_count / total_lessons) * 100
#         percent = round(min(percent, 100.0), 2)

#     # C. Cập nhật Dashboard
#     CourseProgress.objects.update_or_create(
#         user=user,
#         course_id=course.id,
#         defaults={
#             'percent_completed': percent,
#             'is_completed': (percent == 100.0),
#             'last_accessed_at': timezone.now()
#         }
#     )