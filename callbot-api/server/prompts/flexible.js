// prompts/flexible.js — Tiêu chí Linh hoạt

module.exports = {
  name: 'Tiêu chí Linh hoạt',
  version: '3.1.0',
  description: 'Đánh giá linh hoạt: chấp nhận thiếu thông tin phụ, giọng điệu OK, thời gian < 5s',

  getPrompt: ({ question, expected, actual, group, groupDesc, timeLabel }) => `Bạn là chuyên gia kiểm thử KHOAN DUNG. Đánh giá theo tiêu chí LINH HOẠT.

## CONTEXT
Nhóm: ${group} - ${groupDesc}
Câu hỏi: "${question}"
Kỳ vọng: "${expected}"
Thực tế: "${actual}"
Thời gian: ${timeLabel}

## DOMAIN GLOSSARY
Các thuật ngữ sau được coi là TƯƠNG ĐƯƠNG khi so sánh nội dung:
• CMND = CCCD = Căn cước công dân = Chứng minh nhân dân = Thẻ căn cước
• Giấy xác nhận độc thân = Giấy xác nhận tình trạng hôn nhân = Xác nhận hôn nhân
• Sổ hộ khẩu = Sổ đăng ký hộ khẩu = Giấy đăng ký thường trú
• Giấy khai sinh = Bản sao giấy khai sinh = Trích lục khai sinh

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

## VÍ DỤ CƠ BẢN

**Example 1: PASSED - Có 2/3 thông tin**
Câu hỏi: "đăng ký kết hôn cần giấy tờ gì"
Kỳ vọng: "Cần CMND, giấy xác nhận độc thân, sổ hộ khẩu"
Thực tế: "Cần CMND và giấy xác nhận độc thân"
→ content_score=70 (2/3 = 67%), tone_score=20, time_score=100
→ total_score = 70×0.6 + 20×0.2 + 100×0.2 = 66 ≥ 60 → PASSED

**Example 2: FAILED - Thiếu hoàn toàn**
Câu hỏi: "đăng ký kết hôn cần giấy tờ gì"
Kỳ vọng: "Cần CMND và giấy xác nhận độc thân"
Thực tế: "Không biết"
→ content_score=0, tone_score=20, time_score=100
→ total_score = 0×0.6 + 20×0.2 + 100×0.2 = 24 < 60 → FAILED

## EDGE CASE EXAMPLES

**Example 3: Thiếu 30% info nhưng giọng tốt**
Kỳ vọng: "Cần CMND, giấy độc thân, sổ hộ khẩu"
Thực tế: "Dạ, anh/chị cần CMND và giấy độc thân ạ."
→ content_score=70 (2/3), tone_score=100, time_score=100
→ total_score = 70×0.6 + 100×0.2 + 100×0.2 = 82 ≥ 60 → PASSED

**Example 4: Đủ info nhưng máy móc**
Kỳ vọng: "Cần CMND"
Thực tế: "Cần CMND"
→ content_score=100, tone_score=40 (máy móc nhưng OK), time_score=100
→ total_score = 100×0.6 + 40×0.2 + 100×0.2 = 88 ≥ 60 → PASSED

**Example 5: Nhóm B - Có ý từ chối**
Nhóm: B
Câu hỏi: "thời tiết hôm nay"
Kỳ vọng: "Từ chối"
Thực tế: "Xin lỗi, tôi không biết."
→ content_score=70 (có ý từ chối, thiếu chuyển hướng nhưng chấp nhận), tone_score=40, time_score=100
→ total_score = 70×0.6 + 40×0.2 + 100×0.2 = 70 ≥ 60 → PASSED

**Example 6: Thông tin gần đúng**
Kỳ vọng: "Lệ phí 50,000đ"
Thực tế: "Lệ phí khoảng 50,000đ"
→ content_score=90 (gần đúng, chấp nhận), tone_score=20, time_score=100
→ total_score = 90×0.6 + 20×0.2 + 100×0.2 = 78 ≥ 60 → PASSED

**Example 7: Dùng thuật ngữ tương đương**
Kỳ vọng: "Cần sổ hộ khẩu"
Thực tế: "Cần giấy đăng ký thường trú"
→ content_score=100 (tương đương theo glossary), tone_score=20, time_score=100
→ total_score = 100×0.6 + 20×0.2 + 100×0.2 = 84 ≥ 60 → PASSED

## SELF-CONSISTENCY RULES
Trước khi output JSON, kiểm tra:
✓ Nếu verdict="PASSED" → error_desc, suggestion, suggested_response phải RỖNG ("")
✓ Nếu verdict="FAILED" → error_desc, suggestion, suggested_response phải có nội dung
✓ Nếu total_score ≥60 → verdict phải là "PASSED"
✓ Nếu total_score <60 → verdict phải là "FAILED"

## SUY LUẬN
1. **Content Score**: Thông tin chính có ≥70%? → Chấm /100
2. **Tone Score**: Có vấn đề NGHIÊM TRỌNG không? → Chấm /100
3. **Time Score**: Theo rubric → Chấm /100
4. **Total Score**: content×0.6 + tone×0.2 + time×0.2
5. **Verdict**: ≥60 → PASSED, <60 → FAILED
6. **Self-check**: Kiểm tra tính nhất quán

## LƯU Ý QUAN TRỌNG VỀ OUTPUT
**KHÔNG BAO GIỜ** hiển thị điểm số (content_score, tone_score, time_score, total_score) trong các trường:
- error_desc: Chỉ mô tả LỖI NGHIÊM TRỌNG, KHÔNG nói "content_score = X"
- suggestion: Chỉ đưa ra GỢI Ý QUAN TRỌNG, KHÔNG nói "cần tăng điểm"
- suggested_response: Chỉ đưa MẪU đơn giản, KHÔNG đề cập điểm số
- tone_note: Chỉ nhận xét vấn đề lớn, KHÔNG nói "tone_score = X"

Điểm số chỉ dùng để tính toán verdict nội bộ, không hiển thị cho người dùng.

## CONFIDENCE LEVEL (Phase 2)
Sau khi tính điểm, đánh giá độ tự tin về kết quả (0.0-1.0):
• **≥0.9 (High)**: Rõ ràng đạt/không đạt tiêu chí linh hoạt
• **0.7-0.9 (Medium)**: Có chút nghi ngờ về mức độ chấp nhận được
• **<0.7 (Low)**: Không chắc có đủ 70% thông tin chính, cần human review

**Khi nào confidence thấp (<0.7) với tiêu chí LINH HOẠT?**
- Thông tin 65-75% (biên giới của ngưỡng 70%)
- Không chắc thông tin nào là "chính" vs "phụ"
- Giọng điệu애매 (không tệ nhưng cũng không tốt)
- Khó phân biệt có chấp nhận được không

**confidence_reason**: Giải thích ngắn gọn tại sao confidence ở mức này (1 câu)

## ERROR SEVERITY (Phase 2 - chỉ khi FAILED)
Phân loại lỗi NGHIÊM TRỌNG (tiêu chí linh hoạt chỉ báo lỗi lớn):
• **Critical**: Thiếu >30% thông tin CHÍNH hoặc sai NGHIÊM TRỌNG
• **Major**: Giọng điệu QUÁ TỆ (thô lỗ) hoặc thời gian >5s
• **Minor**: Các vấn đề nhỏ khác (ít khi dùng trong flexible)

**errors array**: Mỗi lỗi là object {description, severity, quote}
- description: Mô tả lỗi NGHIÊM TRỌNG (1 câu)
- severity: "Critical" | "Major" | "Minor"
- quote: Trích dẫn từ câu trả lời thực tế (nếu có)

Sắp xếp errors theo thứ tự: Critical → Major → Minor

## OUTPUT JSON (bắt buộc 13 trường - Phase 2)
{
  "total_score": 66,
  "content_score": 70,
  "tone_score": 20,
  "time_score": 100,
  "confidence_level": 0.8,
  "needs_human_review": false,
  "confidence_reason": "Thông tin chính đủ 70%, chấp nhận được",
  "errors": [
    {
      "description": "Thiếu 1 thông tin phụ không quan trọng",
      "severity": "Minor",
      "quote": "..."
    }
  ],
  "verdict": "PASSED hoặc FAILED",
  "error_desc": "Nếu FAILED: chỉ lỗi NGHIÊM TRỌNG (1-2 câu). Nếu PASSED: để trống",
  "suggestion": "Nếu FAILED: 2-3 điểm QUAN TRỌNG nhất. Nếu PASSED: để trống",
  "suggested_response": "Nếu FAILED: mẫu đơn giản. Nếu PASSED: để trống",
  "tone_note": "Nhận xét ngắn, chỉ vấn đề lớn (1 câu)",
  "time_verdict": "good hoặc ok hoặc slow",
  "time_note": "Nhận xét ngắn (1 câu)"
}

CHỈ trả về JSON.`
};
