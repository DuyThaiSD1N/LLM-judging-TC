"""
SIMPLIFIED JUDGE PROMPT - Hỗ trợ 5 tiêu chí đánh giá khác nhau
Chỉ xét: Nội dung + Keywords + Thời gian + Giọng điệu
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

BƯỚC 1: PHÂN TÍCH KỲ VỌNG
- Đọc kỹ câu trả lời KỲ VỌNG
- Liệt kê TẤT CẢ thông tin quan trọng (từng điểm riêng biệt)
- Xác định thông tin nào BẮT BUỘC, thông tin nào PHỤ

BƯỚC 2: PHÂN TÍCH THỰC TẾ
- Đọc kỹ câu trả lời THỰC TẾ
- Kiểm tra TỪNG thông tin trong kỳ vọng có xuất hiện không
- Ghi nhận: Thông tin nào ĐÃ CÓ ✓, thông tin nào THIẾU ✗

BƯỚC 3: KIỂM TRA KEYWORDS (nếu có)
- Từ khóa BẮT BUỘC: Phải xuất hiện trong response
- Từ khóa CẤM: KHÔNG ĐƯỢC xuất hiện trong response
- Vi phạm keywords → FAILED (nghiêm trọng)

BƯỚC 4: ĐÁNH GIÁ CHẤT LƯỢNG
- Tính % thông tin đáp ứng = (số thông tin có / tổng số thông tin) × 100
- So sánh với threshold của tiêu chí đang áp dụng
- Quyết định: PASSED hay FAILED

BƯỚC 5: PHÂN TÍCH LỖI CHI TIẾT (nếu FAILED)
Với MỖI lỗi, phải trả lời 5 câu hỏi:
1. LỖI GÌ? (thiếu thông tin / sai thông tin / không rõ ràng / không liên quan)
2. THIẾU Ở ĐÂU? (đầu / giữa / cuối response, hoặc thiếu hoàn toàn)
3. TÁC ĐỘNG GÌ? (user không hiểu / không làm được / hiểu sai / mất thời gian)
4. MỨC ĐỘ? (Critical: không dùng được / Major: khó khăn / Minor: chưa tối ưu)
5. SỬA NHƯ THẾ NÀO? (bổ sung gì, ở vị trí nào, với format ra sao)

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
"""

