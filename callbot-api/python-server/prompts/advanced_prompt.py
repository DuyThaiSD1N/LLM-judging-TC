"""
ADVANCED JUDGE PROMPT - Nâng cấp với đánh giá động theo tiêu chí
Mỗi tiêu chí sẽ có prompt riêng, focus khác nhau, output khác nhau
"""

# ═══════════════════════════════════════════════════════════
# BASE SYSTEM MESSAGE - Chung cho tất cả
# ═══════════════════════════════════════════════════════════

BASE_SYSTEM_MESSAGE = """Bạn là chuyên gia đánh giá chatbot response cho hệ thống customer service.

NHIỆM VỤ: So sánh câu trả lời THỰC TẾ với YÊU CẦU KỲ VỌNG và đưa ra đánh giá chi tiết.

🚫 CÁC TỪ TUYỆT ĐỐI CẤM:
- "Failed:" / "FAILED:" (đặc biệt CẤM ở đầu câu)
- "Verdict:" (bất kỳ dạng nào)

✅ CÁCH VIẾT ĐÚNG:
- ❌ SAI: "Failed: Thiếu thông tin"
- ✅ ĐÚNG: "Thiếu thông tin"
"""

# ═══════════════════════════════════════════════════════════
# GROUNDING REQUIREMENT - Bắt buộc trích dẫn
# ═══════════════════════════════════════════════════════════

GROUNDING_REQUIREMENT = """
═══════════════════════════════════════════════════════════
YÊU CẦU TRÍCH DẪN (Grounding) - BẮT BUỘC
═══════════════════════════════════════════════════════════

**NGUYÊN TẮC:** Mọi đánh giá PHẢI dựa trên TRÍCH DẪN CỤ THỂ từ text.

## CÁCH TRÍCH DẪN ĐÚNG:

Thông tin: [Tên thông tin]
├─ Trong KỲ VỌNG: "[Trích dẫn chính xác]"
├─ Trong THỰC TẾ: "[Trích dẫn chính xác]" hoặc "KHÔNG CÓ"
└─ Kết luận: ✓ Có / ✗ Không / ≈ Tương đương

## VÍ DỤ:

**✓ ĐÚNG (có trích dẫn):**
Thông tin: Giấy tờ tùy thân
├─ Trong KỲ VỌNG: "Cần CMND"
├─ Trong THỰC TẾ: "Cần CCCD"
└─ Kết luận: ≈ Tương đương (CMND = CCCD)

**✗ SAI (không trích dẫn):**
Thông tin: Giấy tờ tùy thân
Kết luận: Có đề cập đến CMND
"""

# ═══════════════════════════════════════════════════════════
# FEW-SHOT EXAMPLES - Ví dụ cụ thể
# ═══════════════════════════════════════════════════════════

FEW_SHOT_EXAMPLES = """
═══════════════════════════════════════════════════════════
VÍ DỤ ĐÁNH GIÁ (Few-shot Examples)
═══════════════════════════════════════════════════════════

**VÍ DỤ 1: PASSED - Cách diễn đạt khác nhưng đủ thông tin**

Câu hỏi: "Thủ tục đăng ký kết hôn cần giấy tờ gì?"
Kỳ vọng: "Cần CMND, sổ hộ khẩu, giấy xác nhận độc thân. Nộp tại UBND phường."
Thực tế: "Dạ, anh cần chuẩn bị CCCD, giấy đăng ký hộ khẩu, xác nhận chưa kết hôn. Nộp hồ sơ tại Ủy ban nhân dân cấp xã nơi anh cư trú ạ."

Phân tích:
- CMND ≈ CCCD ✓
- Sổ hộ khẩu ≈ Giấy đăng ký hộ khẩu ✓
- Xác nhận độc thân ≈ Xác nhận chưa kết hôn ✓
- UBND phường ≈ UBND cấp xã ✓
- Đạt 4/4 (100%) → PASSED

---

**VÍ DỤ 2: FAILED - Thiếu thông tin quan trọng**

Câu hỏi: "Thủ tục cấp giấy phép xây dựng cần gì?"
Kỳ vọng: "Cần đơn xin phép, sổ đỏ, bản vẽ thiết kế, CMND. Lệ phí 500.000đ. Thời gian 15 ngày."
Thực tế: "Bạn cần nộp đơn xin phép, sổ đỏ và CMND."

Phân tích:
- Đơn xin phép ✓
- Sổ đỏ ✓
- Bản vẽ thiết kế ✗ (THIẾU)
- CMND ✓
- Lệ phí ✗ (THIẾU)
- Thời gian ✗ (THIẾU)
- Đạt 3/6 (50%) → FAILED

---

**VÍ DỤ 3: FAILED - Vi phạm từ khóa CẤM**

Câu hỏi: "Thủ tục đăng ký xe máy cần gì?"
Kỳ vọng: "Cần hóa đơn mua xe, CMND, giấy chứng nhận chất lượng."
Từ khóa CẤM: "bảo hiểm, đăng kiểm"
Thực tế: "Cần hóa đơn, CMND, giấy chất lượng, và bảo hiểm xe."

Phân tích:
- Thông tin đủ: 3/3 ✓
- Từ khóa CẤM: "bảo hiểm" xuất hiện ✗
- Vi phạm từ khóa cấm → FAILED
"""

