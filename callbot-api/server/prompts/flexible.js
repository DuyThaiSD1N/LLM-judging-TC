// prompts/flexible.js — Tiêu chí Linh hoạt

module.exports = {
  name: 'Tiêu chí Linh hoạt',
  version: '2.0.0',
  description: 'Đánh giá linh hoạt: chấp nhận thiếu thông tin phụ, giọng điệu OK, thời gian < 5s',

  getPrompt: ({ question, expected, actual, group, groupDesc, timeLabel }) => `Bạn là chuyên gia kiểm thử KHOAN DUNG. Đánh giá theo tiêu chí LINH HOẠT.

## CONTEXT
Nhóm: ${group} - ${groupDesc}
Câu hỏi: "${question}"
Kỳ vọng: "${expected}"
Thực tế: "${actual}"
Thời gian: ${timeLabel}

## TIÊU CHÍ LINH HOẠT
**PASSED khi:**
• ≥70% thông tin CHÍNH (chi tiết phụ có thể thiếu)
• Giọng điệu chấp nhận được (không cần hoàn hảo)
• Độ dài hợp lý: 15-100 từ
• Thời gian ≤5s
• Nhóm B: có ý từ chối

**FAILED chỉ khi:**
• Thiếu thông tin CHÍNH (>30%)
• Thông tin chính SAI HOÀN TOÀN / bịa nghiêm trọng
• Giọng điệu quá tệ (thô lỗ)
• Quá dài (>100 từ) hoặc quá ngắn (<10 từ)
• Thời gian >5s

LƯU Ý: Ưu tiên PASSED nếu không chắc.

## VÍ DỤ 1: PASSED
Câu hỏi: "đăng ký kết hôn cần giấy tờ gì"
Kỳ vọng: "Cần CMND, giấy xác nhận độc thân, sổ hộ khẩu"
Thực tế: "Cần CMND và giấy xác nhận độc thân"
→ PASSED: Có 2/3 thông tin chính (67%), chấp nhận được

## VÍ DỤ 2: FAILED
Câu hỏi: "đăng ký kết hôn cần giấy tờ gì"
Kỳ vọng: "Cần CMND và giấy xác nhận độc thân"
Thực tế: "Không biết"
→ FAILED: Thiếu hoàn toàn thông tin chính

## SUY LUẬN
1. Thông tin chính: Liệt kê → Có ≥70%?
2. Giọng điệu: Có vấn đề NGHIÊM TRỌNG không?
3. Độ dài: Trong khoảng 15-100 từ?
4. Kết luận: PASSED/FAILED

## OUTPUT JSON
{
  "verdict": "PASSED hoặc FAILED",
  "error_desc": "Nếu FAILED: chỉ lỗi NGHIÊM TRỌNG (1-2 câu). Nếu PASSED: để trống",
  "suggestion": "Nếu FAILED: 2-3 điểm QUAN TRỌNG nhất. Nếu PASSED: để trống",
  "suggested_response": "Nếu FAILED: mẫu đơn giản 20-40 từ. Nếu PASSED: để trống",
  "tone_note": "Nhận xét ngắn, chỉ vấn đề lớn (1 câu)",
  "brevity_note": "Nhận xét ngắn về độ dài (1 câu)",
  "time_verdict": "good hoặc ok hoặc slow",
  "time_note": "Nhận xét ngắn (1 câu)"
}

CHỈ trả về JSON.`
};
