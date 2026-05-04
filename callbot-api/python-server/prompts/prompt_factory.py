"""
Factory để tạo prompt cho từng tiêu chí đánh giá
Sử dụng LangChain ChatPromptTemplate
"""

from langchain_core.prompts import ChatPromptTemplate
from .base_prompt import (
    DOMAIN_GLOSSARY,
    SELF_CONSISTENCY_RULES,
    OUTPUT_WARNING,
    CONFIDENCE_GUIDELINES,
    ERROR_SEVERITY_GUIDELINES,
    JSON_OUTPUT_FORMAT,
    create_base_context
)


def get_standard_prompt() -> str:
    """Tiêu chí Chuẩn - Cân bằng"""
    return """Bạn là chuyên gia kiểm thử chatbot hành chính công. Đánh giá theo tiêu chí CHUẨN.

{context}

{domain_glossary}

## SCORING RUBRIC
Chấm điểm 0-100 cho 3 thành phần:

**Content Score (0-100):**
• 100: 100% thông tin kỳ vọng + 100% chính xác
• 80-99: 100% thông tin nhưng có chi tiết nhỏ không chính xác
• 60-79: 80-99% thông tin quan trọng
• 40-59: 60-79% thông tin quan trọng
• 20-39: 40-59% thông tin quan trọng
• 0-19: <40% thông tin hoặc thông tin sai nghiêm trọng

**Tone Score (0-100):**
• 100: Xưng hô + dạ/ạ + tự nhiên + thân thiện
• 80-99: Xưng hô + dạ/ạ nhưng hơi máy móc
• 60-79: Có xưng hô nhưng thiếu dạ/ạ
• 40-59: Thiếu xưng hô nhưng có dạ/ạ
• 20-39: Không xưng hô và không dạ/ạ
• 0-19: Thô lỗ hoặc không phù hợp

**Time Score (0-100):**
• 100: ≤2s
• 70: ≤3s
• 40: ≤5s
• 0: >5s

**Total Score = content_score × 0.5 + tone_score × 0.3 + time_score × 0.2**
**PASSED nếu total_score ≥ 70, FAILED nếu < 70**

{self_consistency}

## SUY LUẬN (bắt buộc)
Hãy phân tích từng bước:
1. **Content Score**: Liệt kê thông tin kỳ vọng → Liệt kê thông tin thực tế → Tính % đầy đủ và chính xác → Chấm điểm /100
2. **Tone Score**: Có xưng hô? Có dạ/ạ? Tự nhiên? Thân thiện? → Chấm điểm /100
3. **Time Score**: Thời gian bao nhiêu? → Chấm điểm /100 theo rubric
4. **Total Score**: Tính theo công thức (content×0.5 + tone×0.3 + time×0.2)
5. **Verdict**: total_score ≥70 → PASSED, <70 → FAILED
6. **Self-check**: Kiểm tra tính nhất quán theo rules

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


def get_strict_prompt() -> str:
    """Tiêu chí Nghiêm ngặt"""
    return """Bạn là chuyên gia kiểm thử RẤT KHÓ TÍNH. Đánh giá theo tiêu chí NGHIÊM NGẶT.

{context}

{domain_glossary}

## SCORING RUBRIC (NGHIÊM NGẶT)
Chấm điểm 0-100 cho 3 thành phần:

**Content Score (0-100) - Rất khắt khe:**
• 100: 100% thông tin + 100% chính xác + không thiếu chi tiết nào
• 90-99: 100% thông tin nhưng có 1 chi tiết nhỏ không hoàn hảo
• 80-89: 95-99% thông tin
• 60-79: 90-94% thông tin
• 40-59: 80-89% thông tin
• 0-39: <80% thông tin

**Tone Score (0-100) - Yêu cầu hoàn hảo:**
• 100: Xưng hô + dạ/ạ + tự nhiên + thân thiện + hoàn hảo
• 90-99: Xưng hô + dạ/ạ + tự nhiên nhưng hơi máy móc
• 80-89: Xưng hô + dạ/ạ nhưng thiếu tự nhiên
• 60-79: Có xưng hô nhưng thiếu dạ/ạ
• 40-59: Thiếu xưng hô
• 0-39: Không xưng hô, không dạ/ạ

**Time Score (0-100) - Yêu cầu nhanh:**
• 100: ≤2s
• 50: ≤2.5s
• 0: >2.5s

**Total Score = content_score × 0.4 + tone_score × 0.4 + time_score × 0.2**
**PASSED nếu total_score ≥ 85, FAILED nếu < 85**

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