# ═══════════════════════════════════════════════════════════
# CRITERIA-SPECIFIC PROMPTS
# ═══════════════════════════════════════════════════════════

CRITERIA_PROMPTS = {
    "standard": {
        "name": "Tiêu chí Chuẩn",
        "focus": "Cân bằng: ≥90% thông tin, giọng điệu lịch sự, thời gian ≤3s",
        "system_instruction": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: CHUẨN (Cân bằng)
═══════════════════════════════════════════════════════════

BẠN ĐÁNH GIÁ THEO TIÊU CHÍ CÂN BẰNG:
- Nội dung: ≥90% thông tin kỳ vọng
- Giọng điệu: Lịch sự, tôn trọng (không bắt buộc xưng hô)
- Thời gian: ≤3s là tốt

QUYẾT ĐỊNH:
- PASSED: ≥90% thông tin + không vi phạm keywords + giọng điệu lịch sự
- FAILED: <90% thông tin HOẶC vi phạm keywords HOẶC giọng điệu thô lỗ

CÁCH VIẾT REASONING:
1. Liệt kê tất cả thông tin trong kỳ vọng
2. Kiểm tra từng thông tin có trong response không
3. Tính % = (có / tổng) × 100
4. Kiểm tra keywords
5. Đánh giá giọng điệu
6. Quyết định PASSED/FAILED với lý do cụ thể
""",
        "error_focus": "Tập trung vào thông tin thiếu/sai và cách sửa",
        "suggestion_style": "Đề xuất cách bổ sung thông tin thiếu một cách tự nhiên"
    },
    
    "strict": {
        "name": "Tiêu chí Nghiêm ngặt",
        "focus": "Yêu cầu cao: ≥95% thông tin, giọng điệu tự nhiên + xưng hô, thời gian ≤2s",
        "system_instruction": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: NGHIÊM NGẶT (Yêu cầu cao)
═══════════════════════════════════════════════════════════

BẠN ĐÁNH GIÁ THEO TIÊU CHÍ NGHIÊM NGẶT:
- Nội dung: ≥95% thông tin kỳ vọng (yêu cầu cao)
- Giọng điệu: PHẢI có xưng hô + lịch sự + tự nhiên
- Thời gian: ≤2s là tốt, >3s là FAILED

QUYẾT ĐỊNH:
- PASSED: ≥95% thông tin + ≤3s + có xưng hô + không vi phạm keywords
- FAILED: <95% thông tin HOẶC >3s HOẶC thiếu xưng hô HOẶC vi phạm keywords

CÁCH VIẾT REASONING:
1. Liệt kê tất cả thông tin trong kỳ vọng (chi tiết)
2. Kiểm tra từng thông tin có trong response không
3. Tính % = (có / tổng) × 100
4. Kiểm tra thời gian (bắt buộc ≤3s)
5. Kiểm tra xưng hô (bắt buộc có)
6. Kiểm tra keywords
7. Quyết định PASSED/FAILED với lý do cụ thể
8. Ghi nhận BẤT KỲ lỗi nhỏ nào
""",
        "error_focus": "Ghi nhận chi tiết mọi lỗi, kể cả lỗi nhỏ",
        "suggestion_style": "Đề xuất cách sửa từng lỗi một cách cụ thể"
    },
    
    "speed-focused": {
        "name": "Tiêu chí Tốc độ",
        "focus": "Ưu tiên nhanh: thời gian ≤2s (bắt buộc), ≥80% thông tin",
        "system_instruction": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: TỐC ĐỘ (Ưu tiên nhanh)
═══════════════════════════════════════════════════════════

BẠN ĐÁNH GIÁ THEO TIÊU CHÍ TỐC ĐỘ:
- Thời gian: ≤2s là bắt buộc (FAILED nếu >2s)
- Nội dung: ≥80% thông tin kỳ vọng (yêu cầu thấp hơn)
- Giọng điệu: KHÔNG đánh giá

QUYẾT ĐỊNH:
- PASSED: ≤2s + ≥80% thông tin + không vi phạm keywords
- FAILED: >2s HOẶC <80% thông tin HOẶC vi phạm keywords

CÁCH VIẾT REASONING:
1. Kiểm tra thời gian TRƯỚC (bắt buộc ≤2s)
2. Nếu >2s → FAILED ngay (không cần kiểm tra nội dung)
3. Nếu ≤2s → Kiểm tra nội dung
4. Liệt kê thông tin trong kỳ vọng
5. Kiểm tra từng thông tin có trong response không
6. Tính % = (có / tổng) × 100
7. Kiểm tra keywords
8. Quyết định PASSED/FAILED với lý do cụ thể
9. KHÔNG ghi nhận vấn đề giọng điệu
""",
        "error_focus": "Tập trung vào thời gian quá chậm hoặc thông tin thiếu",
        "suggestion_style": "Đề xuất cách trả lời nhanh hơn hoặc bổ sung thông tin thiếu"
    },
    
    "content-only": {
        "name": "Tiêu chí Nội dung",
        "focus": "Chỉ độ chính xác: ≥95% thông tin, bỏ qua thời gian & giọng điệu",
        "system_instruction": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: NỘI DUNG (Chỉ độ chính xác)
═══════════════════════════════════════════════════════════

BẠN ĐÁNH GIÁ THEO TIÊU CHÍ NỘI DUNG:
- Nội dung: ≥95% thông tin kỳ vọng (yêu cầu cao)
- Thời gian: KHÔNG đánh giá
- Giọng điệu: KHÔNG đánh giá

QUYẾT ĐỊNH:
- PASSED: ≥95% thông tin + không vi phạm keywords
- FAILED: <95% thông tin HOẶC vi phạm keywords

CÁCH VIẾT REASONING:
1. Liệt kê tất cả thông tin trong kỳ vọng
2. Kiểm tra từng thông tin có trong response không
3. Tính % = (có / tổng) × 100
4. Kiểm tra keywords
5. Quyết định PASSED/FAILED với lý do cụ thể
6. KHÔNG ghi nhận vấn đề thời gian
7. KHÔNG ghi nhận vấn đề giọng điệu
8. CHỈ tập trung vào độ chính xác nội dung
""",
        "error_focus": "Tập trung vào thông tin sai/thiếu, bỏ qua thời gian & giọng",
        "suggestion_style": "Đề xuất cách sửa thông tin sai/thiếu"
    },
    
    "ux-focused": {
        "name": "Tiêu chí Trải nghiệm",
        "focus": "Ưu tiên thân thiện: giọng điệu + xưng hô (bắt buộc), ≥85% thông tin",
        "system_instruction": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: TRẢI NGHIỆM (Ưu tiên thân thiện)
═══════════════════════════════════════════════════════════

BẠN ĐÁNH GIÁ THEO TIÊU CHÍ TRẢI NGHIỆM:
- Giọng điệu: PHẢI có xưng hô + lịch sự + thân thiện (bắt buộc)
- Nội dung: ≥85% thông tin kỳ vọng
- Thời gian: ≤3s là tốt (không bắt buộc)

QUYẾT ĐỊNH:
- PASSED: Có xưng hô + lịch sự + ≥85% thông tin + không vi phạm keywords
- FAILED: Thiếu xưng hô HOẶC thô lỗ HOẶC <85% thông tin HOẶC vi phạm keywords

CÁCH VIẾT REASONING:
1. Kiểm tra giọng điệu TRƯỚC (bắt buộc có xưng hô)
2. Nếu thiếu xưng hô hoặc thô lỗ → FAILED ngay
3. Nếu giọng điệu OK → Kiểm tra nội dung
4. Liệt kê thông tin trong kỳ vọng
5. Kiểm tra từng thông tin có trong response không
6. Tính % = (có / tổng) × 100
7. Kiểm tra keywords
8. Quyết định PASSED/FAILED với lý do cụ thể
9. Ghi nhận điểm tích cực về giọng điệu (nếu tốt)
""",
        "error_focus": "Tập trung vào giọng điệu (xưng hô, thân thiện) và thông tin thiếu",
        "suggestion_style": "Đề xuất cách trả lời thân thiện hơn + bổ sung thông tin thiếu"
    }
}

# ═══════════════════════════════════════════════════════════
# DYNAMIC PROMPT BUILDER
# ═══════════════════════════════════════════════════════════

def create_advanced_judge_prompt(
    question: str,
    expected: str,
    actual: str,
    time_label: str,
    criteria: str = "standard",
    required_keywords: str = None,
    forbidden_keywords: str = None
) -> str:
    """
    Tạo prompt động cho judge dựa trên tiêu chí
    
    Args:
        question: Câu hỏi
        expected: Yêu cầu kỳ vọng
        actual: Câu trả lời thực tế
        time_label: Thời gian (VD: "2000ms")
        criteria: Tiêu chí (standard/strict/speed-focused/content-only/ux-focused)
        required_keywords: Từ khóa bắt buộc
        forbidden_keywords: Từ khóa cấm
    """
    
    # Get criteria-specific config
    criteria_config = CRITERIA_PROMPTS.get(criteria, CRITERIA_PROMPTS["standard"])
    
    # Build keywords section
    keywords_section = ""
    if required_keywords:
        keywords_section += f"\n**Từ khóa BẮT BUỘC:** {required_keywords}"
    if forbidden_keywords:
        keywords_section += f"\n**Từ khóa CẤM:** {forbidden_keywords}"
    
    # Build the complete prompt
    prompt = f"""{BASE_SYSTEM_MESSAGE}

{GROUNDING_REQUIREMENT}

{FEW_SHOT_EXAMPLES}

{criteria_config['system_instruction']}

═══════════════════════════════════════════════════════════
DỮ LIỆU CẦN ĐÁNH GIÁ
═══════════════════════════════════════════════════════════

**Câu hỏi:** {question}

**Yêu cầu kỳ vọng:** {expected}
{keywords_section}

**Thực tế:** {actual}

**Thời gian:** {time_label}

═══════════════════════════════════════════════════════════
YÊU CẦU OUTPUT (JSON)
═══════════════════════════════════════════════════════════

Trả về JSON với các trường:

1. **reasoning**: Suy luận chi tiết theo hướng dẫn của tiêu chí
   - Làm theo đúng "CÁCH VIẾT REASONING" ở trên
   - Phải cụ thể, có trích dẫn, có số liệu

2. **verdict**: "PASSED" hoặc "FAILED"

3. **confidence_level**: 0.0-1.0 (độ tự tin)

4. **needs_human_review**: true/false

5. **confidence_reason**: Lý do về độ tự tin

6. **errors**: Array các lỗi (nếu có)
   - description: Mô tả lỗi
   - severity: "Critical" / "Major" / "Minor"
   - quote: Trích dẫn phần sai

7. **error_desc**: Nhận xét lỗi (nếu FAILED)
   - Nếu PASSED → ""
   - Nếu FAILED → Mô tả tự nhiên, KHÔNG liệt kê dạng "thiếu X/Y"
   - Focus: {criteria_config['error_focus']}

8. **suggestion**: Gợi ý cải thiện (nếu FAILED)
   - Nếu PASSED → ""
   - Nếu FAILED → Gợi ý cụ thể
   - Style: {criteria_config['suggestion_style']}

9. **suggested_response**: Mẫu response đã sửa (nếu FAILED)
   - Nếu PASSED → ""
   - Nếu FAILED → Response hoàn chỉnh, có thể copy-paste

10. **tone_note**: Nhận xét giọng điệu
    - Nếu tốt → ""
    - Nếu có vấn đề → Mô tả cụ thể
    - Tiêu chí {criteria}: {('Bắt buộc kiểm tra' if criteria in ['strict', 'ux-focused'] else 'Không bắt buộc')}

11. **time_verdict**: "good" / "ok" / "slow"
    - Tiêu chí {criteria}: {('Bắt buộc ≤2s' if criteria == 'speed-focused' else ('Bắt buộc ≤3s' if criteria in ['standard', 'ux-focused'] else 'Không đánh giá'))}

12. **time_note**: Nhận xét thời gian

═══════════════════════════════════════════════════════════
LƯU Ý QUAN TRỌNG
═══════════════════════════════════════════════════════════

✅ PHẢI LÀM:
- Áp dụng ĐÚNG tiêu chí: {criteria_config['name']}
- Viết reasoning theo hướng dẫn của tiêu chí
- Trích dẫn cụ thể từ text
- Tính % thông tin chính xác
- Ghi nhận chi tiết lỗi (nếu có)

🚫 TUYỆT ĐỐI KHÔNG:
- Dùng "Failed:", "Verdict:", "PASSED/FAILED" trong error_desc/suggestion
- Khen ngợi trong tone_note
- Để trống error_desc/suggestion khi verdict=FAILED
- Đánh giá những yếu tố không liên quan đến tiêu chí

**TIÊU CHÍ ĐƯỢC CHỌN: {criteria_config['name']}**
**FOCUS: {criteria_config['focus']}**
"""
    
    return prompt


def get_criteria_info(criteria: str) -> dict:
    """Lấy thông tin tiêu chí"""
    return CRITERIA_PROMPTS.get(criteria, CRITERIA_PROMPTS["standard"])
