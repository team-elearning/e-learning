# from django.db.models import F
# from typing import Optional

# from content.models import ContentBlock
# from analytics.models import UserActivityLog
# from analytics.domains.video_engagement_domain import VideoEngagementDomain


# # ==========================================
# # PUBLIC INTERFACE (HELPER - HEURISTIC LOGIC)
# # ==========================================

# def _classify_behavior(stats, duration, time_spent):
#     """
#     Dùng luật (Rule-based) để đoán phong cách học.
#     """
#     seek_fwd = stats['seek_fwd']
#     seek_bwd = stats['seek_bwd']
#     pause = stats['pause']
    
#     # Nếu duration = 0 (Video lỗi)
#     if duration == 0: return 'unknown', 0.0, "Video không có thời lượng."

#     percent_covered = (stats['max_ts'] / duration) * 100

#     # 1. SKIMMER (Học lướt)
#     # Tua đi nhiều + Thời gian ở lại trang < 50% thời lượng video
#     if seek_fwd > 3 and time_spent < (duration * 0.5):
#         return 'skimmer', 4.0, "Học viên tua nhanh qua nội dung, có thể chưa nắm vững."

#     # 2. DEEP LEARNER (Học sâu)
#     # Tua lại nhiều (nghiền ngẫm) + Pause nhiều (ghi chép)
#     if seek_bwd > 2 or pause > 3:
#         return 'deep_learner', 9.5, "Học viên xem rất kỹ, tua lại để ôn tập."

#     # 3. DROPOUT (Bỏ cuộc)
#     # Xem chưa đến 20%
#     if percent_covered < 20:
#         return 'dropout', 2.0, "Học viên tắt video quá sớm."

#     # 4. PASSIVE (Thụ động)
#     # Không seek, không pause, xem một mạch (hoặc treo máy)
#     if seek_fwd == 0 and seek_bwd == 0 and pause == 0:
#         # Nếu xem hết -> Tốt (hoặc treo máy)
#         if percent_covered > 90:
#             return 'passive', 8.0, "Xem hết video một mạch."
#         else:
#             return 'passive', 5.0, "Xem thụ động và dừng giữa chừng."

#     return 'normal', 7.0, "Hành vi học tập bình thường."


# def _empty_engagement(user_id, block):
#     return VideoEngagementDomain(
#         user_id=user_id,
#         content_block_id=str(block.id),
#         video_title=block.title,
#         video_duration=block.duration,
#         total_time_spent=0, actual_watch_time=0, max_timestamp_reached=0,
#         play_count=0, pause_count=0, seek_forward_count=0, seek_backward_count=0,
#         learning_style='not_started', engagement_quality=0.0, insight_text="Chưa xem video."
#     )


# # ==========================================
# # PUBLIC INTERFACE (ANALYZE)
# # ==========================================

# def analyze_video_engagement(user_id: str, block_id: str) -> Optional[VideoEngagementDomain]:     
#     # 1. Lấy thông tin gốc của Video
#     try:
#         block = ContentBlock.objects.get(id=block_id, type='video')
#     except ContentBlock.DoesNotExist:
#         return None

#     # 2. Lấy Logs (Sắp xếp theo thời gian tăng dần là BẮT BUỘC)
#     logs = UserActivityLog.objects.filter(
#         user_id=user_id,
#         entity_type='content_block', # Lưu ý check lại entity_type trong log của bạn
#         entity_id=str(block_id),
#         action__in=['VIDEO_PLAY', 'VIDEO_PAUSE', 'VIDEO_SEEK', 'VIDEO_COMPLETE']
#     ).order_by('timestamp')

#     if not logs.exists():
#         return _empty_engagement(user_id, block)

#     # 3. Thuật toán Replay (Tái hiện hành vi)
#     # Chúng ta sẽ duyệt qua từng log để tính toán
#     stats = {
#         'play': 0, 'pause': 0, 
#         'seek_fwd': 0, 'seek_bwd': 0,
#         'max_ts': 0,
#         'total_watch_seconds': 0 # Thời gian video thực chạy
#     }
    
#     last_action_time = None
#     last_video_timestamp = 0

#     for log in logs:
#         # Lấy thông tin từ payload (Giả sử payload lưu: {'timestamp': 120, 'to': 150...})
#         current_video_ts = log.payload.get('timestamp', 0) # Vị trí video hiện tại (giây)
        
#         # Cập nhật Max Timestamp đã đạt được
#         if current_video_ts > stats['max_ts']:
#             stats['max_ts'] = current_video_ts

#         # Phân loại hành động
#         if log.action == 'VIDEO_PLAY':
#             stats['play'] += 1
            
#         elif log.action == 'VIDEO_PAUSE':
#             stats['pause'] += 1
#             # Nếu trước đó đang Play, cộng dồn thời gian xem
#             # (Logic đơn giản hóa: Tính khoảng cách giữa các log, 
#             # thực tế cần check log trước đó là PLAY hay gì)
#             pass 

#         elif log.action == 'VIDEO_SEEK':
#             target_ts = log.payload.get('to_timestamp', current_video_ts)
#             if target_ts > current_video_ts:
#                 stats['seek_fwd'] += 1
#             else:
#                 stats['seek_bwd'] += 1
            
#             # Cập nhật lại vị trí hiện tại sau khi seek
#             current_video_ts = target_ts 

#         elif log.action == 'VIDEO_COMPLETE':
#             stats['max_ts'] = block.duration

#     # Tính toán thời gian thực tế (Approximate)
#     # Cách đơn giản nhất: Lấy timestamp log cuối - log đầu (Time spent on page)
#     # Cách xịn hơn: Cộng dồn khoảng thời gian giữa PLAY và PAUSE (Cần logic phức tạp hơn)
#     # Ở đây ta dùng công thức ước lượng dựa trên heartbeat (UserBlockProgress) nếu có, 
#     # hoặc dùng tổng timestamp log.
#     # Giả sử ta lấy từ UserBlockProgress (đã có trường time_spent_seconds)
#     # Nhưng ở đây ta đang viết service thuần log, nên ta sẽ dùng max_timestamp làm proxy tạm.
    
#     # Để chính xác, ta nên lấy time_spent_seconds từ bảng UserBlockProgress (nếu bạn đã lưu)
#     # Ở đây tôi giả định bạn muốn tính từ Log raw:
#     first_log = logs.first()
#     last_log = logs.last()
#     time_spent_on_page = int((last_log.timestamp - first_log.timestamp).total_seconds())

#     # 4. Phân loại hành vi (Behavior Classification)
#     style, quality, insight = _classify_behavior(stats, block.duration, time_spent_on_page)

#     return VideoEngagementDomain(
#         user_id=user_id,
#         content_block_id=str(block.id),
#         video_title=block.title or "Video",
#         video_duration=block.duration,
        
#         total_time_spent=time_spent_on_page,
#         actual_watch_time=stats['max_ts'], # Tạm dùng max ts
#         max_timestamp_reached=int(stats['max_ts']),
        
#         play_count=stats['play'],
#         pause_count=stats['pause'],
#         seek_forward_count=stats['seek_fwd'],
#         seek_backward_count=stats['seek_bwd'],
        
#         learning_style=style,
#         engagement_quality=quality,
#         insight_text=insight
#     )

