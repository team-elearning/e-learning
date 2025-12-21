from rest_framework import serializers


VALID_MEDIA_TYPES = {'image', 'video', 'audio', 'file'}

def validate_prompt_structure(data):
    """
    Validate cấu trúc Prompt "Rich Media".
    
    Cấu trúc mong đợi:
    {
        "content": "HTML/Text string",  # (Optional - Bắt buộc nếu không có media)
        "media": [                        # (Optional - Bắt buộc nếu không có content)
            { 
                "type": "image",          # image | video | audio | file
                "caption": "Mô tả...",    # (Optional)
                
                # --- NGUỒN DỮ LIỆU (Chọn 1 trong 3) ---
                "file_id": "uuid...",     # Case 1: File mới upload (Staging)
                "file_path": "path/...",  # Case 2: File đã có trong hệ thống (S3 Private)
                "url": "https://..."      # Case 3: Link ngoài (Youtube, Vimeo...)
            }
        ],
        "options": [                      # (Optional - Dành cho trắc nghiệm)
            { "id": "A", "text": "..." }
        ]
    }

    Hỗ trợ 3 nguồn media:
    1. file_id: File mới upload (Staging)
    2. file_path: File đã lưu trong hệ thống (S3 Private)
    3. url: Link ngoài (Youtube, v.v.)
    """
    if not isinstance(data, dict):
        raise serializers.ValidationError("Prompt phải là một JSON object.")

    content = data.get('content')
    media = data.get('media')

    if not content and not media:
        raise serializers.ValidationError("Câu hỏi phải có nội dung (content) HOẶC đính kèm (media).")
    
    # 2. Validate Media List
    if media:
        if not isinstance(media, list):
            raise serializers.ValidationError("'media' phải là một danh sách (list).")
        
        for index, item in enumerate(media):
            if not isinstance(item, dict):
                raise serializers.ValidationError(f"Item media tại vị trí {index} phải là object.")
            
            # Check Type
            m_type = item.get('type')
            if m_type not in VALID_MEDIA_TYPES:
                raise serializers.ValidationError(f"Media type '{m_type}' không hợp lệ. Chỉ chấp nhận: {VALID_MEDIA_TYPES}")
            
            # [FIXED] Check Source (Chấp nhận 1 trong 3: id, path, url)
            has_source = any([
                item.get('file_id'),   # Case 1: File mới (quan trọng nhất)
                item.get('file_path'), # Case 2: File cũ
                item.get('url')        # Case 3: External link
            ])

            if not has_source:
                raise serializers.ValidationError(
                    f"Media tại vị trí {index} thiếu nguồn dữ liệu. "
                    "Cần cung cấp 'file_id' (upload mới), 'file_path' (có sẵn), hoặc 'url' (link ngoài)."
                )

    # Validate Options (cho trắc nghiệm/matching)
    if 'options' in data:
        options = data['options']
        if not isinstance(options, list):
            raise serializers.ValidationError("'options' phải là một danh sách (array).")
        
        seen_ids = set()
        for opt in options:
            if not isinstance(opt, dict):
                raise serializers.ValidationError("Mỗi option phải là object.")
            if 'id' not in opt or 'text' not in opt:
                raise serializers.ValidationError("Mỗi lựa chọn trong 'options' phải có 'id' và 'text'.")
            
            # Check trùng ID option
            opt_id = str(opt['id'])
            if opt_id in seen_ids:
                raise serializers.ValidationError(f"Option ID '{opt['id']}' bị trùng lặp.")
            seen_ids.add(opt_id)
            

def validate_answer_payload(q_type, payload, prompt_options=None):
    """
    Validate tính logic của đáp án đúng so với prompt.
    """
    if not isinstance(payload, dict):
        raise serializers.ValidationError("Answer Payload phải là JSON object.")

    # Lấy tập hợp ID hợp lệ từ prompt
    valid_ids = {str(opt['id']) for opt in prompt_options} if prompt_options else set()

    # --- 1. SINGLE CHOICE ---
    if q_type == 'multiple_choice_single':
        cid = payload.get('correct_id')
        if not cid:
            raise serializers.ValidationError("Thiếu 'correct_id'.")
        if valid_ids and str(cid) not in valid_ids:
            raise serializers.ValidationError(f"ID đáp án '{cid}' không tồn tại trong danh sách lựa chọn.")

    # --- 2. MULTI CHOICE ---
    elif q_type == 'multiple_choice_multi':
        cids = payload.get('correct_ids')
        if not isinstance(cids, list) or not cids:
            raise serializers.ValidationError("Thiếu 'correct_ids' (phải là danh sách khác rỗng).")
        
        invalid = [cid for cid in cids if str(cid) not in valid_ids]
        if invalid:
            raise serializers.ValidationError(f"Các ID đáp án sau không tồn tại trong options: {invalid}")

    # --- 3. TRUE / FALSE ---
    elif q_type == 'true_false':
        # True/False không dùng options trong prompt, mà render UI cứng.
        # Nhưng payload bắt buộc phải có correct_value
        if 'correct_value' not in payload:
            raise serializers.ValidationError("Thiếu 'correct_value'.")
        if not isinstance(payload['correct_value'], bool):
            raise serializers.ValidationError("'correct_value' phải là boolean (true/false).")

    # --- 4. SHORT ANSWER / FILL BLANK ---
    elif q_type in ['short_answer', 'fill_in_the_blank']:
        accepted = payload.get('accepted_texts')
        if not isinstance(accepted, list) or not accepted:
            raise serializers.ValidationError("Thiếu 'accepted_texts' (danh sách các câu trả lời chấp nhận).")
        
        # Check case sensitive flag (optional)
        if 'case_sensitive' in payload and not isinstance(payload['case_sensitive'], bool):
             raise serializers.ValidationError("'case_sensitive' phải là boolean.")

    # --- 5. MATCHING (Nối cột) ---
    elif q_type == 'matching':
        matches = payload.get('matches') # {"A": "1", "B": "2"}
        if not isinstance(matches, dict) or not matches:
            raise serializers.ValidationError("Thiếu 'matches' (cặp nối đúng).")
        
        # Kiểm tra xem các Key trong matches có nằm trong Option không (nếu có option)
        # Thường Matching sẽ có 2 list: Prompts (Left) và Options (Right).
        # Tùy cấu trúc prompt của bạn. Nếu prompt['options'] là cột phải (Right side).
        # Thì value của matches phải nằm trong valid_ids.
        if valid_ids:
            for key, val in matches.items():
                if str(val) not in valid_ids:
                     raise serializers.ValidationError(f"Giá trị nối '{val}' không tồn tại trong Options.")

    # --- 6. ESSAY (Tự luận) ---
    elif q_type == 'essay':
        # Essay không cần đáp án đúng cố định, nhưng có thể cần rubric
        pass