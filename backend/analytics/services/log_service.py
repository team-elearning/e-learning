from django.db import transaction
from django.conf import settings
from typing import Optional, Dict, Any, List

from analytics.models import UserActivityLog, ACTION_VERBS
from analytics.domains.activity_log_domain import ActivityLogDomain
from analytics.tasks import async_log_activity, update_streak_on_activity_logic



VALID_ACTIONS = {action[0] for action in ACTION_VERBS}

# ==========================================
# PUBLIC INTERFACE (HELPER)
# ==========================================

def _validate_and_normalize(user, 
    data: Dict[str, Any], 
    ip_address: str, 
    user_agent: str) -> Optional[Dict[str, Any]]:
    """
    Nhiệm vụ: Đảm bảo dữ liệu rác không chui vào hệ thống Analytics.
    """
    action = data.get('action')
    
    # Check 1: Action có hợp lệ trong hệ thống không?
    if action not in VALID_ACTIONS:
        # Log warning ở đây nếu cần
        print(f"⚠️ Tracking Rejected: Invalid Action '{action}' from user {user.id}")
        return None

    # Check 2: Nếu là action liên quan đến entity, bắt buộc phải có entity_id
    entity_type = data.get('entity_type')
    entity_id = data.get('entity_id')
    
    if entity_type and not entity_id:
        print(f"⚠️ Missing Entity ID for type: {data.get('entity_type')}")
        return None

    # 3. Enrichment (Làm giàu dữ liệu context)
    # Tự động lấy IP/Agent từ payload nếu bên ngoài chưa tách ra
    payload = data.get('payload', {}) or {}
    if not isinstance(payload, dict):
        payload = {} # Fail-safe nếu frontend gửi string
    
    # Merge các thông tin context vào payload để lưu trữ JSON gọn gàng
    enriched_payload = payload.copy()
    if ip_address:
        enriched_payload['_ip'] = ip_address
    if user_agent:
        enriched_payload['_ua'] = user_agent

    return {
        'user': user,
        'action': action,
        'entity_type': entity_type,
        'entity_id': entity_id,
        'payload': enriched_payload,
        'session_id': data.get('session_id'),
        # Default False nếu không gửi
        'is_critical': data.get('is_critical', False) 
    }


def _save_to_db(data: Dict[str, Any]) -> Optional[ActivityLogDomain]:
    """
    Ghi 1 bản ghi vào DB.
    """
    try:
        log = UserActivityLog.objects.create(
            user=data['user'],
            action=data['action'],
            entity_type=data['entity_type'],
            entity_id=data['entity_id'],
            payload=data['payload'],
            session_id=data['session_id']
        )
        return ActivityLogDomain.from_model(log)
    
    except Exception as e:
        # Silent Fail: Tracking chết không được làm ảnh hưởng user
        print(f"🔴 Tracking DB Error: {e}")
        return None
        

@transaction.atomic
def _bulk_save_to_db(data_list: List[Dict[str, Any]]) -> List[ActivityLogDomain]:
    """
    Ghi nhiều bản ghi 1 lúc (Tối ưu SQL).
    """
    logs_to_create = [
        UserActivityLog(
            user=item['user'],
            action=item['action'],
            entity_type=item['entity_type'],
            entity_id=item['entity_id'],
            payload=item['payload'],
            session_id=item['session_id']
        ) for item in data_list
    ]
    
    try:
        # bulk_create nhanh hơn loop create rất nhiều
        created_logs = UserActivityLog.objects.bulk_create(logs_to_create)
        
        # Convert sang Domain List
        return [ActivityLogDomain.from_model(log) for log in created_logs]
    except Exception as e:
        print(f"🔴 Bulk Tracking Error: {e}")
        return []


# ==========================================
# PUBLIC INTERFACE (RECORD)
# ==========================================

def record_activity(user, 
    data: Dict[str, Any], 
    ip_address: Optional[str] = None, 
    user_agent: Optional[str] = None) -> Optional[ActivityLogDomain]:
    """
        Ghi nhận 1 hành động đơn lẻ.
        :param data: Dict chứa {action, entity_type, entity_id, payload, session_id...}
    """
    # 1. Validate & Clean Data
    clean_data = _validate_and_normalize(user, data, ip_address, user_agent)
    if not clean_data:
        return None

    # return _save_to_db(clean_data)

    is_critical = clean_data.get('is_critical', False)

    if is_critical:
        # A. Critical -> Ghi ngay lập tức (Sync) để đảm bảo toàn vẹn
        # [LƯU Ý]: Nếu là critical (ví dụ nộp bài thi), ta NÊN update streak ngay (Sync)
        # để user thấy kết quả ngay lập tức (Instant Gratification).
        log_entry = _save_to_db(clean_data)

        # Gọi update streak trực tiếp (Sync) vì đây là hành động quan trọng
        update_streak_on_activity_logic(user)

        return log_entry
    else:
        # B. Non-critical -> Đẩy vào Queue (Async)
        
        # BƯỚC QUAN TRỌNG: Serializer dữ liệu trước khi gửi cho Celery
        # Celery không hiểu object 'user', nên ta chỉ gửi 'user_id'
        task_payload = clean_data.copy()
        task_payload.pop('user') # Bỏ object user ra
        user_id = user.id       # Chỉ lấy ID

        # Gọi task async
        transaction.on_commit(
            lambda: async_log_activity.delay(user_id, task_payload)
        )
        
        return True # Return True để báo hiệu đã đẩy vào queue thành công
    

def record_batch(user, 
    data_list: List[Dict[str, Any]], 
    ip_address: Optional[str] = None, 
    user_agent: Optional[str] = None) -> List[ActivityLogDomain]:
    """
    Xử lý hàng loạt (Bulk Insert).
    Dùng cho heartbeat video (30s gửi 1 lần) hoặc scroll tracking.
    Thay vì 10 request DB, ta chỉ làm 1 request.
    """
    clean_entries = []

    # 1. Loop & Validate
    for item in data_list:
        clean_item = _validate_and_normalize(user, item, ip_address, user_agent)
        if clean_item:
            clean_entries.append(clean_item)
    
    if not clean_entries:
        return []

    # Bulk Create để tối ưu DB Performance
    return _bulk_save_to_db(clean_entries)