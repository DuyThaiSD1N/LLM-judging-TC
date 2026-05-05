"""
Base prompt template cho tất cả các tiêu chí
"""

from langchain_core.prompts import ChatPromptTemplate


# ============================================================================
# NGUYÊN TẮC PHÂN TÍCH NỘI DUNG
# ============================================================================

DOMAIN_GLOSSARY = """
## NGUYÊN TẮC PHÂN TÍCH NỘI DUNG

### A. So sánh theo Ý NGHĨA, không so sánh từng chữ
Câu hỏi cốt lõi khi đánh giá: "Người dùng nghe câu trả lời này có hiểu đúng và đủ không?"
Không yêu cầu bot dùng đúng từ ngữ trong kỳ vọng — chỉ cần ý nghĩa tương đương.

### B. Phân biệt THÔNG TIN CỐT LÕI và THÔNG TIN BỔ SUNG

**Thông tin CỐT LÕI** — thiếu thì FAILED:
• Giấy tờ BẮT BUỘC phải nộp (CMND, hộ khẩu, giấy khai sinh...)
• Địa điểm nộp hồ sơ (UBND cấp nào, phòng ban nào)
• Lệ phí (nếu kỳ vọng đề cập — đặc biệt khi miễn phí hoặc có số tiền cụ thể)
• Thời gian xử lý (nếu kỳ vọng đề cập)
• Hành vi từ chối / chuyển hướng (với nhóm B)
• Thừa nhận không có thông tin (với nhóm D)

**Thông tin BỔ SUNG** — thiếu thì KHÔNG FAILED:
• Lưu ý thêm, gợi ý phụ không ảnh hưởng quyết định
• Giải thích thêm về quy trình (nếu kỳ vọng không đề cập)
• Thông tin hữu ích nhưng không bắt buộc
• Câu chào hỏi, lời kết thúc lịch sự

**Quy tắc ngưỡng theo số lượng thông tin cốt lõi:**
• Kỳ vọng có 1–2 thông tin cốt lõi → cần đủ 100% (không thể thiếu)
• Kỳ vọng có 3–5 thông tin cốt lõi → cần ≥80%
• Kỳ vọng có >5 thông tin cốt lõi → cần ≥70% nhưng không được thiếu thông tin quan trọng nhất

### C. Các cách trình bày TƯƠNG ĐƯƠNG được chấp nhận

**Giấy tờ tùy thân:**
CMND = CCCD = Căn cước công dân = Chứng minh nhân dân = Thẻ căn cước = Giấy tờ tùy thân có ảnh

**Giấy tờ hộ khẩu / cư trú:**
Sổ hộ khẩu = Sổ đăng ký hộ khẩu = Giấy đăng ký thường trú = Giấy xác nhận cư trú
Giấy tạm trú = Xác nhận tạm trú = Đăng ký tạm trú

**Giấy tờ hôn nhân / độc thân:**
Giấy xác nhận độc thân = Giấy xác nhận tình trạng hôn nhân = Xác nhận chưa kết hôn
Giấy đăng ký kết hôn = Giấy chứng nhận kết hôn

**Giấy khai sinh:**
Giấy khai sinh = Bản sao giấy khai sinh = Trích lục khai sinh = Bản sao trích lục khai sinh

**Địa điểm nộp hồ sơ:**
UBND cấp xã = UBND phường = UBND xã = UBND thị trấn = Ủy ban nhân dân xã/phường/thị trấn
UBND cấp huyện = UBND quận = UBND huyện = Phòng Tư pháp cấp huyện
Bộ phận một cửa = Bộ phận tiếp nhận hồ sơ = Văn phòng một cửa = Trung tâm hành chính công

**Lệ phí:**
Miễn phí = Không mất phí = Không thu phí = Lệ phí 0 đồng = Không có lệ phí

**Thời gian xử lý:**
"X ngày làm việc" = "X ngày" (trong ngữ cảnh hành chính)
"Trong ngày" = "Ngay trong buổi" = "Không quá 1 ngày làm việc"

### D. Cách trình bày LINH HOẠT được chấp nhận
• Bot dùng từ đồng nghĩa, cách diễn đạt khác → hợp lệ nếu ý nghĩa đúng
• Bot trình bày dạng liệt kê hoặc văn xuôi → đều hợp lệ
• Bot thêm thông tin bổ sung hữu ích (không sai) → không bị trừ điểm
• Bot bỏ qua thông tin BỔ SUNG → không bị trừ điểm
• Bot bỏ qua thông tin CỐT LÕI → bị trừ điểm / FAILED
"""


