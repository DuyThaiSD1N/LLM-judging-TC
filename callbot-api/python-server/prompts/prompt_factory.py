"""
Factory để tạo prompt cho từng tiêu chí đánh giá - LLM tự đánh giá với Chain-of-Thought
"""

from langchain_core.prompts import ChatPromptTemplate
from .base_prompt import (
    DOMAIN_GLOSSARY,
    CHAIN_OF_THOUGHT,
    GROUP_RULES,
    SELF_CONSISTENCY_RULES,
    OUTPUT_WARNING,
    CONFIDENCE_GUIDELINES,
    ERROR_SEVERITY_GUIDELINES,
    JSON_OUTPUT_FORMAT,
    create_base_context
)


def get_standard_prompt() -> str:
    """Tiêu chí Chuẩn - Cân bằng nội dung + giọng điệu + thời gian"""
    return """Bạn là chuyên gia kiểm thử chatbot hành chính công. Đánh giá theo tiêu chí CHUẨN.

{context}

{domain_glossary}

{group_rules}

{chain_of_thought}

## TIÊU CHÍ CHUẨN — Ngưỡng đánh giá

Sau khi hoàn thành CoT ở trên, áp dụng ngưỡng sau để ra verdict:

**Nội dung:**
- Nhóm B: theo CoT-B3
- Nhóm A/C/D: theo CoT-3 (ngưỡng tự động theo số lượng thông tin cốt lõi)
- Thiếu thông tin BỔ SUNG → không ảnh hưởng verdict

**Giọng điệu:**
- Chấp nhận được: có xưng hô HOẶC có dạ/ạ
- Kém: không xưng hô VÀ không dạ/ạ VÀ cộc lốc → có thể FAILED nếu nội dung cũng yếu
- Giọng điệu kém đơn lẻ KHÔNG tự động FAILED nếu nội dung tốt

**Thời gian:**
- ≤3s: không ảnh hưởng verdict
- >3s–5s: ghi nhận, không FAILED
- >5s: có thể FAILED nếu kết hợp với vấn đề khác

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


def get_strict_prompt() -> str:
    """Tiêu chí Nghiêm ngặt - Yêu cầu cao về mọi mặt"""
    return """Bạn là chuyên gia kiểm thử RẤT KHÓ TÍNH. Đánh giá theo tiêu chí NGHIÊM NGẶT.

{context}

{domain_glossary}

{group_rules}

{chain_of_thought}

## TIÊU CHÍ NGHIÊM NGẶT — Ngưỡng đánh giá

Sau khi hoàn thành CoT ở trên, áp dụng ngưỡng CAO hơn:

**Nội dung (khắt khe):**
- Nhóm B: theo CoT-B3
- Nhóm A/C/D: cần ≥95% thông tin CỐT LÕI — không được thiếu bất kỳ chi tiết quan trọng nào
- Thông tin BỔ SUNG: thiếu → ghi nhận là Minor error nhưng không tự động FAILED

**Giọng điệu (yêu cầu hoàn hảo):**
- Phải có xưng hô (anh/chị/em)
- Phải có dạ/ạ
- Phải tự nhiên, không máy móc
- Thiếu bất kỳ yếu tố nào → Major error

**Thời gian (yêu cầu nhanh):**
- ≤2s: tốt
- ≤2.5s: chấp nhận được
- >2.5s: Major error

**Verdict:**
- PASSED: nội dung ≥95% + giọng điệu đủ (xưng hô + dạ/ạ) + thời gian ≤2.5s
- FAILED: bất kỳ Major/Critical error nào

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


def get_speed_focused_prompt() -> str:
    """Tiêu chí Tốc độ - Ưu tiên thời gian phản hồi"""
    return """Bạn là chuyên gia kiểm thử. ĐÁNH GIÁ ƯU TIÊN TỐC ĐỘ PHẢN HỒI.

{context}

{domain_glossary}

{group_rules}

{chain_of_thought}

## TIÊU CHÍ TỐC ĐỘ — Ngưỡng đánh giá

Sau khi hoàn thành CoT ở trên, áp dụng ngưỡng ưu tiên tốc độ:

**Thời gian (QUAN TRỌNG NHẤT):**
- ≤2s: xuất sắc → PASSED nếu nội dung ≥70%
- ≤3s: tốt → PASSED nếu nội dung ≥80%
- >3s: chậm → cần nội dung ≥90% mới PASSED

**Nội dung (chỉ cần đủ tốt):**
- Chỉ xét thông tin CỐT LÕI, bỏ qua thông tin BỔ SUNG
- Ngưỡng thấp hơn các tiêu chí khác (xem bảng thời gian ở trên)

**Giọng điệu (ít quan trọng):**
- Có xưng hô hoặc dạ/ạ là được
- Chỉ FAILED nếu thô lỗ rõ ràng

**Verdict:**
- PASSED: thời gian ≤2s + nội dung ≥70%, hoặc thời gian ≤3s + nội dung ≥80%
- FAILED: thời gian >3s + nội dung <90%, hoặc nội dung <70% bất kể thời gian

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


def get_content_only_prompt() -> str:
    """Tiêu chí Nội dung - Chỉ đánh giá content, bỏ qua giọng điệu"""
    return """Bạn là chuyên gia kiểm thử. ĐÁNH GIÁ CHỈ NỘI DUNG, BỎ QUA GIỌNG ĐIỆU.

