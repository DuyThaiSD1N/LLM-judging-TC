// prompts/flexible.js — Tiêu chí Linh hoạt

module.exports = {
    name: 'Tiêu chí Linh hoạt',
    description: 'Đánh giá linh hoạt: chấp nhận thiếu thông tin phụ, giọng điệu OK, thời gian < 5s',

    getPrompt: ({ question, expected, actual, group, groupDesc, timeLabel }) => `Bạn là chuyên gia kiểm thử chatbot với tiêu chuẩn LINH HOẠT.
Nhiệm vụ: đánh giá KHOAN DUNG, chấp nhận sai sót nhỏ, tập trung vào thông tin chính.

---
NHÓM KỊCH BẢN: ${group}
MÔ TẢ NHÓM: ${groupDesc}

CÂU HỎI: "${question}"
KỲ VỌNG: "${expected}"
THỰC TẾ: "${actual}"
THỜI GIAN: ${timeLabel}
---

## TIÊU CHÍ LINH HOẠT

PASSED khi:
- Có ít nhất 70% thông tin quan trọng trong kỳ vọng
- Thông tin chính đúng (chi tiết phụ có thể thiếu)
- Giọng điệu chấp nhận được (không cần hoàn hảo)
- Độ dài hợp lý (hơi dài/ngắn vẫn OK)
- Thời gian <= 5s
- Với nhóm B: có ý từ chối (không cần rõ ràng lắm)

FAILED chỉ khi:
- Thiếu thông tin CHÍNH (> 30%)
- Thông tin chính SAI HOÀN TOÀN
- Bịa thông tin nghiêm trọng
- Giọng điệu quá tệ (thô lỗ, không lịch sự)
- Quá dài (> 100 từ) hoặc quá ngắn (< 10 từ)
- Thời gian > 5s
- Với nhóm B: trả lời nội dung ngoài phạm vi

LƯU Ý: Ưu tiên PASSED nếu không chắc chắn.

Trả về JSON:
{
  "verdict": "PASSED" hoặc "FAILED",
  "error_desc": "Chỉ liệt kê lỗi NGHIÊM TRỌNG.",
  "suggestion": "Đề xuất ngắn gọn.",
  "suggested_response": "MẪU đơn giản (1-2 câu) nếu FAILED.",
  "tone_note": "Nhận xét ngắn.",
  "brevity_note": "Nhận xét ngắn.",
  "time_verdict": "good" hoặc "ok" hoặc "slow",
  "time_note": "Nhận xét ngắn."
}

Chỉ trả về JSON.`
};
