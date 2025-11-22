import pandas as pd
from docx import Document
import pandas as pd
import numpy as np # Cần để xử lý nan an toàn
import re



"""
Service chỉ làm nhiệm vụ: File -> List[Dict] (JSON).
Không truy cập Database.
"""
def parse_excel(file_obj) -> list:
    """ Chuyên trị file .xlsx, .xls """
    try:
        # Đọc Excel
        df = pd.read_excel(file_obj, engine='openpyxl')
        # Chuẩn hóa tên cột
        df.columns = [str(c).lower().strip() for c in df.columns]
        return _process_dataframe(df)
    except Exception as e:
        raise ValueError(f"Lỗi đọc file Excel: {str(e)}")


def parse_csv(file_obj) -> list:
    """ Chuyên trị file .csv """
    try:
        # Đọc CSV (Lưu ý encoding utf-8 cho tiếng Việt)
        # dtype=str để tránh việc '09' bị biến thành số 9
        df = pd.read_csv(file_obj, encoding='utf-8', dtype=str)
        
        # Chuẩn hóa tên cột
        df.columns = [str(c).lower().strip() for c in df.columns]
        return _process_dataframe(df)
    except UnicodeDecodeError:
        raise ValueError("Lỗi font chữ CSV. Vui lòng lưu file CSV với encoding UTF-8.")
    except Exception as e:
        raise ValueError(f"Lỗi đọc file CSV: {str(e)}")


def _process_dataframe(df: pd.DataFrame) -> list:
    """
    Hàm nội bộ: Chuyển đổi DataFrame (bảng) thành List JSON.
    Dùng chung cho cả Excel và CSV.
    """
    questions_list = []

    # Thay thế các giá trị NaN (Not a Number) thành None hoặc chuỗi rỗng để dễ check
    df = df.replace({np.nan: None})

    for index, row in df.iterrows():
        try:
            # 1. Lấy các field cơ bản
            q_type = str(row.get('type', 'multiple_choice_single')).strip()
            content = row.get('content')
            
            # Nếu content trống -> Bỏ qua dòng này
            if not content: continue 

            prompt = {
                "text": str(content),
                "image_url": row.get('image_url'), # Đã replace nan thành None ở trên
                "options": []
            }

            # 2. Map Options (A, B, C, D, E)
            for char in ['a', 'b', 'c', 'd', 'e']:
                val = row.get(f'option_{char}')
                if val: # Check if not None/Empty
                    prompt['options'].append({
                        "id": char.upper(), 
                        "text": str(val)
                    })

            # 3. Map Answer Payload
            correct_raw = row.get('correct_answer')
            correct_ids = []
            if correct_raw:
                # Tách dấu phẩy, viết hoa, xóa khoảng trắng (vd: "a, b" -> ["A", "B"])
                correct_ids = [x.strip().upper() for x in str(correct_raw).split(',')]

            answer_payload = {}
            if q_type == 'short_answer':
                # Với câu trả lời ngắn, correct_answer là text đáp án
                answer_payload = {
                    "correct_text": [str(correct_raw)] if correct_raw else [], 
                    "match_type": "exact"
                }
            else:
                # Với trắc nghiệm, đúng sai...
                answer_payload = {"correct_ids": correct_ids}

            # 4. Gom vào list
            questions_list.append({
                "id": None, # Null để FE biết là tạo mới
                "type": q_type,
                "prompt": prompt,
                "answer_payload": answer_payload,
                "hint": {"text": str(row.get('hint', '')) if row.get('hint') else ""},
                "position": index + 1 
            })

        except Exception:
            # Log lỗi nếu cần thiết, nhưng continue để không chết cả file
            continue
    
    return questions_list


def parse_docx(file_obj) -> list:
    """
    Đọc file Word theo chuẩn Aiken/Template:
    Câu 1: ...
    A. ...
    B. ...
    ANSWER: A
    """
    try:
        doc = Document(file_obj)
    except Exception:
        raise ValueError("File Word lỗi hoặc không đúng định dạng .docx")

    questions_list = []
    current_q = None
    
    # Regex Patterns (Biên dịch 1 lần để tối ưu)
    # Bắt dòng: "Câu 1: ...", "1. ...", "Question 1: ..."
    question_pattern = re.compile(r'^(Câu|Question)?\s*\d+[\.:]\s*(.+)', re.IGNORECASE)
    # Bắt dòng options: "A. ...", "a) ..."
    option_pattern = re.compile(r'^([A-D])[\.\)]\s*(.+)', re.IGNORECASE)
    # Bắt dòng đáp án: "ANSWER: A", "ĐÁP ÁN: A"
    answer_pattern = re.compile(r'^(ANSWER|ĐÁP ÁN|DAP AN|RESULT):\s*([A-D])', re.IGNORECASE)

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text: continue

        # 1. Bắt đầu câu hỏi mới
        q_match = question_pattern.match(text)
        if q_match:
            # Lưu câu trước đó nếu có
            if current_q:
                _finalize_question_to_list(current_q, questions_list)
            
            # Khởi tạo câu mới
            current_q = {
                "text": q_match.group(2).strip(),
                "options": [],
                "correct_char": None
            }
            continue

        # 2. Bắt Options
        opt_match = option_pattern.match(text)
        if current_q and opt_match:
            char = opt_match.group(1).upper()
            content = opt_match.group(2).strip()
            current_q["options"].append({"id": char, "text": content})
            continue

        # 3. Bắt Đáp án
        ans_match = answer_pattern.match(text)
        if current_q and ans_match:
            current_q["correct_char"] = ans_match.group(2).upper()
            continue
        
        # (Optional) Nối dòng nếu câu hỏi dài nhiều dòng
        # if current_q and not opt_match and not ans_match:
        #     current_q["text"] += "\n" + text

    # Lưu câu cuối cùng
    if current_q:
        _finalize_question_to_list(current_q, questions_list)
        
    return questions_list


def _finalize_question_to_list(raw_q, output_list):
    # ... (Logic map dữ liệu y hệt cũ) ...
    # Append vào list dict thay vì list object model
    output_list.append({
        "id": None,
        "type": "multiple_choice_single",
        "prompt": {
            "text": raw_q["text"],
            "options": raw_q["options"]
        },
        "answer_payload": {
            "correct_ids": [raw_q["correct_char"]]
        },
        "position": len(output_list) + 1
    })