{context}

{domain_glossary}

{group_rules}

{chain_of_thought}

## TIÊU CHÍ NỘI DUNG — Ngưỡng đánh giá

Sau khi hoàn thành CoT ở trên, chỉ xét nội dung:

**Nội dung (DUY NHẤT ảnh hưởng verdict):**
- Nhóm B: theo CoT-B3
- Nhóm A/C/D: theo CoT-3 (ngưỡng tự động theo số lượng thông tin cốt lõi)
- Chỉ xét thông tin CỐT LÕI — thông tin BỔ SUNG không ảnh hưởng

**Giọng điệu — BỎ QUA HOÀN TOÀN:**
- Không ảnh hưởng verdict dù tốt hay kém
- tone_note: chỉ ghi nhận để tham khảo

**Thời gian — Ít quan trọng:**
- ≤5s: không ảnh hưởng verdict
- >5s: ghi nhận nhưng không tự động FAILED

**Verdict:**
- PASSED: nội dung CỐT LÕI đủ ngưỡng
- FAILED: thiếu thông tin CỐT LÕI hoặc sai thông tin

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


def get_ux_focused_prompt() -> str:
    """Tiêu chí Trải nghiệm - Ưu tiên giọng điệu và UX"""
    return """Bạn là chuyên gia UX/CX. ĐÁNH GIÁ TRẢI NGHIỆM NGƯỜI DÙNG.

{context}

{domain_glossary}

{group_rules}

{chain_of_thought}

## TIÊU CHÍ TRẢI NGHIỆM — Ngưỡng đánh giá

Sau khi hoàn thành CoT ở trên, ưu tiên trải nghiệm:

**Giọng điệu (QUAN TRỌNG NHẤT):**
- Xuất sắc: xưng hô + dạ/ạ + tự nhiên + ấm áp
- Tốt: xưng hô + dạ/ạ
- Chấp nhận: có xưng hô HOẶC có dạ/ạ
- Kém: không xưng hô VÀ không dạ/ạ VÀ máy móc → có thể FAILED

**Nội dung (chỉ cần đủ tốt):**
- Chỉ xét thông tin CỐT LÕI, bỏ qua thông tin BỔ SUNG
- Ngưỡng: ≥70% thông tin cốt lõi là đủ

**Thời gian:**
- ≤3s: tốt
- >3s: ghi nhận, không tự động FAILED

**Verdict:**
- PASSED: giọng điệu ≥ "Chấp nhận" + nội dung CỐT LÕI ≥70%
- FAILED: giọng điệu "Kém" HOẶC nội dung CỐT LÕI <70%

{self_consistency}

{output_warning}

{confidence_guidelines}

{error_severity}

{json_output}
"""


# ============================================================================
# PROMPT MAP & FACTORY
# ============================================================================

PROMPT_MAP = {
    "standard": get_standard_prompt,
    "strict": get_strict_prompt,
    "speed-focused": get_speed_focused_prompt,
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
        group: Nhóm testcase (A/B/C/D)
        time_label: Label thời gian (vd: "1500ms (Nhanh)")

    Returns:
        ChatPromptTemplate đã format
    """
    prompt_func = PROMPT_MAP.get(criteria, PROMPT_MAP["standard"])
    prompt_template = prompt_func()

    context = create_base_context(question, expected, actual, group, time_label)

    formatted_prompt = prompt_template.format(
        context=context,
        domain_glossary=DOMAIN_GLOSSARY,
        chain_of_thought=CHAIN_OF_THOUGHT,
        group_rules=GROUP_RULES,
        self_consistency=SELF_CONSISTENCY_RULES,
        output_warning=OUTPUT_WARNING,
        confidence_guidelines=CONFIDENCE_GUIDELINES,
        error_severity=ERROR_SEVERITY_GUIDELINES,
        json_output=JSON_OUTPUT_FORMAT
    )

    return ChatPromptTemplate.from_messages([
        ("user", formatted_prompt)
    ])
