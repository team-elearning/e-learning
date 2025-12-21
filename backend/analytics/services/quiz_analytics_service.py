# from django.db.models import Count, Avg, F, Q
# from typing import Optional, Dict

# from quiz.models import Quiz, Question
# from progress.models import QuizAttempt, QuestionAnswer
# from analytics.domains.quiz_quality_domain import QuizQualityDomain
# from analytics.domains.question_analysis_domain import QuestionAnalysisDomain
# from analytics.models import QuizStatisticSnapshot, QuestionStatisticSnapshot



# # ==========================================
# # PRIVATE HELPERS
# # ==========================================

# def _evaluate_question(p_diff, d_discrim):
#     """
#     Đưa ra lời khuyên dựa trên số liệu.
#     p_diff: Độ khó (0-100).
#     d_discrim: Độ phân biệt (-1 đến 1).
#     """
#     # Case 1: Discrimination Âm (Nguy hiểm nhất)
#     # Học sinh dở làm đúng nhiều hơn học sinh giỏi -> Sai đáp án hoặc đề lừa/mẹo vặt.
#     if d_discrim < 0:
#         return 'check_key', "CẢNH BÁO: Học sinh giỏi hay làm sai câu này. Kiểm tra lại đáp án!"

#     # Case 2: Discrimination Thấp (Gần 0) -> Câu hỏi vô tác dụng phân loại
#     if d_discrim < 0.1:
#         if p_diff > 90:
#             return 'too_easy', "Câu hỏi quá dễ, ai cũng làm đúng."
#         elif p_diff < 20:
#             return 'too_hard', "Câu hỏi quá khó, ai cũng làm sai."
#         else:
#             return 'poor_quality', "Câu hỏi không phân loại được học sinh."

#     # Case 3: Bình thường
#     if p_diff < 30:
#         return 'hard', "Câu hỏi khó (nhưng phân loại tốt)."
#     if p_diff > 80:
#         return 'easy', "Câu hỏi dễ."
        
#     return 'good', "Câu hỏi tốt."


# def _analyze_distractors(question, answers_qs) -> Dict[str, float]:
#     """
#     Đếm tỷ lệ chọn A, B, C, D.
#     Giả sử answer_data lưu dạng: {"selected_ids": ["uuid-opt-1"]}
#     """
#     # Logic này phụ thuộc vào cấu trúc lưu JSON của bạn.
#     # Ở đây tôi demo cách đếm đơn giản.
#     # Cần lấy map option_id -> label (A, B, C) từ question.prompt['options']
    
#     options_map = { opt['id']: opt.get('text', '')[:20] 
#                     for opt in question.prompt.get('options', []) }
    
#     stats = { opt_id: 0 for opt_id in options_map.keys() }
#     total = 0
    
#     for ans in answers_qs:
#         # Lấy list ID đã chọn
#         selected = ans.answer_data.get('selected_ids', [])
#         if isinstance(selected, list):
#             for opt_id in selected:
#                 if opt_id in stats:
#                     stats[opt_id] += 1
#                     total += 1
                    
#     # Chuyển sang phần trăm
#     result = {}
#     if total > 0:
#         for opt_id, count in stats.items():
#             label = options_map.get(opt_id, 'Unknown')
#             percent = round((count / total) * 100, 1)
#             result[label] = percent
            
#     return result


# def _empty_report(quiz):
#     return QuizQualityDomain(
#         quiz_id=str(quiz.id),
#         quiz_title=quiz.title,
#         total_attempts=0,
#         average_score=0.0,
#         questions=[]
#     )


# # ==========================================
# # PUBLIC INTERFACE (ANALYZE)
# # ==========================================

# def analyze_quiz_quality(quiz_id: str) -> Optional[QuizQualityDomain]:
#     try:
#         quiz = Quiz.objects.get(id=quiz_id)
#     except Quiz.DoesNotExist:
#         return None

#     # 1. Lấy tất cả bài làm đã chấm xong (Graded)
#     attempts = QuizAttempt.objects.filter(
#         quiz=quiz, status='graded'
#     ).order_by('-score') # Sắp xếp điểm từ cao xuống thấp để tính phân nhóm
    
#     total_attempts_count = attempts.count()
#     if total_attempts_count < 5:
#         # Chưa đủ mẫu để phân tích thống kê
#         return _empty_report(quiz)

#     # 2. Phân nhóm Top/Bottom (để tính độ phân biệt)
#     # Theo lý thuyết Psychometrics, lấy top 27% và bottom 27%
#     threshold = max(1, int(total_attempts_count * 0.27))
#     attempt_ids = list(attempts.values_list('id', flat=True)) # Lấy 1 lần ra list ID
    
