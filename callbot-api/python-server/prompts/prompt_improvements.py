"""
Prompt Improvements - Grounding, Error Analysis, Optimization
Các cải tiến để giảm hallucination và tăng chất lượng đánh giá
"""

# ═══════════════════════════════════════════════════════════
# GROUNDING REQUIREMENT - Đã thêm vào simple_prompt.py
# ═══════════════════════════════════════════════════════════

# Đã implement trong simple_prompt.py


# ═══════════════════════════════════════════════════════════
# ERROR ANALYSIS TEMPLATE - Phân tích lỗi có cấu trúc
# ═══════════════════════════════════════════════════════════

ERROR_ANALYSIS_TEMPLATE = """
═══════════════════════════════════════════════════════════
TEMPLATE PHÂN TÍCH LỖI (Error Analysis) - CHI TIẾT
═══════════════════════════════════════════════════════════

**KHI NÀO DÙNG:** Chỉ khi verdict = "FAILED"

**FORMAT BẮT BUỘC:** Với MỖI lỗi, trả lời 5 câu hỏi:

## 1. LỖI GÌ? (What)
- Loại: [Thiếu thông tin / Sai thông tin / Không rõ ràng / Vi phạm keywords]
- Thông tin cụ thể: [Tên thông tin bị lỗi]

## 2. Ở ĐÂU? (Where)
- Vị trí trong response: [Đầu / Giữa / Cuối / Hoàn toàn không có]
- Context xung quanh: [Trích dẫn đoạn text xung quanh lỗi]

## 3. TÁC ĐỘNG GÌ? (Impact)
- Đến user: [User không hiểu X / User không làm được Y / User hiểu sai Z]
- Mức độ ảnh hưởng: [Cao / Trung bình / Thấp]

## 4. MỨC ĐỘ NGHIÊM TRỌNG? (Severity)
- **Critical:** Thông tin CỐT LÕI thiếu/sai → User không thể hoàn thành thủ tục
- **Major:** Thông tin QUAN TRỌNG thiếu/sai → User gặp khó khăn lớn
- **Minor:** Thông tin PHỤ thiếu/sai → User hơi bất tiện

## 5. SỬA NHƯ THẾ NÀO? (How to Fix)
- Hành động: [Bổ sung / Sửa / Xóa / Di chuyển]
- Vị trí: [Sau câu "..." / Trước đoạn "..." / Thay thế "..."]
- Nội dung cụ thể: [Thêm câu "..." / Sửa từ "X" thành "Y"]
- Ví dụ: [Câu hoàn chỉnh sau khi sửa]

═══════════════════════════════════════════════════════════
VÍ DỤ PHÂN TÍCH LỖI HOÀN CHỈNH
═══════════════════════════════════════════════════════════

**LỖI #1: Thiếu thông tin về lệ phí**

1. LỖI GÌ?
   - Loại: Thiếu thông tin
   - Thông tin: Lệ phí

2. Ở ĐÂU?
   - Vị trí: Hoàn toàn không có
   - Context: Response chỉ nói "Cần CMND, hộ khẩu" rồi kết thúc

3. TÁC ĐỘNG GÌ?
   - Đến user: User không biết phải trả bao nhiêu tiền
   - Mức độ: Cao (user có thể không chuẩn bị đủ tiền)

4. MỨC ĐỘ NGHIÊM TRỌNG?
   - **Major** (thông tin quan trọng, ảnh hưởng trực tiếp đến việc chuẩn bị)

5. SỬA NHƯ THẾ NÀO?
   - Hành động: Bổ sung
   - Vị trí: Sau câu "Cần CMND, hộ khẩu"
   - Nội dung: Thêm câu "Lệ phí là 500.000đ"
   - Ví dụ: "Cần CMND, hộ khẩu. Lệ phí là 500.000đ."

---

**LỖI #2: Sai thông tin về thời gian**

1. LỖI GÌ?
   - Loại: Sai thông tin
   - Thông tin: Thời gian xử lý

2. Ở ĐÂU?
   - Vị trí: Cuối response
   - Context: "...Thời gian xử lý khoảng 30 ngày"

3. TÁC ĐỘNG GÌ?
   - Đến user: User hiểu sai thời gian (thực tế 15 ngày, không phải 30)
   - Mức độ: Cao (user có thể lên lịch sai)

4. MỨC ĐỘ NGHIÊM TRỌNG?
   - **Critical** (thông tin sai, gây hiểu lầm nghiêm trọng)

5. SỬA NHƯ THẾ NÀO?
   - Hành động: Sửa
   - Vị trí: Câu cuối
   - Nội dung: Sửa "30 ngày" thành "15 ngày"
   - Ví dụ: "...Thời gian xử lý khoảng 15 ngày làm việc"

═══════════════════════════════════════════════════════════
ÁP DỤNG VÀO OUTPUT JSON
═══════════════════════════════════════════════════════════

**Trong trường "errors" array:**
```json
[
  {
    "description": "Thiếu thông tin về lệ phí. Response chỉ nói 'Cần CMND, hộ khẩu' mà không đề cập đến lệ phí 500.000đ. User không biết phải chuẩn bị bao nhiêu tiền.",
    "severity": "Major",
    "quote": "Cần CMND, hộ khẩu"
  },
  {
    "description": "Sai thông tin về thời gian xử lý. Response nói '30 ngày' nhưng kỳ vọng là '15 ngày'. User có thể lên lịch sai.",
    "severity": "Critical",
    "quote": "Thời gian xử lý khoảng 30 ngày"
  }
]
```

**Trong trường "error_desc":**
```
Response có 2 lỗi nghiêm trọng:

LỖI #1 - Thiếu lệ phí (Major):
- Vị trí: Hoàn toàn không có
- Tác động: User không biết phải trả 500.000đ
- Trích dẫn: Response chỉ nói "Cần CMND, hộ khẩu"

LỖI #2 - Sai thời gian (Critical):
- Vị trí: Câu cuối
- Tác động: User hiểu sai (30 ngày thay vì 15 ngày)
- Trích dẫn: "Thời gian xử lý khoảng 30 ngày"
```

**Trong trường "suggestion":**
```
1. Bổ sung lệ phí: Thêm câu "Lệ phí là 500.000đ" sau "Cần CMND, hộ khẩu"
2. Sửa thời gian: Đổi "30 ngày" thành "15 ngày làm việc" ở câu cuối
```

**Trong trường "suggested_response":**
```
Cần CMND, hộ khẩu. Lệ phí là 500.000đ. Thời gian xử lý khoảng 15 ngày làm việc.
```

═══════════════════════════════════════════════════════════
QUY TẮC QUAN TRỌNG
═══════════════════════════════════════════════════════════

1. **MỖI lỗi phải trả lời ĐỦ 5 câu hỏi**
2. **Phải có TRÍCH DẪN cụ thể** (không chung chung)
3. **Phải chỉ rõ VỊ TRÍ** (đầu/giữa/cuối/không có)
4. **Phải có VÍ DỤ SỬA** (câu hoàn chỉnh sau khi sửa)
5. **Severity phải chính xác** (Critical/Major/Minor theo impact)
"""


