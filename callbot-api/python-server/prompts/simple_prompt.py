"""
SIMPLIFIED JUDGE PROMPT - Hỗ trợ 5 tiêu chí đánh giá khác nhau
Chỉ xét: Nội dung + Keywords + Thời gian + Giọng điệu
"""

# ═══════════════════════════════════════════════════════════
# GROUNDING REQUIREMENT - Bắt buộc trích dẫn để giảm hallucination
# ═══════════════════════════════════════════════════════════

GROUNDING_REQUIREMENT = """
═══════════════════════════════════════════════════════════
YÊU CẦU TRÍCH DẪN (Grounding) - BẮT BUỘC
═══════════════════════════════════════════════════════════

**NGUYÊN TẮC:** Mọi đánh giá PHẢI dựa trên TRÍCH DẪN CỤ THỂ từ text.
**MỤC ĐÍCH:** Tránh bịa đặt (hallucination), đảm bảo đánh giá có căn cứ.

## CÁCH TRÍCH DẪN ĐÚNG:

### 1. Với MỖI thông tin đánh giá:
```
Thông tin: [Tên thông tin]
├─ Trong KỲ VỌNG: "[Trích dẫn chính xác]"
├─ Trong THỰC TẾ: "[Trích dẫn chính xác]" hoặc "KHÔNG CÓ"
└─ Kết luận: ✓ Có / ✗ Không / ≈ Tương đương
```

### 2. Ví dụ cụ thể:

**VÍ DỤ 1: Thông tin CÓ (từ đồng nghĩa)**
```
Thông tin: Giấy tờ tùy thân
├─ Trong KỲ VỌNG: "Cần CMND"
├─ Trong THỰC TẾ: "Cần CCCD"
└─ Kết luận: ≈ Tương đương (CMND = CCCD)
```

**VÍ DỤ 2: Thông tin THIẾU**
```
Thông tin: Lệ phí
├─ Trong KỲ VỌNG: "Lệ phí 500.000đ"
├─ Trong THỰC TẾ: KHÔNG CÓ
└─ Kết luận: ✗ Thiếu
```

**VÍ DỤ 3: Thông tin SAI**
```
Thông tin: Thời gian xử lý
├─ Trong KỲ VỌNG: "15 ngày"
├─ Trong THỰC TẾ: "30 ngày"
└─ Kết luận: ✗ Sai (15 ≠ 30)
```

## QUY TẮC BẮT BUỘC:

✅ **PHẢI LÀM:**
1. Trích dẫn CHÍNH XÁC từ text (copy nguyên văn)
2. Dùng dấu ngoặc kép "..." cho trích dẫn
3. Nếu không có → ghi "KHÔNG CÓ", không bịa
4. So sánh trích dẫn với nhau, không so sánh ý nghĩa chung chung

❌ **KHÔNG ĐƯỢC:**
1. Paraphrase (diễn giải lại) khi trích dẫn
2. Tóm tắt thành ý chung
3. Bịa thông tin không có trong text
4. Nói "có đề cập" mà không trích dẫn cụ thể

## VÍ DỤ SAI vs ĐÚNG:

**❌ SAI (không trích dẫn):**
```
Thông tin: Địa điểm
Kết luận: Có đề cập đến UBND
```

**✅ ĐÚNG (có trích dẫn):**
```
Thông tin: Địa điểm
├─ Trong KỲ VỌNG: "Nộp tại UBND phường"
├─ Trong THỰC TẾ: "Nộp tại Ủy ban nhân dân cấp xã"
└─ Kết luận: ≈ Tương đương (UBND phường = UBND cấp xã)
```

**❌ SAI (bịa thông tin):**
```
Thông tin: Lệ phí
Kết luận: Có đề cập đến miễn phí
(Nhưng thực tế text không nói gì về lệ phí)
```

**✅ ĐÚNG (thừa nhận không có):**
```
Thông tin: Lệ phí
├─ Trong KỲ VỌNG: "Miễn phí"
├─ Trong THỰC TẾ: KHÔNG CÓ
└─ Kết luận: ✗ Thiếu
```
"""

# ═══════════════════════════════════════════════════════════
# FEW-SHOT EXAMPLES - Ví dụ cụ thể để LLM học
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
- Thông tin 1: CMND ≈ CCCD ✓
- Thông tin 2: Sổ hộ khẩu ≈ Giấy đăng ký hộ khẩu ✓
- Thông tin 3: Xác nhận độc thân ≈ Xác nhận chưa kết hôn ✓
- Thông tin 4: UBND phường ≈ UBND cấp xã ✓
- Giọng điệu: Có xưng hô (anh) ✓
- Kết luận: 4/4 thông tin (100%) → PASSED

