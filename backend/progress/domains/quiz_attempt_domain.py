from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from uuid import UUID
from django.utils import timezone



@dataclass
class QuizAttemptDomain:
    id: UUID
    status: str
    started_at: datetime
    remaining_seconds: Optional[int]
    message: str

    @classmethod
    def from_model(cls, attempt, quiz) -> 'QuizAttemptDomain':
        """
        Factory Method: Chuyển từ Django Model -> Domain.
        Tại đây ta tính toán luôn logic thời gian còn lại (Encapsulation).
        """
        now = timezone.now()
        remaining_seconds = None

        # --- LOGIC TÍNH COUNTDOWN (Chuyển từ View sang đây) ---
        if quiz.time_limit_minutes:
            limit_seconds = quiz.time_limit_minutes * 60
            # Thời gian đã trôi qua
            elapsed = (now - attempt.started_at).total_seconds()
            # Thời gian còn lại theo limit
            remaining_seconds = max(0, limit_seconds - elapsed)

            # CLAMP: Kiểm tra nếu Quiz sắp đóng cửa (Time Close)
            if quiz.time_close:
                seconds_until_close = (quiz.time_close - now).total_seconds()
                # Lấy số nhỏ hơn giữa (Time Limit còn lại) và (Khoảng cách đến giờ đóng)
                if seconds_until_close < remaining_seconds:
                    remaining_seconds = max(0, seconds_until_close)
        
        # Logic message
        msg = "Bắt đầu làm bài thành công." 
        # So sánh chênh lệch nhỏ (vài giây) để biết là mới tạo hay resume
        if (now - attempt.started_at).total_seconds() > 5:
            msg = "Tiếp tục bài làm."

        return cls(
            id=attempt.id,
            status=attempt.status,
            started_at=attempt.started_at,
            remaining_seconds=int(remaining_seconds) if remaining_seconds is not None else None,
            message=msg
        )