#     top_group_ids = attempt_ids[:threshold]
#     bottom_group_ids = attempt_ids[-threshold:]

#     # 3. BULK CALCULATION (Sức mạnh của SQL)
#     # Thay vì loop query, ta annotate ngay trên QuerySet Question
    
#     questions_stats = Question.objects.filter(quiz=quiz).annotate(
#         # A. Tổng số lần trả lời câu này (trong các attempt đã chấm)
#         # Filter relationship ngược: questionanswer -> attempt -> status='graded'
#         total_answers=Count('questionanswer', filter=Q(questionanswer__attempt__status='graded')),
        
#         # B. Số lần trả lời ĐÚNG
#         correct_answers=Count('questionanswer', filter=Q(questionanswer__is_correct=True, questionanswer__attempt__status='graded')),
        
#         # C. Số lần Nhóm GIỎI trả lời ĐÚNG
#         top_correct=Count('questionanswer', filter=Q(
#             questionanswer__is_correct=True, 
#             questionanswer__attempt__id__in=top_group_ids
#         )),
        
#         # D. Số lần Nhóm YẾU trả lời ĐÚNG
#         bottom_correct=Count('questionanswer', filter=Q(
#             questionanswer__is_correct=True, 
#             questionanswer__attempt__id__in=bottom_group_ids
#         ))
#     ).order_by('position')

#     # 4. Processing & Saving
    
#     # A. Tạo Quiz Snapshot trước
#     avg_score = attempts.aggregate(Avg('score'))['score__avg'] or 0
#     quiz_snapshot = QuizStatisticSnapshot.objects.create(
#         quiz=quiz,
#         total_attempts=total_attempts_count,
#         average_score=round(avg_score, 2)
#     )

#     domain_questions = []
#     quest_stat_objs = []

#     # Bây giờ loop qua results đã có sẵn số liệu (không query DB nữa)
#     for q in questions_stats:
#         q_total = q.total_answers
#         if q_total == 0: continue

#         # Tính toán chỉ số (Python Math - Rất nhanh)
#         difficulty_index = (q.correct_answers / q_total) * 100
        
#         # Tính Discrimination
#         p_top = q.top_correct / len(top_group_ids) if top_group_ids else 0
#         p_bottom = q.bottom_correct / len(bottom_group_ids) if bottom_group_ids else 0
#         discrimination_index = round(p_top - p_bottom, 2)

#         # Evaluate
#         status, recommendation = _evaluate_question(difficulty_index, discrimination_index)
        
#         # Distractor Analysis (Phần này vẫn phải query riêng nếu muốn chi tiết từng option, 
#         # nhưng có thể chấp nhận được hoặc tối ưu sau bằng Raw SQL nếu cần thiết)
#         dist_data = {}
#         if q.type in ['multiple_choice_single', 'multiple_choice_multi']:
#              # Lấy câu trả lời để đếm distractor (Vẫn cần query nhẹ ở đây nhưng đã lọc kỹ)
#              # Để tối ưu hơn nữa, có thể dùng 1 query to lấy toàn bộ answers của quiz rồi group by python
#              dist_data = _analyze_distractors(q.id) 

#         # Tạo Domain
#         q_domain = QuestionAnalysisDomain(
#             question_id=str(q.id),
#             prompt_text=q.prompt.get('text', 'No text')[:80],
#             question_type=q.type,
#             total_attempts=q_total,
#             correct_ratio=round(difficulty_index, 1),
#             discrimination_index=discrimination_index,
#             option_distribution=dist_data,
#             status=status,
#             recommendation=recommendation
#         )
#         domain_questions.append(q_domain)

#         # Tạo Model Object (cho bulk_create)
#         quest_stat_objs.append(QuestionStatisticSnapshot(
#             quiz_stat=quiz_snapshot,
#             question_id=q.id,
#             prompt_text_snapshot=q_domain.prompt_text,
#             total_attempts=q_total,
#             correct_ratio=q_domain.correct_ratio,
#             discrimination_index=discrimination_index,
#             option_distribution=dist_data,
#             status=status,
#             recommendation=recommendation
#         ))

#     # Bulk Save
#     QuestionStatisticSnapshot.objects.bulk_create(quest_stat_objs)

#     return QuizQualityDomain(
#         quiz_id=str(quiz.id),
#         quiz_title=quiz.title,
#         total_attempts=total_attempts_count,
#         average_score=round(avg_score, 2),
#         questions=domain_questions
#     )

