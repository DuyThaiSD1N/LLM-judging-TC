"""
Base prompt template cho tất cả các tiêu chí
"""

from langchain_core.prompts import ChatPromptTemplate


# Domain glossary - dùng chung cho tất cả tiêu chí
DOMAIN_GLOSSARY = """
## DOMAIN GLOSSARY
Các thuật ngữ sau được coi là TƯƠNG ĐƯƠNG khi so sánh nội dung:
• CMND = CCCD = Căn cước công dân = Chứng minh nhân dân = Thẻ căn cước
• Giấy xác nhận độc thân = Giấy xác nhận tình trạng hôn nhân = Xác nhận hôn nhân
• Sổ hộ khẩu = Sổ đăng ký hộ khẩu = Giấy đăng ký thường trú
• Giấy khai sinh = Bản sao giấy khai sinh = Trích lục khai sinh
"""


# Group descriptions
GROUP_DESC = {
    "A": "Hỏi đầy đủ thông tin — bot phải cung cấp đúng và đủ thông tin về thủ tục hành chính.",
    "B": """Hỏi ngoại lệ / ngoài phạm vi — bot phải từ chối và chuyển hướng về hành chính công.
      Cách từ chối mặc định HỢP LỆ của bot là: KHÔNG trả lời nội dung ngoài phạm vi, sau đó
      hỏi lại người dùng có cần hỗ trợ thủ tục hành chính không.
      Ví dụ hợp lệ: "Dạ em rất sẵn lòng a, nhưng em xin phép hỗ trợ các nội dung hành chính
      công thôi, anh cần em tra cứu thủ tục nào không ạ?"
      Đây là hành vi ĐÚNG — phải chấm PASSED nếu bot từ chối và chuyển hướng như vậy.""",
    "C": "Hỏi chuyển topic đột ngột — bot phải xử lý chuyển chủ đề hợp lý, không bị lạc.",
    "D": "Hỏi tài liệu không có trong CSDL — bot phải thừa nhận không có thông tin và hướng dẫn đến văn phòng 1 cửa, tuyệt đối không bịa.",
}


# Self-consistency rules - dùng chung
SELF_CONSISTENCY_RULES = """
## SELF-CONSISTENCY RULES
Trước khi output JSON, kiểm tra:
✓ Nếu verdict="PASSED" → error_desc, suggestion, suggested_response phải RỖNG ("")
✓ Nếu verdict="FAILED" → error_desc, suggestion, suggested_response phải có nội dung
✓ Nếu total_score ≥threshold → verdict phải là "PASSED"
✓ Nếu total_score <threshold → verdict phải là "FAILED"
"""


# Output format warning - dùng chung
OUTPUT_WARNING = """
## LƯU Ý QUAN TRỌNG VỀ OUTPUT
**KHÔNG BAO GIỜ** hiển thị điểm số (content_score, tone_score, time_score, total_score) trong các trường:
- error_desc: Chỉ mô tả LỖI cụ thể, KHÔNG nói "content_score = X"
- suggestion: Chỉ đưa ra GỢI Ý cải thiện, KHÔNG nói "cần tăng điểm lên X"
- suggested_response: Chỉ đưa MẪU câu trả lời, KHÔNG đề cập điểm số
- tone_note: Chỉ PHÂN TÍCH giọng điệu, KHÔNG nói "tone_score = X"

Điểm số chỉ dùng để tính toán verdict nội bộ, không hiển thị cho người dùng.
"""


# Confidence level guidelines - Phase 2
CONFIDENCE_GUIDELINES = """
## CONFIDENCE LEVEL (Phase 2)
Sau khi tính điểm, đánh giá độ tự tin về kết quả (0.0-1.0):
• **≥0.9 (High)**: Rõ ràng thiếu/sai hoặc hoàn toàn đúng, không có vùng xám
• **0.7-0.9 (Medium)**: Thông tin gần đúng, giọng điệu không rõ ràng, có chút nghi ngờ
• **<0.7 (Low)**: Edge case, không chắc chắn, cần human review

**confidence_reason**: Giải thích ngắn gọn tại sao confidence ở mức này (1 câu)
"""


# Error severity guidelines - Phase 2
ERROR_SEVERITY_GUIDELINES = """
## ERROR SEVERITY (Phase 2 - chỉ khi FAILED)
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
## OUTPUT JSON (bắt buộc 13 trường - Phase 2)
{{
  "total_score": 75,
  "content_score": 80,
  "tone_score": 70,
  "time_score": 100,
  "confidence_level": 0.85,
  "needs_human_review": false,
  "confidence_reason": "Thông tin rõ ràng, giọng điệu ổn định",
  "errors": [
    {{
      "description": "Thiếu thông tin về giấy xác nhận độc thân",
      "severity": "Critical",
      "quote": "Cần CMND"
    }}
  ],
  "verdict": "PASSED hoặc FAILED",
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
    """Get group description"""
    return GROUP_DESC.get(group, "")


def create_base_context(
    question: str,
    expected: str,
    actual: str,
    group: str,
    time_label: str
) -> str:
    """Create base context section"""
    return f"""## CONTEXT
Nhóm: {group} - {get_group_desc(group)}
Câu hỏi: "{question}"
Kỳ vọng: "{expected}"
Thực tế: "{actual}"
Thời gian: {time_label}
"""