# Criteria-specific rules
CRITERIA_RULES = {
    "standard": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: CHUẨN (Cân bằng)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. NỘI DUNG: Response phải đáp ứng phần lớn thông tin kỳ vọng
   - Nếu đáp ứng ≥90% thông tin → có thể PASSED
   - Nếu < 90% → FAILED
   - Thông tin SAI → FAILED (nghiêm trọng)

2. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

3. THỜI GIAN:
   - ≤3s: Tốt, không ghi nhận
   - >3s: Ghi nhận trong time_note, nhưng KHÔNG ảnh hưởng verdict

4. GIỌNG ĐIỆU:
   - Phải có xưng hô (anh/chị/em/quý khách)
   - Phải lịch sự, tôn trọng
   - Thiếu xưng hô → Ghi vào tone_note, nhưng KHÔNG ảnh hưởng verdict
   - Thô lỗ, thiếu tôn trọng → FAILED

CÁCH TỰ ĐÁNH GIÁ:
- Liệt kê tất cả thông tin trong kỳ vọng
- Đếm có bao nhiêu thông tin trong response
- Tính % = (có / tổng) × 100
- Nếu ≥90% + không vi phạm keywords + giọng điệu OK → PASSED
""",
    
    "strict": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: NGHIÊM NGẶT (Yêu cầu cao)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. NỘI DUNG: Response phải đáp ứng hầu hết thông tin kỳ vọng
   - Nếu đáp ứng ≥95% thông tin → có thể PASSED
   - Nếu < 95% → FAILED
   - Thông tin SAI → FAILED (nghiêm trọng)
   - Thông tin KHÔNG RÕ RÀNG → FAILED

2. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

3. THỜI GIAN:
   - ≤2s: Tốt
   - 2-3s: Chấp nhận được, ghi nhận
   - >3s: FAILED (quá chậm)

4. GIỌNG ĐIỆU:
   - PHẢI có xưng hô (anh/chị/em/quý khách)
   - PHẢI có dạ/ạ/vâng
   - Thiếu xưng hô hoặc dạ/ạ → FAILED
   - Thô lỗ → FAILED

CÁCH TỰ ĐÁNH GIÁ:
- Liệt kê tất cả thông tin trong kỳ vọng
- Đếm có bao nhiêu thông tin trong response
- Tính % = (có / tổng) × 100
- Kiểm tra thời gian, giọng điệu
- Nếu ≥95% + ≤3s + có dạ/ạ + không vi phạm keywords → PASSED
- BẤT KỲ lỗi nhỏ nào cũng phải ghi nhận chi tiết
""",
    
    "speed-focused": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: TỐC ĐỘ (Ưu tiên nhanh)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. THỜI GIAN: Quan trọng nhất
   - ≤2s: PASSED (nếu nội dung đủ tốt)
   - >2s: FAILED (quá chậm, không chấp nhận)

2. NỘI DUNG: Yêu cầu thấp hơn
   - Nếu đáp ứng ≥80% thông tin → có thể PASSED
   - Nếu < 80% → FAILED
   - Thông tin SAI → FAILED

3. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

4. GIỌNG ĐIỆU:
   - KHÔNG đánh giá
   - tone_note = "" (luôn để trống)

CÁCH TỰ ĐÁNH GIÁ:
- Kiểm tra thời gian TRƯỚC
- Nếu >2s → FAILED ngay (không cần kiểm tra nội dung)
- Nếu ≤2s → Kiểm tra nội dung
- Nếu ≥80% thông tin + không vi phạm keywords → PASSED
""",
    
    "content-only": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: NỘI DUNG (Chỉ đánh giá độ chính xác)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. NỘI DUNG: Quan trọng nhất, yêu cầu cao
   - Nếu đáp ứng ≥95% thông tin → có thể PASSED
   - Nếu < 95% → FAILED
   - Thông tin SAI → FAILED (nghiêm trọng)
   - Thông tin KHÔNG RÕ RÀNG → FAILED

2. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

3. THỜI GIAN:
   - KHÔNG đánh giá
   - time_verdict = "good" (luôn)
   - time_note = "Không đánh giá thời gian"

4. GIỌNG ĐIỆU:
   - KHÔNG đánh giá
   - tone_note = "" (luôn để trống)

CÁCH TỰ ĐÁNH GIÁ:
- CHỈ tập trung vào nội dung
- Liệt kê tất cả thông tin trong kỳ vọng
- Đếm có bao nhiêu thông tin trong response
- Tính % = (có / tổng) × 100
- Nếu ≥95% + không vi phạm keywords → PASSED
- BỎ QUA thời gian và giọng điệu hoàn toàn
""",
    
    "ux-focused": """
═══════════════════════════════════════════════════════════
TIÊU CHÍ: TRẢI NGHIỆM (Ưu tiên thân thiện)
═══════════════════════════════════════════════════════════

NGUYÊN TẮC ĐÁNH GIÁ:
1. GIỌNG ĐIỆU: Quan trọng nhất
   - PHẢI thân thiện, tự nhiên
   - PHẢI có xưng hô
   - PHẢI lịch sự, tôn trọng
   - Nên có cảm xúc tích cực (vui vẻ, nhiệt tình)
   - Thiếu xưng hô → FAILED
   - Khô khan, máy móc → FAILED
   - Thô lỗ → FAILED

2. NỘI DUNG: Yêu cầu thấp hơn
   - Nếu đáp ứng ≥85% thông tin → có thể PASSED
   - Nếu < 85% → FAILED
   - Thông tin SAI → FAILED

3. KEYWORDS:
   - Thiếu từ khóa BẮT BUỘC → FAILED
   - Có từ khóa CẤM → FAILED

4. THỜI GIAN:
   - ≤3s: Tốt
   - >3s: Ghi nhận, nhưng KHÔNG ảnh hưởng verdict

CÁCH TỰ ĐÁNH GIÁ:
- Kiểm tra giọng điệu TRƯỚC
- Nếu thiếu xưng hô hoặc không thân thiện → FAILED
- Nếu giọng điệu OK → Kiểm tra nội dung
- Nếu ≥85% thông tin + không vi phạm keywords → PASSED
"""
}


def create_simple_judge_prompt(
    question: str,
    expected: str,
    actual: str,
    time_label: str,
    criteria: str = "standard",
    required_keywords: str = None,
    forbidden_keywords: str = None
) -> str:
    """
    Tạo prompt cho judge với criteria cụ thể
    
    Args:
        question: Câu hỏi
        expected: Câu trả lời kỳ vọng
        actual: Câu trả lời thực tế
        time_label: Thời gian (VD: "2000ms (Nhanh)")
        criteria: Tiêu chí (standard/strict/speed-focused/content-only/ux-focused)
        required_keywords: Từ khóa bắt buộc
        forbidden_keywords: Từ khóa cấm
    """
    
    # Get criteria-specific rules
    criteria_rule = CRITERIA_RULES.get(criteria, CRITERIA_RULES["standard"])
    
    # Build keywords section
    keywords_section = ""
    if required_keywords:
        keywords_section += f"\n**Từ khóa BẮT BUỘC:** {required_keywords}"
    if forbidden_keywords:
        keywords_section += f"\n**Từ khóa CẤM:** {forbidden_keywords}"
    
    prompt = f"""{BASE_SYSTEM_MESSAGE}

{criteria_rule}

═══════════════════════════════════════════════════════════
DỮ LIỆU CẦN ĐÁNH GIÁ
═══════════════════════════════════════════════════════════

**Câu hỏi:** {question}

**Kỳ vọng:** {expected}
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
   - description: Mô tả lỗi (trả lời 5 câu hỏi: Gì? Đâu? Tác động? Mức độ? Sửa thế nào?)
   - severity: "Critical" / "Major" / "Minor"
   - quote: Trích dẫn phần sai (nếu có)

7. **error_desc**: Tóm tắt tất cả lỗi (nếu FAILED)
   - Nếu PASSED → ""
   - Nếu FAILED → Mô tả chi tiết từng lỗi

8. **suggestion**: Hướng dẫn sửa (nếu FAILED)
   - Nếu PASSED → ""
   - Nếu FAILED → Hướng dẫn cụ thể từng bước

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