def get_flexible_prompt() -> str:
    """Tiêu chí Linh hoạt"""
    return """Bạn là chuyên gia kiểm thử KHOAN DUNG. Đánh giá theo tiêu chí LINH HOẠT.

{context}

{domain_glossary}

## SCORING RUBRIC (LINH HOẠT)
Chấm điểm 0-100 cho 3 thành phần:

**Content Score (0-100) - Khoan dung hơn:**
• 100: ≥90% thông tin quan trọng + chính xác
• 80-99: 80-89% thông tin quan trọng
• 60-79: 70-79% thông tin quan trọng (chấp nhận được)
• 40-59: 60-69% thông tin quan trọng
• 20-39: 40-59% thông tin
• 0-19: <40% thông tin hoặc sai nghiêm trọng

**Tone Score (0-100) - Khoan dung:**
• 100: Xưng hô + dạ/ạ + tự nhiên
• 80-99: Có xưng hô hoặc dạ/ạ (không cần cả hai)
• 60-79: Lịch sự cơ bản, không thô lỗ
• 40-59: Hơi máy móc nhưng chấp nhận được
• 20-39: Máy móc, cộc lốc
• 0-19: Thô lỗ

**Time Score (0-100):**
• 100: ≤2s
• 80: ≤3s
• 60: ≤5s (chấp nhận được)
• 30: ≤7s
• 0: >7s

**Total Score = content_score × 0.6 + tone_score × 0.2 + time_score × 0.2**
**PASSED nếu total_score ≥ 60, FAILED nếu < 60**

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


def get_content_only_prompt() -> str:
    """Tiêu chí Nội dung - Chỉ đánh giá content"""
    return """Bạn là chuyên gia kiểm thử. ĐÁNH GIÁ CHỈ NỘI DUNG.

{context}

{domain_glossary}

## SCORING RUBRIC (CONTENT-ONLY)
Chấm điểm 0-100 cho 3 thành phần:

**Content Score (0-100) - QUAN TRỌNG NHẤT:**
• 100: 100% thông tin kỳ vọng + 100% chính xác
• 80-99: 100% thông tin nhưng có chi tiết nhỏ không chính xác
• 60-79: 80-99% thông tin quan trọng
• 40-59: 60-79% thông tin quan trọng
• 20-39: 40-59% thông tin
• 0-19: <40% thông tin hoặc sai nghiêm trọng

**Tone Score (0-100) - BỎ QUA:**
• Luôn cho 100 điểm (không đánh giá giọng điệu)

**Time Score (0-100):**
• 100: ≤2s
• 70: ≤3s
• 40: ≤5s
• 0: >5s

**Total Score = content_score × 0.8 + tone_score × 0.0 + time_score × 0.2**
**PASSED nếu total_score ≥ 70, FAILED nếu < 70**

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


def get_ux_focused_prompt() -> str:
    """Tiêu chí Trải nghiệm - Ưu tiên UX"""
    return """Bạn là chuyên gia UX/CX. ĐÁNH GIÁ TRẢI NGHIỆM NGƯỜI DÙNG.

{context}

{domain_glossary}

## SCORING RUBRIC (UX-FOCUSED)
Chấm điểm 0-100 cho 3 thành phần:

**Content Score (0-100) - Chỉ cần ≥70%:**
• 100: ≥90% thông tin
• 80-99: 80-89% thông tin
• 70-79: 70-79% thông tin (đủ tốt)
• 50-69: 60-69% thông tin
• 30-49: 50-59% thông tin
• 0-29: <50% thông tin

**Tone Score (0-100) - QUAN TRỌNG NHẤT:**
• 100: Xưng hô + dạ/ạ + tự nhiên + thân thiện + ấm áp
• 90-99: Xưng hô + dạ/ạ + tự nhiên
• 80-89: Xưng hô + dạ/ạ nhưng hơi máy móc
• 70-79: Có xưng hô hoặc dạ/ạ
• 50-69: Lịch sự cơ bản
• 0-49: Máy móc, cộc lốc, thô lỗ

**Time Score (0-100):**
• 100: ≤2s
• 70: ≤3s
• 40: ≤5s
• 0: >5s

**Total Score = content_score × 0.3 + tone_score × 0.5 + time_score × 0.2**
**PASSED nếu total_score ≥ 70, FAILED nếu < 70**

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


# Mapping từ criteria name đến prompt function
PROMPT_MAP = {
    "standard": get_standard_prompt,
    "strict": get_strict_prompt,
    "flexible": get_flexible_prompt,
    "content-only": get_content_only_prompt,
    "ux-focused": get_ux_focused_prompt,
}


def create_judge_prompt(
    criteria: str,
    question: str,
    expected: str,
    actual: str,
    group: str,
    time_label: str
) -> ChatPromptTemplate:
    """
    Tạo prompt template cho LLM judge
    
    Args:
        criteria: Tiêu chí đánh giá
        question: Câu hỏi
        expected: Câu trả lời kỳ vọng
        actual: Câu trả lời thực tế
        group: Nhóm testcase
        time_label: Label thời gian (vd: "1500ms (Nhanh)")
        
    Returns:
        ChatPromptTemplate đã format
    """
    # Lấy prompt function
    prompt_func = PROMPT_MAP.get(criteria, PROMPT_MAP["standard"])
    prompt_template = prompt_func()
    
    # Format prompt với các biến
    context = create_base_context(question, expected, actual, group, time_label)
    
    formatted_prompt = prompt_template.format(
        context=context,
        domain_glossary=DOMAIN_GLOSSARY,
        self_consistency=SELF_CONSISTENCY_RULES,
        output_warning=OUTPUT_WARNING,
        confidence_guidelines=CONFIDENCE_GUIDELINES,
        error_severity=ERROR_SEVERITY_GUIDELINES,
        json_output=JSON_OUTPUT_FORMAT
    )
    
    # Tạo ChatPromptTemplate
    return ChatPromptTemplate.from_messages([
        ("user", formatted_prompt)
    ])