# ═══════════════════════════════════════════════════════════
# PROMPT OPTIMIZATION - Rút gọn và tối ưu
# ═══════════════════════════════════════════════════════════

OPTIMIZATION_GUIDELINES = """
═══════════════════════════════════════════════════════════
HƯỚNG DẪN TỐI ƯU PROMPT
═══════════════════════════════════════════════════════════

## MỤC TIÊU:
- Giảm độ dài prompt 20-30%
- Giữ nguyên accuracy
- Tăng tốc độ xử lý

## NGUYÊN TẮC:

### 1. Loại bỏ Redundancy
❌ **TRƯỚC:**
```
Bạn phải kiểm tra thông tin. Việc kiểm tra thông tin rất quan trọng. 
Hãy kiểm tra kỹ từng thông tin.
```

✅ **SAU:**
```
Kiểm tra kỹ từng thông tin.
```

### 2. Dùng Bullet Points thay vì Văn xuôi
❌ **TRƯỚC:**
```
Khi đánh giá, bạn cần xem xét nhiều yếu tố. Đầu tiên là nội dung, 
sau đó là giọng điệu, và cuối cùng là thời gian phản hồi.
```

✅ **SAU:**
```
Đánh giá:
- Nội dung
- Giọng điệu
- Thời gian
```

### 3. Gộp Quy tắc tương tự
❌ **TRƯỚC:**
```
CMND = CCCD
CMND = Căn cước
CCCD = Căn cước
Chứng minh nhân dân = CMND
```

✅ **SAU:**
```
CMND = CCCD = Căn cước = Chứng minh nhân dân
```

### 4. Dùng Ký hiệu thay vì Chữ
❌ **TRƯỚC:**
```
Nếu có thông tin → đánh dấu là có
Nếu không có thông tin → đánh dấu là không có
Nếu tương đương → đánh dấu là tương đương
```

✅ **SAU:**
```
Có: ✓ | Không: ✗ | Tương đương: ≈
```

### 5. Loại bỏ Ví dụ trùng lặp
- Giữ 3-5 ví dụ đại diện
- Loại bỏ ví dụ tương tự nhau
- Mỗi ví dụ phải cover 1 pattern khác nhau

### 6. Rút gọn Hướng dẫn
❌ **TRƯỚC:**
```
Bạn cần phải đọc kỹ câu hỏi, sau đó đọc kỳ vọng, rồi đọc thực tế,
và so sánh giữa kỳ vọng với thực tế để đưa ra đánh giá.
```

✅ **SAU:**
```
Đọc → So sánh → Đánh giá
```

## KẾT QUẢ MONG ĐỢI:

**TRƯỚC tối ưu:**
- Prompt length: ~5000 tokens
- Processing time: ~3-4s
- Cost: $0.015/request

**SAU tối ưu:**
- Prompt length: ~3500 tokens (-30%)
- Processing time: ~2-3s (-25%)
- Cost: $0.010/request (-33%)

**Accuracy:** Giữ nguyên hoặc tăng nhẹ (nhờ rõ ràng hơn)
"""


