from content.models import ContentBlock



def evaluate(block: ContentBlock, interaction_data: dict, current_progress_seconds: int) -> bool:
    block_type = block.type
    payload = block.payload or {}

    # --- LOGIC 1: VIDEO (Xong khi xem > 90%) ---
    if block_type == 'video':
        duration = block.duration

        if duration == 0:
            payload = block.payload or {}
            duration = payload.get('duration', 0)

        if duration == 0: 
            return True # Safe-guard: Video lỗi duration thì cho qua
        
        # Cách 1: Dựa vào timestamp hiện tại (Client gửi lên)
        current_time = interaction_data.get('video_timestamp', 0)
        if current_time / duration >= 0.9:
            return True
            
        # Cách 2: Dựa vào tổng thời gian user đã ở lại trang (Server tính)
        # if current_progress_seconds / duration >= 0.9:
        #     return True
        
        return False

    # --- LOGIC 2: QUIZ (Xong khi submit và pass - Xử lý ở API khác, ko phải heartbeat) ---
    elif block_type == 'quiz':
        # Heartbeat chỉ track thời gian làm bài, không bao giờ đánh dấu hoàn thành Quiz
        return False

    # --- LOGIC 3: TEXT/PDF (Xong khi scroll cuối hoặc ở đủ lâu) ---
    elif block_type in ['rich_text', 'pdf', 'docx']:
        # Client gửi flag 'read_complete' khi scroll xuống cuối
        if interaction_data.get('read_complete') is True:
            return True
        
        # Hoặc ở lại trang đủ tối thiểu 10 giây
        min_read_time = payload.get('min_read_seconds', 10)
        if current_progress_seconds >= min_read_time:
            return True
            
        return False

    return False