Output:
{
  "reasoning": "Kiểm tra 4 thông tin: (1) CMND=CCCD ✓, (2) Sổ hộ khẩu=Giấy đăng ký hộ khẩu ✓, (3) Độc thân=Chưa kết hôn ✓, (4) UBND phường=UBND cấp xã ✓. Đạt 100%. Giọng điệu tốt (có xưng hô).",
  "verdict": "PASSED",
  "confidence_level": 0.95,
  "needs_human_review": false,
  "confidence_reason": "Rõ ràng đủ thông tin, cách diễn đạt tương đương",
  "errors": [],
  "error_desc": "",
  "suggestion": "",
  "suggested_response": "",
  "tone_note": "",
  "time_verdict": "good",
  "time_note": ""
}

---

**VÍ DỤ 2: FAILED - Thiếu thông tin quan trọng**

Câu hỏi: "Thủ tục cấp giấy phép xây dựng cần gì?"
Kỳ vọng: "Cần đơn xin phép, sổ đỏ, bản vẽ thiết kế, CMND. Lệ phí 500.000đ. Thời gian 15 ngày."
Thực tế: "Bạn cần nộp đơn xin phép, sổ đỏ và CMND."

Phân tích:
- Thông tin 1: Đơn xin phép ✓
- Thông tin 2: Sổ đỏ ✓
- Thông tin 3: Bản vẽ thiết kế ✗ (THIẾU)
- Thông tin 4: CMND ✓
- Thông tin 5: Lệ phí ✗ (THIẾU)
- Thông tin 6: Thời gian ✗ (THIẾU)
- Kết luận: 3/6 thông tin (50%) → FAILED

Output:
{
  "reasoning": "Kiểm tra 6 thông tin: (1) Đơn ✓, (2) Sổ đỏ ✓, (3) Bản vẽ ✗, (4) CMND ✓, (5) Lệ phí ✗, (6) Thời gian ✗. Chỉ đạt 50% (3/6). Thiếu 3 thông tin quan trọng.",
  "verdict": "FAILED",
  "confidence_level": 0.9,
  "needs_human_review": false,
  "confidence_reason": "Rõ ràng thiếu nhiều thông tin quan trọng",
  "errors": [
    {
      "description": "Thiếu thông tin về bản vẽ thiết kế - giấy tờ bắt buộc",
      "severity": "Critical",
      "quote": "Response chỉ nói 'đơn xin phép, sổ đỏ và CMND'"
    },
    {
      "description": "Thiếu thông tin về lệ phí",
      "severity": "Major",
      "quote": "Response không đề cập đến lệ phí"
    },
    {
      "description": "Thiếu thông tin về thời gian xử lý",
      "severity": "Major",
      "quote": "Response không đề cập đến thời gian"
    }
  ],
  "error_desc": "Response chưa đầy đủ. User không biết cần chuẩn bị bản vẽ thiết kế, không biết phải trả bao nhiêu tiền lệ phí, và không biết bao lâu sẽ có kết quả.",
  "suggestion": "Cần bổ sung thông tin về bản vẽ thiết kế trong danh sách giấy tờ, nêu rõ lệ phí 500.000đ, và thông báo thời gian xử lý 15 ngày làm việc.",
  "suggested_response": "Bạn cần nộp đơn xin phép, sổ đỏ, bản vẽ thiết kế và CMND. Lệ phí là 500.000đ. Thời gian xử lý khoảng 15 ngày làm việc.",
  "tone_note": "Thiếu xưng hô (anh/chị/em)",
  "time_verdict": "good",
  "time_note": ""
}

---

**VÍ DỤ 3: FAILED - Vi phạm từ khóa CẤM**

Câu hỏi: "Thủ tục đăng ký xe máy cần gì?"
Kỳ vọng: "Cần hóa đơn mua xe, CMND, giấy chứng nhận chất lượng."
Từ khóa CẤM: "bảo hiểm, đăng kiểm"
Thực tế: "Cần hóa đơn, CMND, giấy chất lượng, và bảo hiểm xe."