# ═══════════════════════════════════════════════════════════
# CONSISTENCY CHECK - Kiểm tra tính nhất quán
# ═══════════════════════════════════════════════════════════

CONSISTENCY_CHECK = """
═══════════════════════════════════════════════════════════
KIỂM TRA NHẤT QUÁN (Consistency Check) - TRƯỚC KHI OUTPUT
═══════════════════════════════════════════════════════════

**MỤC ĐÍCH:** Đảm bảo output JSON nhất quán, không mâu thuẫn

## CHECKLIST BẮT BUỘC:

### 1. Verdict vs Error Fields
```python
if verdict == "PASSED":
    assert errors == []
    assert error_desc == ""
    assert suggestion == ""
    assert suggested_response == ""
    
if verdict == "FAILED":
    assert len(errors) > 0
    assert error_desc != ""
    assert suggestion != ""
    assert suggested_response != ""
```

### 2. Reasoning vs Verdict
```python
if "đủ thông tin" in reasoning or "100%" in reasoning:
    assert verdict == "PASSED"
    
if "thiếu thông tin" in reasoning or "<90%" in reasoning:
    assert verdict == "FAILED"
```

### 3. Confidence vs Human Review
```python
if confidence_level < 0.7:
    assert needs_human_review == True
    assert confidence_reason != ""
    
if confidence_level >= 0.9:
    assert needs_human_review == False
```

### 4. Errors vs Error_desc
```python
if len(errors) > 0:
    # error_desc phải tóm tắt tất cả errors
    for error in errors:
        assert error["description"] in error_desc or \
               similar_meaning(error["description"], error_desc)
```

### 5. Suggestion vs Suggested_response
```python
if suggestion != "":
    # suggested_response phải áp dụng suggestion
    assert suggested_response != ""
    # Kiểm tra suggestion đã được áp dụng
    for action in parse_suggestions(suggestion):
        assert action_applied(action, suggested_response)
```

## VÍ DỤ KIỂM TRA:

**❌ KHÔNG NHẤT QUÁN:**
```json
{
  "reasoning": "Đủ 4/4 thông tin (100%)",
  "verdict": "FAILED",  // ← MÂU THUẪN!
  "errors": []
}
```

**✅ NHẤT QUÁN:**
```json
{
  "reasoning": "Đủ 4/4 thông tin (100%)",
  "verdict": "PASSED",
  "errors": []
}
```

---

**❌ KHÔNG NHẤT QUÁN:**
```json
{
  "verdict": "FAILED",
  "errors": [{"description": "Thiếu lệ phí", ...}],
  "error_desc": "",  // ← THIẾU!
  "suggestion": ""   // ← THIẾU!
}
```

**✅ NHẤT QUÁN:**
```json
{
  "verdict": "FAILED",
  "errors": [{"description": "Thiếu lệ phí", ...}],
  "error_desc": "Response thiếu thông tin về lệ phí...",
  "suggestion": "Bổ sung lệ phí..."
}
```

## TỰ ĐỘNG KIỂM TRA:

Trước khi output JSON, tự hỏi:
1. ✓ Verdict có khớp với reasoning không?
2. ✓ Nếu FAILED, có đủ error_desc/suggestion/suggested_response không?
3. ✓ Nếu PASSED, các trường error có rỗng không?
4. ✓ Confidence có khớp với needs_human_review không?
5. ✓ Errors array có khớp với error_desc không?

Nếu BẤT KỲ câu nào trả lời "KHÔNG" → SỬA LẠI trước khi output!
"""


# ═══════════════════════════════════════════════════════════
# EXPORT FUNCTIONS
# ═══════════════════════════════════════════════════════════

def get_error_analysis_template() -> str:
    """Lấy template phân tích lỗi"""
    return ERROR_ANALYSIS_TEMPLATE


def get_optimization_guidelines() -> str:
    """Lấy hướng dẫn tối ưu prompt"""
    return OPTIMIZATION_GUIDELINES


def get_consistency_check() -> str:
    """Lấy checklist kiểm tra nhất quán"""
    return CONSISTENCY_CHECK


def get_all_improvements() -> str:
    """Lấy tất cả cải tiến"""
    return f"""
{ERROR_ANALYSIS_TEMPLATE}

{OPTIMIZATION_GUIDELINES}

{CONSISTENCY_CHECK}
"""


if __name__ == "__main__":
    print("=" * 80)
    print("PROMPT IMPROVEMENTS")
    print("=" * 80)
    print("\n1. Error Analysis Template")
    print("2. Optimization Guidelines")
    print("3. Consistency Check")
    print("\nUse: from prompt_improvements import get_error_analysis_template")
