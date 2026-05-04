"""
Base prompt template cho tất cả các tiêu chí
"""

from langchain_core.prompts import ChatPromptTemplate


# Domain glossary - dùng chung cho tất cả tiêu chí
DOMAIN_GLOSSARY = """
## NGUYÊN TẮC PHÂN TÍCH NỘI DUNG

### 1. So sánh theo Ý NGHĨA, không so sánh từng chữ
Khi đánh giá, hãy hỏi: "Người dùng nghe câu trả lời này có hiểu đúng và đủ không?"
Không yêu cầu bot dùng đúng từ ngữ trong kỳ vọng — chỉ cần ý nghĩa tương đương.

### 2. Các cách trình bày TƯƠNG ĐƯƠNG về giấy tờ tùy thân
• CMND / CCCD / Căn cước công dân / Chứng minh nhân dân / Thẻ căn cước / Giấy tờ tùy thân có ảnh
→ Nếu kỳ vọng nói "CMND" mà bot nói "CCCD" hoặc "căn cước" → coi là ĐÃ ĐÁP ỨNG

### 3. Các cách trình bày TƯƠNG ĐƯƠNG về giấy tờ hộ khẩu / cư trú
• Sổ hộ khẩu / Sổ đăng ký hộ khẩu / Giấy đăng ký thường trú / Giấy xác nhận cư trú
• Giấy tạm trú / Xác nhận tạm trú / Đăng ký tạm trú
→ Nếu kỳ vọng nói "sổ hộ khẩu" mà bot nói "giấy đăng ký thường trú" → coi là ĐÃ ĐÁP ỨNG

### 4. Các cách trình bày TƯƠNG ĐƯƠNG về giấy tờ hôn nhân / độc thân
• Giấy xác nhận độc thân / Giấy xác nhận tình trạng hôn nhân / Xác nhận chưa kết hôn
• Giấy đăng ký kết hôn / Giấy chứng nhận kết hôn
→ Nếu kỳ vọng nói "xác nhận độc thân" mà bot nói "xác nhận tình trạng hôn nhân" → coi là ĐÃ ĐÁP ỨNG

### 5. Các cách trình bày TƯƠNG ĐƯƠNG về giấy khai sinh
• Giấy khai sinh / Bản sao giấy khai sinh / Trích lục khai sinh / Bản sao trích lục khai sinh

### 6. Các cách trình bày TƯƠNG ĐƯƠNG về địa điểm nộp hồ sơ
• UBND cấp xã / UBND phường / UBND xã / UBND thị trấn / Ủy ban nhân dân xã/phường/thị trấn
• UBND cấp huyện / UBND quận / UBND huyện / UBND thị xã / Phòng Tư pháp cấp huyện
• Bộ phận một cửa / Bộ phận tiếp nhận hồ sơ / Văn phòng một cửa / Trung tâm hành chính công
→ Nếu kỳ vọng nói "UBND cấp xã" mà bot nói "UBND phường" → coi là ĐÃ ĐÁP ỨNG

### 7. Các cách trình bày TƯƠNG ĐƯƠNG về lệ phí
• Miễn phí / Không mất phí / Không thu phí / Lệ phí: 0 đồng / Không có lệ phí
→ Nếu kỳ vọng nói "miễn phí" mà bot nói "không thu phí" → coi là ĐÃ ĐÁP ỨNG

### 8. Các cách trình bày TƯƠNG ĐƯƠNG về thời gian xử lý
• "X ngày làm việc" = "X ngày" (trong ngữ cảnh hành chính)
• "Trong ngày" = "Ngay trong buổi" = "Không quá 1 ngày làm việc"

### 9. Cách trình bày LINH HOẠT được chấp nhận
• Bot có thể dùng từ đồng nghĩa, cách diễn đạt khác nhau miễn thông tin đúng
• Bot có thể trình bày theo dạng liệt kê hoặc văn xuôi — đều hợp lệ
• Bot có thể thêm thông tin bổ sung hữu ích (không sai) — không bị trừ điểm
• Bot có thể bỏ qua thông tin thứ yếu nếu thông tin cốt lõi đã đủ
"""