Phân tích:
- Thông tin đủ: 3/3 ✓
- Từ khóa CẤM: "bảo hiểm" xuất hiện ✗
- Kết luận: Vi phạm từ khóa cấm → FAILED

Output:
{
  "reasoning": "Kiểm tra thông tin: đủ 3/3. NHƯNG response chứa từ khóa CẤM 'bảo hiểm'. Vi phạm nghiêm trọng → FAILED.",
  "verdict": "FAILED",
  "confidence_level": 1.0,
  "needs_human_review": false,
  "confidence_reason": "Vi phạm rõ ràng từ khóa cấm",
  "errors": [
    {
      "description": "Response chứa từ khóa CẤM: 'bảo hiểm'",
      "severity": "Critical",
      "quote": "và bảo hiểm xe"
    }
  ],
  "error_desc": "Response vi phạm từ khóa CẤM: chứa từ 'bảo hiểm'. Từ khóa này không được phép xuất hiện trong response.",
  "suggestion": "Loại bỏ hoàn toàn từ 'bảo hiểm' khỏi response. Chỉ liệt kê các giấy tờ theo đúng quy định.",
  "suggested_response": "Cần hóa đơn mua xe, CMND, và giấy chứng nhận chất lượng.",
  "tone_note": "",
  "time_verdict": "good",
  "time_note": ""
}

---

**VÍ DỤ 4: PASSED - Response dài nhưng đủ thông tin**

Câu hỏi: "Lệ phí đăng ký kết hôn là bao nhiêu?"
Kỳ vọng: "Miễn phí"
Thực tế: "Dạ, theo quy định hiện hành, thủ tục đăng ký kết hôn được miễn phí hoàn toàn, anh chị không phải đóng bất kỳ khoản phí nào ạ."

Phân tích:
- Thông tin cốt lõi: Miễn phí ✓
- Thông tin bổ sung: "theo quy định hiện hành", "không phải đóng bất kỳ khoản phí nào" (không bắt buộc nhưng hữu ích)
- Giọng điệu: Tốt (có xưng hô)
- Kết luận: Đủ thông tin cốt lõi → PASSED

Output:
{
  "reasoning": "Thông tin cốt lõi 'miễn phí' có trong response ('miễn phí hoàn toàn', 'không phải đóng bất kỳ khoản phí nào'). Đạt 100%. Response dài hơn kỳ vọng nhưng không sai, chỉ giải thích thêm.",
  "verdict": "PASSED",
  "confidence_level": 0.95,
  "needs_human_review": false,
  "confidence_reason": "Thông tin đúng và đầy đủ, response dài nhưng không ảnh hưởng",
  "errors": [],
  "error_desc": "",
  "suggestion": "",
  "suggested_response": "",
  "tone_note": "",
  "time_verdict": "good",
  "time_note": ""
}

---

**VÍ DỤ 5: FAILED - Response rỗng**

Câu hỏi: "Thủ tục đổi CMND sang CCCD cần gì?"
Kỳ vọng: "Cần CMND cũ, ảnh 4x6, hộ khẩu."
Thực tế: ""

Phân tích:
- Response rỗng → FAILED

Output:
{
  "reasoning": "Response rỗng, không có nội dung. Không thể đánh giá thông tin. → FAILED.",
  "verdict": "FAILED",
  "confidence_level": 1.0,
  "needs_human_review": false,
  "confidence_reason": "Response rỗng, rõ ràng FAILED",
  "errors": [
    {
      "description": "Response trống, không có nội dung trả lời",
      "severity": "Critical",
      "quote": ""
    }
  ],
  "error_desc": "Response trống hoàn toàn, không có bất kỳ nội dung nào. User không nhận được thông tin gì.",
  "suggestion": "Cần trả lời đầy đủ theo kỳ vọng: liệt kê các giấy tờ cần thiết.",
  "suggested_response": "Cần CMND cũ, ảnh 4x6, và sổ hộ khẩu.",
  "tone_note": "",
  "time_verdict": "good",
  "time_note": ""
}

═══════════════════════════════════════════════════════════
HỌC TỪ CÁC VÍ DỤ TRÊN
═══════════════════════════════════════════════════════════

**BÀI HỌC QUAN TRỌNG:**

1. **Cách diễn đạt khác nhau = OK** (VD1)
   - CMND = CCCD = Căn cước
   - Sổ hộ khẩu = Giấy đăng ký hộ khẩu
   - Độc thân = Chưa kết hôn
   → Chỉ cần Ý NGHĨA giống nhau