# ============================================================================
# CHAIN-OF-THOUGHT — bắt buộc suy luận trước khi ra verdict
# ============================================================================

CHAIN_OF_THOUGHT = """
## YÊU CẦU SUY LUẬN (Chain-of-Thought) — BẮT BUỘC

Trước khi output JSON, bạn PHẢI suy luận theo đúng các bước sau.
Viết suy luận vào trường "reasoning" trong JSON output.

**Với nhóm B — kiểm tra hành vi từ chối:**
```
[CoT-B1] Bot có từ chối trả lời nội dung ngoài phạm vi không?
         → Có / Không — trích dẫn: "..."
[CoT-B2] Bot có chuyển hướng về hành chính công không?
         → Có / Không — trích dẫn: "..."
[CoT-B3] Kết luận: (Có+Có)→PASSED | (Có+Không)→FAILED | (Không+*)→FAILED
```

**Với nhóm A / C / D — kiểm tra nội dung:**
```
[CoT-1] Liệt kê thông tin CỐT LÕI từ kỳ vọng:
         1. [tên thông tin] — loại: [giấy tờ/địa điểm/lệ phí/thời gian/khác]
         2. ...
[CoT-2] Kiểm tra từng thông tin cốt lõi trong câu trả lời thực tế:
         1. [tên thông tin] → Có ✓ / Không ✗ / Tương đương ≈ — trích dẫn: "..."
         2. ...
[CoT-3] Tổng kết: X/Y thông tin cốt lõi đáp ứng = Z%
         Ngưỡng áp dụng: [100% / 80% / 70%] (theo số lượng thông tin)
[CoT-4] Đánh giá giọng điệu:
         Xưng hô: Có/Không | Dạ/ạ: Có/Không | Tự nhiên: Có/Không
[CoT-5] Đánh giá thời gian: [Xms] → [good/ok/slow]
[CoT-6] Verdict: PASSED/FAILED vì [lý do ngắn gọn]
```
"""


# ============================================================================
# GROUP RULES
# ============================================================================

GROUP_RULES = """
## QUY TẮC ĐÁNH GIÁ THEO NHÓM (ƯU TIÊN CAO NHẤT)

### NHÓM A — Hỏi đầy đủ thông tin
Bot phải cung cấp đúng và đủ thông tin về thủ tục hành chính.
- PASSED: Các thông tin CỐT LÕI trong kỳ vọng đều có trong câu trả lời thực tế
  (áp dụng "NGUYÊN TẮC PHÂN TÍCH NỘI DUNG" để nhận biết cách trình bày tương đương)
- FAILED: Thiếu thông tin CỐT LÕI, sai thông tin, hoặc bịa thông tin không có cơ sở
- Thiếu thông tin BỔ SUNG → KHÔNG FAILED

### NHÓM B — Hỏi ngoài phạm vi / ngoại lệ
Bot phải TỪ CHỐI và CHUYỂN HƯỚNG về hành chính công.

**PASSED khi bot làm BẤT KỲ điều nào sau đây:**
✓ Nói không hỗ trợ / không trong phạm vi + hỏi lại về thủ tục hành chính
✓ Từ chối lịch sự + gợi ý hỏi về thủ tục hành chính công
✓ Nói chỉ hỗ trợ hành chính công + mời hỏi thủ tục
✓ Bất kỳ cách diễn đạt nào thể hiện: (1) không trả lời nội dung ngoài phạm vi VÀ (2) chuyển hướng về hành chính công

**FAILED chỉ khi:**
✗ Bot trả lời nội dung câu hỏi ngoài phạm vi (dù đúng hay sai)
✗ Bot từ chối nhưng KHÔNG có bất kỳ ý chuyển hướng nào về hành chính công

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


# ============================================================================
# SELF-CONSISTENCY RULES
# ============================================================================

SELF_CONSISTENCY_RULES = """
## SELF-CONSISTENCY — Kiểm tra trước khi output
✓ Nếu verdict="PASSED" → error_desc, suggestion, suggested_response phải RỖNG ("")
✓ Nếu verdict="FAILED" → error_desc, suggestion, suggested_response phải có nội dung
✓ Với nhóm B: CoT-B1=Có VÀ CoT-B2=Có → BẮT BUỘC verdict="PASSED"
✓ reasoning phải nhất quán với verdict (không được CoT kết luận PASSED nhưng verdict FAILED)
"""


# ============================================================================
# OUTPUT WARNING
# ============================================================================

OUTPUT_WARNING = """
## LƯU Ý OUTPUT
- Đánh giá dựa trên PHÂN TÍCH ĐỊNH TÍNH, KHÔNG dùng điểm số
- error_desc: mô tả lỗi cụ thể, trích dẫn câu sai/thiếu (nếu FAILED)
- suggestion: gợi ý cải thiện cụ thể (nếu FAILED)
- suggested_response: mẫu câu trả lời hoàn chỉnh (nếu FAILED)
- tone_note: nhận xét giọng điệu ngắn gọn
- reasoning: toàn bộ suy luận CoT ở trên (bắt buộc)
"""


# ============================================================================
# CONFIDENCE GUIDELINES
# ============================================================================

CONFIDENCE_GUIDELINES = """
## CONFIDENCE LEVEL (0.0–1.0)
• ≥0.9: Rõ ràng đúng/sai, không có vùng xám
• 0.7–0.9: Có chút nghi ngờ, thông tin gần đúng hoặc giọng điệu không rõ
• <0.7: Edge case, không chắc chắn → needs_human_review = true