# Group rules - quy tắc đánh giá riêng cho từng nhóm
GROUP_RULES = """
## QUY TẮC ĐÁNH GIÁ THEO NHÓM (ƯU TIÊN CAO NHẤT)

### NHÓM A — Hỏi đầy đủ thông tin
Bot phải cung cấp đúng và đủ thông tin về thủ tục hành chính.
- PASSED: Các thông tin cốt lõi trong kỳ vọng đều có trong câu trả lời thực tế
  (áp dụng "NGUYÊN TẮC PHÂN TÍCH NỘI DUNG" để nhận biết cách trình bày tương đương)
- FAILED: Thiếu thông tin quan trọng, sai thông tin, hoặc bịa thông tin không có cơ sở

### NHÓM B — Hỏi ngoài phạm vi / ngoại lệ
Bot phải TỪ CHỐI và CHUYỂN HƯỚNG về hành chính công.

**PASSED khi bot làm BẤT KỲ điều nào sau đây:**
✓ Nói không hỗ trợ / không trong phạm vi + hỏi lại về thủ tục hành chính
✓ Từ chối lịch sự + gợi ý hỏi về thủ tục hành chính công
✓ Nói chỉ hỗ trợ hành chính công + mời hỏi thủ tục
✓ Bất kỳ cách diễn đạt nào thể hiện: (1) không trả lời câu hỏi ngoài phạm vi VÀ (2) chuyển hướng về hành chính công

**FAILED chỉ khi:**
✗ Bot trả lời nội dung câu hỏi ngoài phạm vi (bịa, sai, hoặc đúng nhưng không nên trả lời)
✗ Bot từ chối nhưng KHÔNG chuyển hướng về hành chính công gì cả

**LƯU Ý QUAN TRỌNG cho nhóm B:**
- KHÔNG yêu cầu bot dùng đúng mẫu câu cụ thể nào
- KHÔNG yêu cầu bot phải hỏi lại bằng câu hỏi — chỉ cần có ý chuyển hướng
- Câu trả lời thực tế của bot là cơ sở đánh giá, KHÔNG phải câu trả lời kỳ vọng
- Kỳ vọng chỉ là gợi ý hành vi mong muốn, không phải mẫu câu bắt buộc

### NHÓM C — Hỏi chuyển topic đột ngột
Bot phải xử lý chuyển chủ đề hợp lý, không bị lạc.
- PASSED: Bot nhận ra chủ đề mới và xử lý phù hợp (trả lời hoặc từ chối lịch sự)
- FAILED: Bot bị lạc, trả lời nhầm chủ đề cũ, hoặc không xử lý được

### NHÓM D — Tài liệu không có trong CSDL
Bot phải thừa nhận không có thông tin, TUYỆT ĐỐI không bịa.
- PASSED: Bot nói không có thông tin / chưa có dữ liệu + hướng dẫn liên hệ trực tiếp
- FAILED: Bot bịa thông tin, hoặc trả lời như thể có dữ liệu khi không có
"""


# Self-consistency rules - dùng chung
SELF_CONSISTENCY_RULES = """
## SELF-CONSISTENCY RULES
Trước khi output JSON, kiểm tra:
✓ Nếu verdict="PASSED" → error_desc, suggestion, suggested_response phải RỖNG ("")
✓ Nếu verdict="FAILED" → error_desc, suggestion, suggested_response phải có nội dung
✓ Với nhóm B: nếu bot từ chối VÀ chuyển hướng về hành chính công → BẮT BUỘC PASSED
"""


# Output format warning - dùng chung
OUTPUT_WARNING = """
## LƯU Ý QUAN TRỌNG VỀ OUTPUT
Đánh giá dựa trên PHÂN TÍCH ĐỊNH TÍNH, KHÔNG dùng điểm số.
LLM tự quyết định PASSED/FAILED dựa trên phân tích tổng thể.
- error_desc: Mô tả LỖI cụ thể (nếu FAILED)
- suggestion: Đưa ra GỢI Ý cải thiện (nếu FAILED)
- suggested_response: Đưa MẪU câu trả lời (nếu FAILED)
- tone_note: PHÂN TÍCH giọng điệu
"""