2. **Thiếu thông tin = FAILED** (VD2)
   - Phải đếm từng thông tin
   - Tính % = (có / tổng) × 100
   - So sánh với threshold

3. **Vi phạm keywords = FAILED nghiêm trọng** (VD3)
   - Dù thông tin đủ
   - Chỉ cần 1 từ khóa cấm → FAILED

4. **Response dài = OK nếu đúng** (VD4)
   - Không bắt buộc ngắn gọn
   - Thông tin bổ sung hữu ích = không trừ điểm

5. **Response rỗng = FAILED** (VD5)
   - Không cần phân tích gì thêm
   - Suggested_response = copy kỳ vọng

**CÁCH ÁP DỤNG:**
- Đọc kỹ 5 ví dụ trên
- Áp dụng cùng logic cho testcase mới
- Nhất quán về cách đánh giá
- Nhất quán về format output
"""

# Base system message (chung cho tất cả criteria)
BASE_SYSTEM_MESSAGE = """Bạn là chuyên gia đánh giá chatbot response.

NHIỆM VỤ: So sánh câu trả lời THỰC TẾ với KỲ VỌNG và đưa ra đánh giá.

🚫 CÁC TỪ TUYỆT ĐỐI CẤM:
- "Failed:" / "FAILED:" (đặc biệt CẤM ở đầu câu)
- "Verdict:" (bất kỳ dạng nào)

✅ CÁCH VIẾT ĐÚNG:
- ❌ SAI: "Failed: Thiếu thông tin"
- ✅ ĐÚNG: "Thiếu thông tin"

═══════════════════════════════════════════════════════════
PHƯƠNG PHÁP ĐÁNH GIÁ (STEP-BY-STEP)
═══════════════════════════════════════════════════════════

BƯỚC 1: PHÂN TÍCH YÊU CẦU KỲ VỌNG
- Đọc kỹ YÊU CẦU KỲ VỌNG (không phải câu trả lời cụ thể)
- Liệt kê TẤT CẢ yêu cầu quan trọng (từng điểm riêng biệt)
- Xác định yêu cầu nào BẮT BUỘC, yêu cầu nào PHỤ

BƯỚC 2: PHÂN TÍCH THỰC TẾ
- Đọc kỹ câu trả lời THỰC TẾ
- Kiểm tra TỪNG yêu cầu trong kỳ vọng có được đáp ứng không
- Ghi nhận: Yêu cầu nào ĐÃ ĐÁP ỨNG ✓, yêu cầu nào CHƯA ĐÁP ỨNG ✗

BƯỚC 3: KIỂM TRA KEYWORDS (nếu có)
- Từ khóa BẮT BUỘC: Phải xuất hiện trong response
- Từ khóa CẤM: KHÔNG ĐƯỢC xuất hiện trong response
- Vi phạm keywords → FAILED (nghiêm trọng)

BƯỚC 4: ĐÁNH GIÁ CHẤT LƯỢNG
- Tính % thông tin đáp ứng = (số thông tin có / tổng số thông tin) × 100
- So sánh với threshold của tiêu chí đang áp dụng
- Quyết định: PASSED hay FAILED

BƯỚC 5: PHÂN TÍCH LỖI CHI TIẾT (nếu FAILED)
Mô tả lỗi theo cách TỰ NHIÊN, tập trung vào:
- Thông tin nào còn thiếu hoặc sai
- Tác động đến user như thế nào (user không biết gì, không hiểu gì)
- Mức độ nghiêm trọng (Critical/Major/Minor)

⚠️ TUYỆT ĐỐI KHÔNG liệt kê dạng:
- "Thiếu X/Y thông tin"
- "Response thiếu 3/5 điểm: (1)..., (2)..., (3)..."
- Bất kỳ format đếm số nào

✅ Thay vào đó, viết tự nhiên:
- "Response chưa đầy đủ. User không biết [thông tin A], không biết [thông tin B] và không biết [thông tin C]."
- "Thiếu thông tin về [A], [B] và [C], khiến user không thể hiểu rõ quy trình."

═══════════════════════════════════════════════════════════
XỬ LÝ EDGE CASES
═══════════════════════════════════════════════════════════

