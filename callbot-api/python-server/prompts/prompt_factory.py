"""
Factory để tạo prompt cho từng tiêu chí đánh giá - LLM tự đánh giá không dùng scoring
Sử dụng LangChain ChatPromptTemplate
"""

from langchain_core.prompts import ChatPromptTemplate
from .base_prompt import (
    DOMAIN_GLOSSARY,
    GROUP_RULES,
    SELF_CONSISTENCY_RULES,
    OUTPUT_WARNING,
    CONFIDENCE_GUIDELINES,
    ERROR_SEVERITY_GUIDELINES,
    JSON_OUTPUT_FORMAT,
    create_base_context
)


def get_standard_prompt() -> str:
    """Tiêu chí Chuẩn - Cân bằng giữa nội dung, giọng điệu và thời gian"""
    return """Bạn là chuyên gia kiểm thử chatbot hành chính công. Đánh giá theo tiêu chí CHUẨN.

{context}

{domain_glossary}

{group_rules}

## TIÊU CHÍ CHUẨN — Cân bằng nội dung + giọng điệu + thời gian

**Bước 1: Xác định nhóm và áp dụng quy tắc nhóm trước**
Đọc kỹ "QUY TẮC ĐÁNH GIÁ THEO NHÓM" ở trên và áp dụng cho nhóm tương ứng.
Đặc biệt với nhóm B: nếu bot từ chối + chuyển hướng → PASSED ngay, không cần xét thêm.

**Bước 2: Đánh giá nội dung (chỉ với nhóm A, C, D)**
- Liệt kê các thông tin cốt lõi trong kỳ vọng (giấy tờ, địa điểm, thời gian, lệ phí...)
- Kiểm tra từng thông tin đó có trong câu trả lời thực tế không (dùng "NGUYÊN TẮC PHÂN TÍCH NỘI DUNG" để nhận biết cách trình bày tương đương)
- ≥80% thông tin cốt lõi có mặt → nội dung đạt

**Bước 3: Đánh giá giọng điệu**
- Có xưng hô phù hợp (anh/chị/em) không?
- Có dùng dạ/ạ không?
- Giọng điệu có tự nhiên, thân thiện không?
- Giọng điệu kém KHÔNG tự động dẫn đến FAILED nếu nội dung tốt

**Bước 4: Đánh giá thời gian**
- ≤2s: Rất tốt
- ≤3s: Chấp nhận được
- >3s: Chậm (ghi nhận nhưng không tự động FAILED)

**Quyết định PASSED/FAILED:**
- PASSED: Nội dung đúng đủ (≥80%) VÀ giọng điệu chấp nhận được
- FAILED: Nội dung sai/thiếu quan trọng HOẶC giọng điệu rất kém (thô lỗ, cộc lốc)
- Thời gian chậm: chỉ FAILED nếu >5s

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

## TIÊU CHÍ NGHIÊM NGẶT — Yêu cầu cao về mọi mặt

**Bước 1: Xác định nhóm và áp dụng quy tắc nhóm trước**
Đọc kỹ "QUY TẮC ĐÁNH GIÁ THEO NHÓM" ở trên và áp dụng cho nhóm tương ứng.
Với nhóm B: nếu bot từ chối + chuyển hướng → PASSED (nhưng vẫn nhận xét chất lượng từ chối).

**Bước 2: Đánh giá nội dung (khắt khe)**
- Liệt kê từng thông tin cốt lõi trong kỳ vọng
- Kiểm tra từng thông tin đó có trong câu trả lời thực tế không (dùng "NGUYÊN TẮC PHÂN TÍCH NỘI DUNG" để nhận biết cách trình bày tương đương)
- Phải có ≥95% thông tin cốt lõi, không được thiếu bất kỳ chi tiết quan trọng nào

**Bước 3: Đánh giá giọng điệu (yêu cầu hoàn hảo)**
- Phải có xưng hô đúng (anh/chị/em)
- Phải có dạ/ạ
- Phải tự nhiên, thân thiện, không máy móc
- Thiếu bất kỳ yếu tố nào → trừ điểm nặng

**Bước 4: Đánh giá thời gian (yêu cầu nhanh)**
- ≤2s: Tốt
- ≤2.5s: Chấp nhận được
- >2.5s: Cần ghi nhận là lỗi

**Quyết định PASSED/FAILED:**
- PASSED: Nội dung ≥95% + giọng điệu tốt (xưng hô + dạ/ạ) + thời gian ≤2.5s
- FAILED: Bất kỳ khiếm khuyết đáng kể nào về nội dung, giọng điệu, hoặc thời gian

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

## TIÊU CHÍ TỐC ĐỘ — Ưu tiên thời gian phản hồi nhanh

**Bước 1: Xác định nhóm và áp dụng quy tắc nhóm trước**
Đọc kỹ "QUY TẮC ĐÁNH GIÁ THEO NHÓM" ở trên và áp dụng cho nhóm tương ứng.
Với nhóm B: nếu bot từ chối + chuyển hướng → PASSED bất kể thời gian.

**Bước 2: Đánh giá thời gian (QUAN TRỌNG NHẤT)**
- ≤1.5s: Xuất sắc
- ≤2s: Rất tốt
- ≤3s: Chấp nhận được
- >3s: Chậm → cần nội dung rất tốt mới PASSED

**Bước 3: Đánh giá nội dung (chỉ cần đủ tốt)**
- Liệt kê các thông tin cốt lõi trong kỳ vọng
- Kiểm tra từng thông tin đó có trong câu trả lời thực tế không (dùng "NGUYÊN TẮC PHÂN TÍCH NỘI DUNG")
- ≥70% thông tin cốt lõi là chấp nhận được, không cần 100% hoàn hảo

**Bước 4: Đánh giá giọng điệu (ít quan trọng)**
- Có xưng hô hoặc dạ/ạ là được
- Chấp nhận hơi máy móc
- Chỉ FAILED nếu thô lỗ rõ ràng

**Quyết định PASSED/FAILED:**
- PASSED: Thời gian ≤2s + nội dung ≥70%
- PASSED: Thời gian ≤3s + nội dung ≥80%
- FAILED: Thời gian >3s + nội dung <80%
- FAILED: Nội dung <70% bất kể thời gian

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

## TIÊU CHÍ NỘI DUNG — Chỉ đánh giá độ chính xác thông tin

**Bước 1: Xác định nhóm và áp dụng quy tắc nhóm trước**
Đọc kỹ "QUY TẮC ĐÁNH GIÁ THEO NHÓM" ở trên và áp dụng cho nhóm tương ứng.
Với nhóm B: nếu bot từ chối + chuyển hướng → PASSED bất kể giọng điệu hay thời gian.

**Bước 2: Đánh giá nội dung (QUAN TRỌNG NHẤT — DUY NHẤT)**
- Liệt kê các thông tin cốt lõi trong kỳ vọng
- Kiểm tra từng thông tin đó có trong câu trả lời thực tế không (dùng "NGUYÊN TẮC PHÂN TÍCH NỘI DUNG" để nhận biết cách trình bày tương đương)
- ≥80% thông tin cốt lõi → PASSED; <80% hoặc sai thông tin → FAILED

**Bước 3: Giọng điệu — BỎ QUA HOÀN TOÀN**
- Không đánh giá xưng hô, dạ/ạ, tự nhiên
- Chấp nhận mọi cách diễn đạt miễn nội dung đúng
- tone_note: chỉ ghi nhận, không ảnh hưởng verdict

**Bước 4: Thời gian — Ít quan trọng**
- ≤5s: Chấp nhận được
- >5s: Ghi nhận nhưng không tự động FAILED

**Quyết định PASSED/FAILED:**
- PASSED: Nội dung đầy đủ và chính xác (≥80%)
- FAILED: Thiếu thông tin quan trọng hoặc sai thông tin

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

## TIÊU CHÍ TRẢI NGHIỆM — Ưu tiên giọng điệu thân thiện

**Bước 1: Xác định nhóm và áp dụng quy tắc nhóm trước**
Đọc kỹ "QUY TẮC ĐÁNH GIÁ THEO NHÓM" ở trên và áp dụng cho nhóm tương ứng.
Với nhóm B: nếu bot từ chối + chuyển hướng lịch sự, thân thiện → PASSED.

**Bước 2: Đánh giá giọng điệu (QUAN TRỌNG NHẤT)**
- Có xưng hô phù hợp (anh/chị/em) không?
- Có dùng dạ/ạ không?
- Giọng điệu có tự nhiên, thân thiện, ấm áp không?
- Có tạo cảm giác thoải mái cho người dùng không?

**Bước 3: Đánh giá nội dung (chỉ cần đủ tốt)**
- Liệt kê các thông tin cốt lõi trong kỳ vọng
- Kiểm tra từng thông tin đó có trong câu trả lời thực tế không (dùng "NGUYÊN TẮC PHÂN TÍCH NỘI DUNG")
- ≥70% thông tin cốt lõi là đủ, ưu tiên trải nghiệm hơn chi tiết kỹ thuật

**Bước 4: Đánh giá thời gian**
- ≤3s: Tốt
- >3s: Cần cải thiện (ghi nhận nhưng không tự động FAILED)

**Quyết định PASSED/FAILED:**
- PASSED: Giọng điệu tốt (xưng hô + dạ/ạ + tự nhiên) + nội dung ≥70%
- FAILED: Giọng điệu kém (thô lỗ, cộc lốc, máy móc hoàn toàn) HOẶC nội dung <70%

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
        group: Nhóm testcase
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