# Confidence level guidelines
CONFIDENCE_GUIDELINES = """
## CONFIDENCE LEVEL
Đánh giá độ tự tin về kết quả (0.0-1.0):
• **≥0.9 (High)**: Rõ ràng thiếu/sai hoặc hoàn toàn đúng, không có vùng xám
• **0.7-0.9 (Medium)**: Thông tin gần đúng, giọng điệu không rõ ràng, có chút nghi ngờ
• **<0.7 (Low)**: Edge case, không chắc chắn, cần human review

**confidence_reason**: Giải thích ngắn gọn tại sao confidence ở mức này (1 câu)
"""


# Error severity guidelines
ERROR_SEVERITY_GUIDELINES = """
## ERROR SEVERITY (chỉ khi FAILED)
Phân loại từng lỗi theo mức độ nghiêm trọng:
• **Critical**: Thông tin SAI hoặc THIẾU thông tin QUAN TRỌNG ảnh hưởng quyết định người dùng
• **Major**: Giọng điệu TỆ (thô lỗ, không xưng hô) hoặc thời gian QUÁ CHẬM (>5s)
• **Minor**: Thiếu chi tiết PHỤ, thiếu dạ/ạ, hơi máy móc

**errors array**: Mỗi lỗi là object {{description, severity, quote}}
- description: Mô tả lỗi cụ thể (1 câu)
- severity: "Critical" | "Major" | "Minor"
- quote: Trích dẫn từ câu trả lời thực tế (nếu có)

Sắp xếp errors theo thứ tự: Critical → Major → Minor
"""


# JSON output format
JSON_OUTPUT_FORMAT = """
## OUTPUT JSON (bắt buộc 10 trường)
{{
  "verdict": "PASSED hoặc FAILED",
  "confidence_level": 0.85,
  "needs_human_review": false,
  "confidence_reason": "Giải thích ngắn gọn tại sao confidence ở mức này (1 câu)",
  "errors": [
    {{
      "description": "Mô tả lỗi cụ thể (1 câu)",
      "severity": "Critical | Major | Minor",
      "quote": "Trích dẫn từ câu trả lời thực tế"
    }}
  ],
  "error_desc": "Nếu FAILED: liệt kê cụ thể từng lỗi với trích dẫn (2-3 câu). Nếu PASSED: để trống",
  "suggestion": "Nếu FAILED: từng bước cải thiện (2-3 điểm). Nếu PASSED: để trống",
  "suggested_response": "Nếu FAILED: mẫu hoàn chỉnh. Nếu PASSED: để trống",
  "tone_note": "Phân tích xưng hô, lịch sự, tự nhiên (1-2 câu)",
  "time_verdict": "good hoặc ok hoặc slow",
  "time_note": "Nhận xét thời gian (1 câu)"
}}

CHỈ trả về JSON, không thêm text nào khác.
"""


def get_group_desc(group: str) -> str:
    """Get short group description for context header"""
    descs = {
        "A": "Hỏi đầy đủ thông tin",
        "B": "Hỏi ngoài phạm vi / ngoại lệ",
        "C": "Hỏi chuyển topic đột ngột",
        "D": "Tài liệu không có trong CSDL",
    }
    return descs.get(group, "")


def create_base_context(
    question: str,
    expected: str,
    actual: str,
    group: str,
    time_label: str
) -> str:
    """Create base context section"""
    return f"""## CONTEXT
Nhóm: {group} — {get_group_desc(group)}
Câu hỏi của người dùng: "{question}"
Kỳ vọng (hành vi/nội dung mong muốn — KHÔNG phải mẫu câu bắt buộc): "{expected}"
Câu trả lời thực tế của bot (đây là thứ cần đánh giá): "{actual}"
Thời gian phản hồi: {time_label}

## HƯỚNG DẪN PHÂN TÍCH
Khi so sánh "Kỳ vọng" và "Thực tế":
1. Trích xuất các THÔNG TIN CỐT LÕI từ kỳ vọng (giấy tờ cần có, địa điểm, thời gian, lệ phí...)
2. Kiểm tra từng thông tin cốt lõi đó có xuất hiện trong câu trả lời thực tế không
3. Áp dụng "NGUYÊN TẮC PHÂN TÍCH NỘI DUNG" để nhận biết các cách trình bày tương đương
4. Kết luận: bao nhiêu % thông tin cốt lõi đã được đáp ứng?
"""