CASE 1: Response RỖNG hoặc CHỈ CÓ KHOẢNG TRẮNG
→ verdict = "FAILED"
→ error_desc = "Response trống, không có nội dung"
→ suggestion = "Cần trả lời đầy đủ theo kỳ vọng"
→ suggested_response = [copy toàn bộ kỳ vọng]

CASE 2: Response KHÔNG LIÊN QUAN đến câu hỏi
→ verdict = "FAILED"
→ error_desc = "Response không trả lời câu hỏi. Câu hỏi về [X] nhưng response nói về [Y]"
→ suggestion = "Cần tập trung trả lời đúng câu hỏi"
→ suggested_response = [viết response đúng hướng]

CASE 3: Response TỪ CHỐI trả lời ("Tôi không biết", "Không có thông tin")
→ verdict = "FAILED"
→ error_desc = "Bot từ chối trả lời hoặc không có thông tin"
→ suggestion = "Cần cung cấp thông tin theo kỳ vọng"
→ suggested_response = [copy kỳ vọng]

CASE 4: Response QUÁ DÀI (>500 từ) nhưng ĐÚNG
→ verdict = "PASSED" (nếu đủ thông tin)
→ error_desc = ""
→ suggestion = "Response đúng nhưng hơi dài, có thể rút gọn"
→ suggested_response = ""

CASE 5: Response QUÁ NGẮN (<10 từ) nhưng ĐỦ THÔNG TIN
→ verdict = "PASSED" (nếu đủ thông tin)
→ error_desc = ""
→ suggestion = ""
→ suggested_response = ""

CASE 6: Response có THÔNG TIN SAI (khác với kỳ vọng)
→ verdict = "FAILED"
→ error_desc = "Thông tin sai: Response nói [X] nhưng kỳ vọng là [Y]"
→ suggestion = "Sửa thông tin sai từ [X] thành [Y]"
→ suggested_response = [response với thông tin đã sửa]

CASE 7: Response có THÔNG TIN THỪA (không yêu cầu nhưng không sai)
→ verdict = "PASSED" (nếu đủ thông tin bắt buộc)
→ error_desc = ""
→ suggestion = "Response có thông tin thừa nhưng không ảnh hưởng"
→ suggested_response = ""

CASE 8: Vi phạm TỪ KHÓA CẤM
→ verdict = "FAILED" (nghiêm trọng)
→ error_desc = "Response chứa từ khóa cấm: [liệt kê từ khóa]"
→ suggestion = "Loại bỏ các từ khóa cấm: [liệt kê]"
→ suggested_response = [response đã loại bỏ từ khóa cấm]

CASE 9: Thiếu TỪ KHÓA BẮT BUỘC
→ verdict = "FAILED" (nghiêm trọng)
→ error_desc = "Response thiếu từ khóa bắt buộc: [liệt kê từ khóa]"
→ suggestion = "Bổ sung các từ khóa bắt buộc: [liệt kê]"
→ suggested_response = [response đã thêm từ khóa]

═══════════════════════════════════════════════════════════
QUY TẮC OUTPUT
═══════════════════════════════════════════════════════════

NẾU verdict = "PASSED":
- error_desc = ""
- suggestion = ""
- suggested_response = ""
- tone_note = "" (nếu giọng điệu tốt)

NẾU verdict = "FAILED":
- error_desc = MÔ TẢ CHI TIẾT từng lỗi (trả lời 5 câu hỏi ở trên)
- suggestion = HƯỚNG DẪN CỤ THỂ cách sửa (từng bước)
- suggested_response = MẪU response đã sửa (đầy đủ, có thể copy-paste)
- tone_note = Chỉ ghi vấn đề về giọng điệu (nếu có)

⚠️ QUAN TRỌNG:
- CHỈ ghi những gì CÒN THIẾU, SAI
- KHÔNG ghi khen ngợi
- Phải CỤ THỂ, có VÍ DỤ, chỉ rõ VỊ TRÍ
- Mỗi lỗi phải trả lời đủ 5 câu hỏi: Gì? Đâu? Tác động? Mức độ? Sửa thế nào?

═══════════════════════════════════════════════════════════
ĐÁNH GIÁ GIỌNG ĐIỆU - XƯNG HÔ
═══════════════════════════════════════════════════════════

**QUAN TRỌNG:** Chỉ đánh giá XƯNG HÔ, KHÔNG đánh giá dạ/ạ

**Xưng hô hợp lệ:**
- anh/chị/em (phổ biến nhất)
- quý khách (trang trọng)
- bạn (chấp nhận được nếu có trong context)