confidence_reason: 1 câu giải thích tại sao confidence ở mức này
"""


# ============================================================================
# ERROR SEVERITY
# ============================================================================

ERROR_SEVERITY_GUIDELINES = """
## ERROR SEVERITY (chỉ khi FAILED)
• Critical: Thông tin CỐT LÕI bị thiếu hoặc SAI → ảnh hưởng trực tiếp quyết định người dùng
• Major: Giọng điệu tệ (thô lỗ, không xưng hô) hoặc thời gian >5s
• Minor: Thiếu thông tin BỔ SUNG, thiếu dạ/ạ, hơi máy móc

errors array: [{{description, severity, quote}}] — sắp xếp Critical → Major → Minor
"""


# ============================================================================
# JSON OUTPUT FORMAT — thêm trường "reasoning"
# ============================================================================

JSON_OUTPUT_FORMAT = """
## OUTPUT JSON (11 trường — bắt buộc có "reasoning")

⚠️ QUY TẮC BẮT BUỘC KHI FAILED:
- "error_desc" PHẢI mô tả CỤ THỂ thông tin nào bị thiếu/sai, trích dẫn câu thực tế của bot
  KHÔNG được để trống, KHÔNG được viết chung chung như "không đạt yêu cầu"
  Ví dụ đúng: "Bot thiếu thông tin về lệ phí. Bot nói '...' nhưng kỳ vọng cần đề cập miễn phí."
- "suggestion" PHẢI đưa ra hướng sửa cụ thể (2-3 điểm rõ ràng)
  KHÔNG được để trống khi FAILED
  Ví dụ đúng: "1. Bổ sung thông tin lệ phí. 2. Nêu rõ địa điểm nộp hồ sơ."
- "suggested_response" PHẢI là mẫu câu trả lời hoàn chỉnh đã sửa

{{
  "reasoning": "Toàn bộ suy luận CoT theo các bước [CoT-1]...[CoT-6] hoặc [CoT-B1]...[CoT-B3]",
  "verdict": "PASSED hoặc FAILED",
  "confidence_level": 0.85,
  "needs_human_review": false,
  "confidence_reason": "1 câu giải thích confidence",
  "errors": [
    {{
      "description": "Mô tả lỗi cụ thể (1 câu, có trích dẫn)",
      "severity": "Critical | Major | Minor",
      "quote": "Trích dẫn nguyên văn từ câu trả lời thực tế của bot"
    }}
  ],
  "error_desc": "FAILED: mô tả CHI TIẾT lỗi — thông tin nào thiếu/sai, trích dẫn câu bot nói. PASSED: để trống ''",
  "suggestion": "FAILED: 2-3 bước cải thiện CỤ THỂ. PASSED: để trống ''",
  "suggested_response": "FAILED: mẫu câu trả lời hoàn chỉnh đã sửa. PASSED: để trống ''",
  "tone_note": "Nhận xét giọng điệu (1–2 câu)",
  "time_verdict": "good | ok | slow",
  "time_note": "Nhận xét thời gian (1 câu)"
}}

CHỈ trả về JSON, không thêm text nào khác.
"""


# ============================================================================
# HELPERS
# ============================================================================

def get_group_desc(group: str) -> str:
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
    return f"""## CONTEXT
Nhóm: {group} — {get_group_desc(group)}
Câu hỏi của người dùng: "{question}"
Kỳ vọng (hành vi/nội dung mong muốn — KHÔNG phải mẫu câu bắt buộc): "{expected}"
Câu trả lời thực tế của bot (đây là thứ cần đánh giá): "{actual}"
Thời gian phản hồi: {time_label}
"""
