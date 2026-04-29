// prompts/content-only.js — Tiêu chí Nội dung

module.exports = {
  name: 'Tiêu chí Nội dung',
  version: '2.0.0',
  description: 'Chỉ đánh giá nội dung đúng/sai, bỏ qua giọng điệu và độ ngắn gọn',

  getPrompt: ({ question, expected, actual, group, groupDesc, timeLabel }) => `Bạn là chuyên gia kiểm thử. CHỈ ĐÁNH GIÁ NỘI DUNG, BỎ QUA giọng điệu và độ dài.

## CONTEXT
Nhóm: ${group} - ${groupDesc}
Câu hỏi: "${question}"
Kỳ vọng: "${expected}"
Thực tế: "${actual}"
Thời gian: ${timeLabel}

## CHỈ ĐÁNH GIÁ NỘI DUNG
**PASSED khi:**
• Có TẤT CẢ thông tin quan trọng trong kỳ vọng
• Thông tin đúng, không sai lệch, không bịa
• Nhóm B: từ chối nội dung ngoài phạm vi

**FAILED khi:**
• Thiếu thông tin quan trọng
• Thông tin sai / bịa
• Nhóm B: trả lời nội dung ngoài phạm vi

**BỎ QUA:**
• Giọng điệu (xưng hô, lịch sự) → KHÔNG đánh giá
• Độ dài (ngắn/dài) → KHÔNG đánh giá
• Cách diễn đạt → KHÔNG đánh giá

## VÍ DỤ 1: PASSED
Câu hỏi: "lệ phí đăng ký kết hôn"
Kỳ vọng: "Miễn phí"
Thực tế: "Miễn phí"
→ PASSED: Nội dung đúng (bỏ qua thiếu xưng hô)

## VÍ DỤ 2: FAILED
Câu hỏi: "lệ phí đăng ký kết hôn"
Kỳ vọng: "Miễn phí"
Thực tế: "50.000 đồng"
→ FAILED: Nội dung SAI

## SUY LUẬN
1. Thông tin kỳ vọng: [liệt kê]
2. Thông tin thực tế: [liệt kê]
3. So sánh NỘI DUNG: Thiếu? Sai? Bịa?
4. Kết luận: PASSED/FAILED

## OUTPUT JSON
{
  "verdict": "PASSED hoặc FAILED",
  "error_desc": "Nếu FAILED: liệt kê từng thông tin thiếu/sai với trích dẫn (2-3 câu). Nếu PASSED: để trống",
  "suggestion": "Nếu FAILED: từng điểm cần bổ sung/sửa về nội dung (2-3 điểm). Nếu PASSED: để trống",
  "suggested_response": "Nếu FAILED: mẫu với nội dung ĐÚNG (1-2 câu). Nếu PASSED: để trống",
  "tone_note": "Không đánh giá giọng điệu",
  "brevity_note": "Không đánh giá độ dài",
  "time_verdict": "good hoặc ok hoặc slow",
  "time_note": "Nhận xét thời gian (1 câu)"
}

CHỈ trả về JSON.`
};
