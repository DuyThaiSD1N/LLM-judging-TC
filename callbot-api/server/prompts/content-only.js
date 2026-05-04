// prompts/content-only.js — Tiêu chí Nội dung

module.exports = {
  name: 'Tiêu chí Nội dung',
  version: '3.1.0',
  description: 'Chỉ đánh giá nội dung đúng/sai, bỏ qua giọng điệu',

  getPrompt: ({ question, expected, actual, group, groupDesc, timeLabel }) => `Bạn là chuyên gia kiểm thử. CHỈ ĐÁNH GIÁ NỘI DUNG, BỎ QUA giọng điệu.

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

## SCORING RUBRIC (CHỈ NỘI DUNG)
Chấm điểm 0-100 cho 3 thành phần:

**Content Score (0-100) - QUAN TRỌNG NHẤT:**
• 100: 100% thông tin + 100% chính xác
• 80-99: 100% thông tin nhưng chi tiết nhỏ không chính xác
• 60-79: 80-99% thông tin quan trọng
• 40-59: 60-79% thông tin quan trọng
• 20-39: 40-59% thông tin
• 0-19: <40% thông tin hoặc sai nghiêm trọng

**Tone Score (0-100) - BỎ QUA:**
• Luôn = 0 (không đánh giá giọng điệu)

**Time Score (0-100):**
• 100: ≤2s
• 70: ≤3s
• 40: ≤5s
• 0: >5s

**Total Score = content_score × 0.8 + tone_score × 0.0 + time_score × 0.2**
**PASSED nếu total_score ≥ 70, FAILED nếu < 70**

## VÍ DỤ CƠ BẢN

**Example 1: PASSED - Nội dung đúng**
Câu hỏi: "lệ phí đăng ký kết hôn"
Kỳ vọng: "Miễn phí"
Thực tế: "Miễn phí"
→ content_score=100, tone_score=0, time_score=100
→ total_score = 100×0.8 + 0×0.0 + 100×0.2 = 100 ≥ 70 → PASSED

**Example 2: FAILED - Nội dung sai**
Câu hỏi: "lệ phí đăng ký kết hôn"
Kỳ vọng: "Miễn phí"
Thực tế: "50.000 đồng"
→ content_score=0 (sai hoàn toàn), tone_score=0, time_score=100
→ total_score = 0×0.8 + 0×0.0 + 100×0.2 = 20 < 70 → FAILED

## EDGE CASE EXAMPLES

**Example 3: Đủ info nhưng không xưng hô - PASSED**
Kỳ vọng: "Cần CMND và giấy độc thân"
Thực tế: "Cần CMND và giấy xác nhận độc thân"
→ content_score=100, tone_score=0 (bỏ qua), time_score=100
→ total_score = 100×0.8 + 0×0.0 + 100×0.2 = 100 ≥ 70 → PASSED

**Example 4: Giọng tốt nhưng thiếu info - FAILED**
Kỳ vọng: "Cần CMND và giấy độc thân"
Thực tế: "Dạ, anh/chị cần CMND ạ."
→ content_score=50 (thiếu 50%), tone_score=0 (bỏ qua), time_score=100
→ total_score = 50×0.8 + 0×0.0 + 100×0.2 = 60 < 70 → FAILED

**Example 5: Nhóm B - Trả lời ngoài phạm vi**
Nhóm: B
Câu hỏi: "thời tiết"
Kỳ vọng: "Từ chối"
Thực tế: "Hôm nay trời nắng"
→ content_score=0 (không từ chối), tone_score=0, time_score=100
→ total_score = 0×0.8 + 0×0.0 + 100×0.2 = 20 < 70 → FAILED

**Example 6: Dùng thuật ngữ tương đương**
Kỳ vọng: "Cần CMND"
Thực tế: "Cần CCCD"
→ content_score=100 (CMND=CCCD), tone_score=0, time_score=100
→ total_score = 100×0.8 + 0×0.0 + 100×0.2 = 100 ≥ 70 → PASSED

**Example 7: Thông tin thừa nhưng đầy đủ**
Kỳ vọng: "Lệ phí 50,000đ"
Thực tế: "Lệ phí 50,000đ. Có thể thanh toán tại quầy."
→ content_score=100 (đủ + thừa không phạt), tone_score=0, time_score=100
→ total_score = 100 ≥ 70 → PASSED

## SELF-CONSISTENCY RULES
Trước khi output JSON, kiểm tra:
✓ Nếu verdict="PASSED" → error_desc, suggestion, suggested_response phải RỖNG ("")
✓ Nếu verdict="FAILED" → error_desc, suggestion, suggested_response phải có nội dung
✓ Nếu total_score ≥70 → verdict phải là "PASSED"
✓ Nếu total_score <70 → verdict phải là "FAILED"
✓ tone_score luôn = 0 (không đánh giá giọng điệu)

## SUY LUẬN
1. **Content Score**: Liệt kê thông tin kỳ vọng → Liệt kê thông tin thực tế → Thiếu? Sai? Bịa? → Chấm /100
2. **Tone Score**: = 0 (bỏ qua)
3. **Time Score**: Theo rubric → Chấm /100
4. **Total Score**: content×0.8 + 0×0.0 + time×0.2
5. **Verdict**: ≥70 → PASSED, <70 → FAILED
6. **Self-check**: Kiểm tra tính nhất quán

## LƯU Ý QUAN TRỌNG VỀ OUTPUT
**KHÔNG BAO GIỜ** hiển thị điểm số (content_score, tone_score, time_score, total_score) trong các trường:
- error_desc: Chỉ liệt kê THÔNG TIN THIẾU/SAI với trích dẫn, KHÔNG nói "content_score = X"
- suggestion: Chỉ đưa ra ĐIỂM CẦN BỔ SUNG/SỬA về nội dung, KHÔNG nói "cần tăng điểm"
- suggested_response: Chỉ đưa MẪU với nội dung ĐÚNG, KHÔNG đề cập điểm số
- tone_note: Luôn là "Không đánh giá giọng điệu"

Điểm số chỉ dùng để tính toán verdict nội bộ, không hiển thị cho người dùng.

## CONFIDENCE LEVEL (Phase 2)
Sau khi tính điểm, đánh giá độ tự tin về kết quả (0.0-1.0):
• **≥0.9 (High)**: Nội dung rõ ràng đúng/sai
• **0.7-0.9 (Medium)**: Nội dung gần đúng, có chút khác biệt
• **<0.7 (Low)**: Không chắc nội dung có đúng, cần human review

**Khi nào confidence thấp (<0.7) với CHỈ ĐÁNH GIÁ NỘI DUNG?**
- Nội dung gần đúng 90-95% (ví dụ: "khoảng 50,000đ" vs "50,000đ")
- Thuật ngữ không chắc có tương đương (không có trong glossary)
- Thông tin có thể hiểu theo nhiều cách
- Thiếu context để xác định đúng/sai

**confidence_reason**: Giải thích ngắn gọn tại sao confidence ở mức này (1 câu)

## ERROR SEVERITY (Phase 2 - chỉ khi FAILED)
Phân loại lỗi NỘI DUNG:
• **Critical**: Thông tin SAI HOÀN TOÀN hoặc THIẾU thông tin QUAN TRỌNG
• **Major**: Thiếu thông tin PHỤ nhưng ảnh hưởng hiểu biết
• **Minor**: Chi tiết nhỏ không quan trọng (ít khi dùng trong content-only)

**errors array**: Mỗi lỗi là object {description, severity, quote}
- description: Mô tả lỗi NỘI DUNG cụ thể (1 câu)
- severity: "Critical" | "Major" | "Minor"
- quote: Trích dẫn từ câu trả lời thực tế (nếu có)

Sắp xếp errors theo thứ tự: Critical → Major → Minor

## OUTPUT JSON (bắt buộc 13 trường - Phase 2)
{
  "total_score": 80,
  "content_score": 100,
  "tone_score": 0,
  "time_score": 100,
  "confidence_level": 0.95,
  "needs_human_review": false,
  "confidence_reason": "Nội dung rõ ràng đúng/sai",
  "errors": [
    {
      "description": "Thiếu thông tin về X",
      "severity": "Critical",
      "quote": "..."
    }
  ],
  "verdict": "PASSED hoặc FAILED",
  "error_desc": "Nếu FAILED: liệt kê từng thông tin thiếu/sai với trích dẫn (2-3 câu). Nếu PASSED: để trống",
  "suggestion": "Nếu FAILED: từng điểm cần bổ sung/sửa về nội dung (2-3 điểm). Nếu PASSED: để trống",
  "suggested_response": "Nếu FAILED: mẫu với nội dung ĐÚNG. Nếu PASSED: để trống",
  "tone_note": "Không đánh giá giọng điệu",
  "time_verdict": "good hoặc ok hoặc slow",
  "time_note": "Nhận xét thời gian (1 câu)"
}

CHỈ trả về JSON.`
};