**Cách kiểm tra:**
1. Tìm xem response có chứa từ xưng hô không
2. Nếu CÓ → tone_note = "" (không ghi gì)
3. Nếu KHÔNG → tone_note = "Thiếu xưng hô (anh/chị/em)"

**Lưu ý:**
- Đa phần response đều có dạ/ạ rồi → KHÔNG cần đánh giá dạ/ạ
- CHỈ tập trung vào xưng hô
- Xưng hô sai (VD: dùng "mày/tao") → tone_note = "Xưng hô không phù hợp"
"""

# Criteria-specific rules
CRITERIA_RULES = {
    "standard": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: CHUẨN (Cân bằng)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. NỘI DUNG: ≥90% thông tin kỳ vọng
   - Đếm tất cả thông tin trong kỳ vọng
   - Kiểm tra bao nhiêu thông tin có trong response
   - Tính % = (có / tổng) × 100
   - ≥90% → PASSED (nếu không vi phạm keywords)
   - <90% → FAILED

2. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

3. THỜI GIAN:
   - ≤3s: Tốt (time_verdict = "good")
   - >3s: Chấp nhận được (time_verdict = "ok", ghi nhận trong time_note)
   - Không ảnh hưởng verdict

4. GIỌNG ĐIỆU:
   - Phải lịch sự, tôn trọng
   - Nên có xưng hô (anh/chị/em/quý khách)
   - Thiếu xưng hô → Ghi vào tone_note, KHÔNG ảnh hưởng verdict
   - Thô lỗ, không tôn trọng → FAILED

QUYẾT ĐỊNH PASSED/FAILED:
- PASSED nếu: ≥90% thông tin + không vi phạm keywords + giọng điệu lịch sự
- FAILED nếu: <90% thông tin HOẶC vi phạm keywords HOẶC giọng điệu thô lỗ
""",
    
    "strict": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: NGHIÊM NGẶT (Yêu cầu cao)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. NỘI DUNG: ≥95% thông tin kỳ vọng
   - Đếm tất cả thông tin trong kỳ vọng
   - Kiểm tra bao nhiêu thông tin có trong response
   - Tính % = (có / tổng) × 100
   - ≥95% → PASSED (nếu không vi phạm keywords)
   - <95% → FAILED
   - Thông tin SAI → FAILED (nghiêm trọng)

2. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

3. THỜI GIAN:
   - ≤2s: Tốt (time_verdict = "good")
   - 2-3s: Chấp nhận được (time_verdict = "ok")
   - >3s: FAILED (quá chậm)

4. GIỌNG ĐIỆU:
   - PHẢI có xưng hô (anh/chị/em/quý khách)
   - PHẢI lịch sự, tự nhiên
   - Thiếu xưng hô → FAILED
   - Thô lỗ → FAILED

QUYẾT ĐỊNH PASSED/FAILED:
- PASSED nếu: ≥95% thông tin + ≤3s + có xưng hô + không vi phạm keywords
- FAILED nếu: <95% thông tin HOẶC >3s HOẶC thiếu xưng hô HOẶC vi phạm keywords
""",
    
    "speed-focused": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: TỐC ĐỘ (Ưu tiên nhanh)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. THỜI GIAN: Quan trọng nhất (bắt buộc)
   - ≤2s: PASSED (nếu nội dung ≥80%)
   - >2s: FAILED (quá chậm, không chấp nhận)

2. NỘI DUNG: ≥80% thông tin kỳ vọng
   - Chỉ kiểm tra nếu thời gian ≤2s
   - Tính % = (có / tổng) × 100
   - ≥80% → PASSED
   - <80% → FAILED

3. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

4. GIỌNG ĐIỆU:
   - KHÔNG đánh giá
   - tone_note = "" (luôn để trống)

QUYẾT ĐỊNH PASSED/FAILED:
- PASSED nếu: ≤2s + ≥80% thông tin + không vi phạm keywords
- FAILED nếu: >2s HOẶC <80% thông tin HOẶC vi phạm keywords
""",
    
    "content-only": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: NỘI DUNG (Chỉ đánh giá độ chính xác)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. NỘI DUNG: ≥95% thông tin kỳ vọng (yêu cầu cao)
   - Đếm tất cả thông tin trong kỳ vọng
   - Kiểm tra bao nhiêu thông tin có trong response
   - Tính % = (có / tổng) × 100
   - ≥95% → PASSED
   - <95% → FAILED
   - Thông tin SAI → FAILED (nghiêm trọng)

2. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

3. THỜI GIAN:
   - KHÔNG đánh giá
   - time_verdict = "good" (luôn)
   - time_note = "" (để trống)

4. GIỌNG ĐIỆU:
   - KHÔNG đánh giá
   - tone_note = "" (luôn để trống)

QUYẾT ĐỊNH PASSED/FAILED:
- PASSED nếu: ≥95% thông tin + không vi phạm keywords
- FAILED nếu: <95% thông tin HOẶC vi phạm keywords
- BỎ QUA thời gian và giọng điệu hoàn toàn
""",
    
    "ux-focused": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: TRẢI NGHIỆM (Ưu tiên thân thiện)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. GIỌNG ĐIỆU: Quan trọng nhất (bắt buộc)
   - PHẢI có xưng hô (anh/chị/em/quý khách)
   - PHẢI lịch sự, tôn trọng
   - PHẢI thân thiện, tự nhiên
   - Thiếu xưng hô → FAILED
   - Thô lỗ, không tôn trọng → FAILED

2. NỘI DUNG: ≥85% thông tin kỳ vọng
   - Chỉ kiểm tra nếu giọng điệu OK
   - Tính % = (có / tổng) × 100
   - ≥85% → PASSED
   - <85% → FAILED

3. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

4. THỜI GIAN:
   - ≤3s: Tốt (time_verdict = "good")
   - >3s: Chấp nhận được (time_verdict = "ok")
   - Không ảnh hưởng verdict

QUYẾT ĐỊNH PASSED/FAILED:
- PASSED nếu: Có xưng hô + lịch sự + ≥85% thông tin + không vi phạm keywords
- FAILED nếu: Thiếu xưng hô HOẶC thô lỗ HOẶC <85% thông tin HOẶC vi phạm keywords
"""
}


