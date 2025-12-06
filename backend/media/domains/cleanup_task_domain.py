from dataclasses import dataclass
from typing import Optional



@dataclass
class CleanupTaskDomain:
    """
    Domain object đại diện cho kết quả của việc kích hoạt tác vụ dọn dẹp.
    """
    is_started: bool       # True nếu thread bắt đầu chạy, False nếu bị lock
    message: str           # Thông báo cho người dùng
    lock_id: str           # ID của lock (để debug)
    
    # Factory method tiện lợi
    @classmethod
    def locked(cls, message: str):
        return cls(is_started=False, message=message, lock_id="")

    @classmethod
    def started(cls, message: str, lock_id: str):
        return cls(is_started=True, message=message, lock_id=lock_id)