def create_simple_judge_prompt(
    question: str,
    expected: str,
    actual: str,
    time_label: str,
    criteria: str = "standard",
    required_keywords: str = None,
    forbidden_keywords: str = None,
    inject_knowledge: bool = True
) -> str:
    """
    Tạo prompt cho judge với criteria cụ thể
    
    Args:
        question: Câu hỏi
        expected: YÊU CẦU KỲ VỌNG (không phải câu trả lời cụ thể)
        actual: Câu trả lời thực tế
        time_label: Thời gian (VD: "2000ms (Nhanh)")
        criteria: Tiêu chí (standard/strict/speed-focused/content-only/ux-focused)
        required_keywords: Từ khóa bắt buộc
        forbidden_keywords: Từ khóa cấm
        inject_knowledge: Có inject knowledge base không (default: True)
    """
    
    # Import improvements
    try:
        from prompt_improvements import (
            get_error_analysis_template,
            get_consistency_check
        )
        error_analysis = get_error_analysis_template()
        consistency_check = get_consistency_check()
    except ImportError:
        error_analysis = ""
        consistency_check = ""
    
    # Get criteria-specific rules
    criteria_rule = CRITERIA_RULES.get(criteria, CRITERIA_RULES["standard"])
    
    # Build keywords section
    keywords_section = ""
    if required_keywords:
        keywords_section += f"\n**Từ khóa BẮT BUỘC:** {required_keywords}"
    if forbidden_keywords:
        keywords_section += f"\n**Từ khóa CẤM:** {forbidden_keywords}"
    
    # Inject knowledge base (if enabled)
    knowledge_section = ""
    if inject_knowledge:
        try:
            from knowledge import search_relevant_knowledge
            knowledge_text = search_relevant_knowledge(question, top_k=2)
            if knowledge_text and "Không tìm thấy" not in knowledge_text:
                knowledge_section = f"""
═══════════════════════════════════════════════════════════
KNOWLEDGE BASE - THÔNG TIN THAM KHẢO
═══════════════════════════════════════════════════════════

{knowledge_text}

**LƯU Ý:** Sử dụng thông tin trên để:
- Đối chiếu xem response có đầy đủ thông tin theo quy định không
- Kiểm tra tính chính xác (thời hạn, phí lệ phí, điều kiện...)
- Gợi ý bổ sung thông tin còn thiếu dựa trên thủ tục chuẩn

"""
        except Exception as e:
            print(f"⚠️ Failed to inject knowledge: {str(e)}")
            knowledge_section = ""
    
    prompt = f"""{BASE_SYSTEM_MESSAGE}

{GROUNDING_REQUIREMENT}

{FEW_SHOT_EXAMPLES}

{error_analysis}

{criteria_rule}
{knowledge_section}
═══════════════════════════════════════════════════════════
DỮ LIỆU CẦN ĐÁNH GIÁ
═══════════════════════════════════════════════════════════

**Câu hỏi:** {question}

**Yêu cầu kỳ vọng:** {expected}
{keywords_section}

**Thực tế:** {actual}

**Thời gian:** {time_label}

═══════════════════════════════════════════════════════════
YÊU CẦU OUTPUT
═══════════════════════════════════════════════════════════

Trả về JSON với các trường:

1. **reasoning**: Suy luận chi tiết theo 5 bước
   - Bước 1: Liệt kê thông tin trong kỳ vọng
   - Bước 2: Kiểm tra thông tin trong thực tế
   - Bước 3: Kiểm tra keywords (nếu có)
   - Bước 4: Tính % đáp ứng và so sánh threshold
   - Bước 5: Quyết định verdict với lý do

2. **verdict**: "PASSED" hoặc "FAILED"

3. **confidence_level**: 0.0-1.0 (độ tự tin về đánh giá)
   - 0.9-1.0: Rất chắc chắn
   - 0.7-0.9: Khá chắc chắn
   - <0.7: Cần human review

4. **needs_human_review**: true/false
   - true nếu: confidence < 0.7, hoặc edge case phức tạp, hoặc không chắc chắn

5. **confidence_reason**: Lý do về độ tự tin

6. **errors**: Array các lỗi (nếu có), mỗi lỗi có:
   - description: Mô tả lỗi một cách tự nhiên, chi tiết
   - severity: "Critical" / "Major" / "Minor"
   - quote: Trích dẫn phần sai (nếu có)

7. **error_desc**: Nhận xét lỗi tự nhiên (nếu FAILED)
   - Nếu PASSED → ""
   - Nếu FAILED → Mô tả lỗi theo cách tự nhiên, KHÔNG liệt kê dạng "thiếu X/Y thông tin"
   - Ví dụ ĐÚNG: "Response chưa đầy đủ. User không biết quy trình thực hiện, không biết kết quả sẽ được công bố như thế nào và không biết có những hình thức rà soát nào."
   - Ví dụ SAI: "Response thiếu 3/5 thông tin: (1) Quy trình, (2) Kết quả công bố, (3) Hình thức"

8. **suggestion**: Gợi ý cải thiện (nếu FAILED)
   - Nếu PASSED → ""
   - Nếu FAILED → Đưa ra gợi ý cải thiện cụ thể, tự nhiên
   - KHÔNG liệt kê dạng "Bước 1, Bước 2, Bước 3"
   - Ví dụ: "Cần bổ sung thông tin về quy trình thực hiện, cách thức công bố kết quả và các hình thức rà soát có sẵn."

9. **suggested_response**: Mẫu response đã sửa (nếu FAILED)
   - Nếu PASSED → ""
   - Nếu FAILED → Response hoàn chỉnh, có thể copy-paste

10. **tone_note**: Nhận xét giọng điệu (chỉ ghi vấn đề)
    - Nếu tốt → ""
    - Nếu có vấn đề → Mô tả cụ thể

11. **time_verdict**: "good" / "ok" / "slow"

12. **time_note**: Nhận xét thời gian

═══════════════════════════════════════════════════════════
LƯU Ý QUAN TRỌNG
═══════════════════════════════════════════════════════════

✅ PHẢI LÀM:
- Kiểm tra edge cases (rỗng, không liên quan, từ chối, sai thông tin)
- Phân tích lỗi chi tiết (5 câu hỏi: Gì? Đâu? Tác động? Mức độ? Sửa thế nào?)
- Đưa ra suggested_response cụ thể (có thể copy-paste)
- Tự đánh giá confidence và yêu cầu human review nếu không chắc

🚫 TUYỆT ĐỐI KHÔNG:
- Dùng "Failed:", "Verdict:", "PASSED/FAILED" trong error_desc/suggestion
- Khen ngợi trong tone_note
- Để trống error_desc/suggestion khi verdict=FAILED
- Đánh giá chung chung, không cụ thể

**Áp dụng ĐÚNG tiêu chí: {criteria}**
"""
    
    return prompt
